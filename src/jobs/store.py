"""Durable coding queue. Approval binds the immutable snapshot and job contract."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from uuid import uuid4
import hashlib,json
from pydantic import BaseModel,Field,ConfigDict
from .workspace import snapshot,verify_snapshot,JobError
from src.memory.repository import now

class JobRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    repository:str=Field(min_length=1,max_length=100)
    objective:str=Field(min_length=10,max_length=4000)
    paths:list[str]=Field(min_length=1,max_length=30)
    checks:list[str]=Field(default_factory=lambda:['python-syntax'],max_length=3)
    timeout_seconds:int=Field(default=300,ge=30,le=900)
    token_budget:int=Field(default=20000,ge=1000,le=100000)
    request_key:str=Field(min_length=10,max_length=100)

SCHEMA='''
CREATE TABLE IF NOT EXISTS coding_jobs(id TEXT PRIMARY KEY,owner TEXT NOT NULL,request_key TEXT NOT NULL,request_hash TEXT NOT NULL,spec TEXT NOT NULL,manifest TEXT NOT NULL,approval_digest TEXT NOT NULL,state TEXT NOT NULL,cancel_requested INTEGER NOT NULL DEFAULT 0,lease TEXT,lease_until TEXT,heartbeat TEXT,result TEXT,error TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(owner,request_key));
CREATE TABLE IF NOT EXISTS coding_events(id TEXT PRIMARY KEY,job_id TEXT NOT NULL,owner TEXT NOT NULL,event TEXT NOT NULL,detail TEXT NOT NULL,created_at TEXT NOT NULL);
'''

class JobStore:
    def __init__(self,repository,root,repositories,cloud_enabled=False):
        self.repository=repository;self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.repositories={key:Path(value).resolve() for key,value in repositories.items()};self.cloud_enabled=cloud_enabled
        with repository.transaction() as db:
            for statement in SCHEMA.split(';'):
                if statement.strip():db.execute(statement)
    def folder(self,job_id):
        from uuid import UUID
        value=str(UUID(job_id));folder=self.root/value
        if not folder.is_relative_to(self.root) or folder.is_symlink() or folder.is_junction():raise JobError('Invalid job folder')
        return folder
    def event(self,db,job,owner,event,detail):
        db.execute('INSERT INTO coding_events VALUES (?,?,?,?,?,?)',(str(uuid4()),job,owner,event,detail[:2000],now()))
    @staticmethod
    def decode(row):
        result=dict(row)
        for key in ('spec','manifest','result'):
            result[key]=json.loads(result[key]) if result[key] else None
        return result
    def create(self,owner,request):
        spec=request.model_dump();key=spec.pop('request_key')
        if spec['repository'] not in self.repositories:raise JobError('Repository is not registered')
        if any(c not in {'python-syntax','python-unittest','pytest'} for c in spec['checks']):raise JobError('Unsupported check profile')
        request_hash=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()
        with self.repository.transaction() as db:
            old=db.execute('SELECT * FROM coding_jobs WHERE owner=? AND request_key=?',(owner,key)).fetchone()
            if old:
                if old['request_hash']!=request_hash:raise JobError('Request key belongs to a different job')
                return self.decode(old)
        job_id=str(uuid4());folder=self.folder(job_id);folder.mkdir()
        manifest,manifest_hash=snapshot(self.repositories[spec['repository']],folder,spec['paths'])
        spec['adapter']='codex-cloud';spec['provider']='OpenAI via installed Codex login'
        approval_digest=hashlib.sha256((manifest_hash+json.dumps(spec,sort_keys=True)).encode()).hexdigest()
        timestamp=now()
        with self.repository.transaction() as db:
            # Concurrent duplicate preparation retains one durable winner; any
            # losing local snapshot is inert and never queued.
            db.execute('INSERT INTO coding_jobs VALUES (?,?,?,?,?,?,?,?,0,NULL,NULL,NULL,NULL,NULL,?,?) ON CONFLICT(owner,request_key) DO NOTHING',(job_id,owner,key,request_hash,json.dumps(spec),json.dumps(manifest),approval_digest,'waiting_for_approval',timestamp,timestamp))
            row=db.execute('SELECT * FROM coding_jobs WHERE owner=? AND request_key=?',(owner,key)).fetchone()
            if row['request_hash']!=request_hash:raise JobError('Concurrent job key conflict')
            self.event(db,row['id'],owner,'prepared','Awaiting explicit cloud/snapshot approval')
        return self.decode(row)
    def get(self,owner,job_id):
        with self.repository.transaction() as db:row=db.execute('SELECT * FROM coding_jobs WHERE id=? AND owner=?',(job_id,owner)).fetchone()
        if not row:raise JobError('Job not found')
        return self.decode(row)
    def list(self,owner):
        with self.repository.transaction() as db:rows=db.execute('SELECT id,owner,request_key,request_hash,spec,manifest,approval_digest,state,cancel_requested,lease,lease_until,heartbeat,NULL AS result,error,created_at,updated_at FROM coding_jobs WHERE owner=? ORDER BY created_at DESC LIMIT 50',(owner,)).fetchall()
        return [self.decode(row) for row in rows]
    def approve(self,owner,job_id,expected_digest):
        if not self.cloud_enabled:raise JobError('Cloud coding is not enabled on this server')
        job=self.get(owner,job_id)
        if job['approval_digest']!=expected_digest:raise JobError('Approval does not match this job')
        verify_snapshot(self.folder(job_id),job['manifest'])
        with self.repository.transaction() as db:
            changed=db.execute("UPDATE coding_jobs SET state='queued',updated_at=? WHERE id=? AND owner=? AND state='waiting_for_approval' AND approval_digest=? AND cancel_requested=0",(now(),job_id,owner,expected_digest))
            if changed.rowcount!=1:raise JobError('Job was already approved, cancelled or changed')
            self.event(db,job_id,owner,'approved',expected_digest)
        return self.get(owner,job_id)
    def cancel(self,owner,job_id):
        with self.repository.transaction() as db:
            changed=db.execute("UPDATE coding_jobs SET cancel_requested=1,state=CASE WHEN state IN ('waiting_for_approval','queued') THEN 'cancelled' ELSE state END,updated_at=? WHERE id=? AND owner=? AND state IN ('waiting_for_approval','queued','running','verifying')",(now(),job_id,owner))
            if changed.rowcount:self.event(db,job_id,owner,'cancel_requested','Owner requested cancellation')
        return self.get(owner,job_id)
    def claim(self,worker):
        with self.repository.transaction() as db:
            db.execute("UPDATE coding_jobs SET state='interrupted',error='Worker lease expired; create and approve a new attempt',updated_at=? WHERE state IN ('running','verifying') AND lease_until<?",(now(),now()))
            if not self.cloud_enabled:return None
            row=db.execute("SELECT * FROM coding_jobs WHERE state='queued' AND cancel_requested=0 ORDER BY created_at LIMIT 1").fetchone()
            if not row:return None
            expires=(datetime.now(timezone.utc)+timedelta(seconds=45)).isoformat()
            changed=db.execute("UPDATE coding_jobs SET state='running',lease=?,lease_until=?,heartbeat=?,updated_at=? WHERE id=? AND state='queued'",(worker,expires,now(),now(),row['id']))
            if changed.rowcount!=1:return None
            self.event(db,row['id'],row['owner'],'started',worker)
            row=db.execute('SELECT * FROM coding_jobs WHERE id=?',(row['id'],)).fetchone()
        return self.decode(row)
    def heartbeat(self,job_id,worker):
        with self.repository.transaction() as db:
            row=db.execute('SELECT state,cancel_requested FROM coding_jobs WHERE id=? AND lease=?',(job_id,worker)).fetchone()
            if not row or row['state'] not in {'running','verifying'}:return 'lease_lost'
            db.execute('UPDATE coding_jobs SET heartbeat=?,lease_until=?,updated_at=? WHERE id=? AND lease=?',(now(),(datetime.now(timezone.utc)+timedelta(seconds=45)).isoformat(),now(),job_id,worker))
        return 'cancelled' if row['cancel_requested'] else None
    def verifying(self,job,worker):
        with self.repository.transaction() as db:
            changed=db.execute("UPDATE coding_jobs SET state='verifying',updated_at=? WHERE id=? AND lease=? AND state='running' AND cancel_requested=0",(now(),job['id'],worker))
            if changed.rowcount:self.event(db,job['id'],job['owner'],'verifying','Running approved acceptance profiles')
            else:raise JobError('Job cancelled or worker lease lost before verification')
    def finish(self,job,worker,state,result=None,error=None):
        with self.repository.transaction() as db:
            changed=db.execute("UPDATE coding_jobs SET state=CASE WHEN cancel_requested=1 THEN 'cancelled' ELSE ? END,result=?,error=?,lease_until=NULL,updated_at=? WHERE id=? AND lease=? AND state IN ('running','verifying')",(state,json.dumps(result) if result is not None else None,error,now(),job['id'],worker))
            if changed.rowcount:self.event(db,job['id'],job['owner'],state,error or 'Job finished; source repository unchanged')
        return bool(changed.rowcount)
    def events(self,owner,job_id):
        self.get(owner,job_id)
        with self.repository.transaction() as db:return [dict(row) for row in db.execute('SELECT * FROM coding_events WHERE job_id=? AND owner=? ORDER BY created_at',(job_id,owner)).fetchall()]
