"""Typed owner tools. Approval/grant decisions are enforced outside the model."""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import hashlib
import json
from pydantic import BaseModel, ConfigDict, ValidationError
from src.memory.repository import now

SCHEMA = '''
CREATE TABLE IF NOT EXISTS tools_meta (version INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS tool_grants (owner TEXT NOT NULL, tool TEXT NOT NULL, active INTEGER NOT NULL, expires TEXT NOT NULL, PRIMARY KEY(owner,tool));
CREATE TABLE IF NOT EXISTS tool_approvals (id TEXT PRIMARY KEY, owner TEXT NOT NULL, tool TEXT NOT NULL, arguments_hash TEXT NOT NULL, expires TEXT NOT NULL, consumed INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS tool_runs (id TEXT PRIMARY KEY, owner TEXT NOT NULL, tool TEXT NOT NULL, request_key TEXT NOT NULL, arguments_hash TEXT NOT NULL, state TEXT NOT NULL, result TEXT, error TEXT, created_at TEXT NOT NULL, finished_at TEXT, UNIQUE(owner,request_key));
CREATE TABLE IF NOT EXISTS tool_audit (id TEXT PRIMARY KEY, owner TEXT NOT NULL, tool TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
'''

class ToolError(Exception):
    def __init__(self,code,message):
        self.code,self.message = code,message
        super().__init__(message)

class Arguments(BaseModel):
    model_config = ConfigDict(extra='forbid',str_strip_whitespace=True)

@dataclass
class Tool:
    name: str
    description: str
    schema: type[Arguments]
    write: bool
    private: bool
    handler: object

class ToolGateway:
    def __init__(self,repository,tools):
        self.repository = repository
        self.tools = {tool.name:tool for tool in tools}
        with repository.transaction() as db:
            for statement in SCHEMA.split(';'):
                if statement.strip(): db.execute(statement)
            db.execute("UPDATE tool_runs SET state='interrupted',error='process_restart',finished_at=? WHERE state='running'",(now(),))
            # One-time owner read defaults; revoked grants are never recreated.
            seeded = db.execute('SELECT version FROM tools_meta WHERE version=1').fetchone()
            if not seeded:
                for tool in tools:
                    if not tool.write:
                        db.execute('INSERT INTO tool_grants VALUES (?,?,1,?) ON CONFLICT DO NOTHING',('owner',tool.name,(datetime.now(timezone.utc)+timedelta(days=365)).isoformat()))
                db.execute('INSERT INTO tools_meta VALUES (1) ON CONFLICT DO NOTHING')

    def catalog(self):
        return [{'name':t.name,'description':t.description,'write':t.write,'private':t.private,'schema':t.schema.model_json_schema()} for t in self.tools.values()]

    def _validated(self,name,arguments):
        if name not in self.tools: raise ToolError('unknown_tool','Unknown tool')
        tool = self.tools[name]
        try: parsed = tool.schema.model_validate(arguments)
        except ValidationError as exc: raise ToolError('invalid_arguments',str(exc))
        data = parsed.model_dump(mode='json')
        digest = hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        return tool,parsed,digest

    def _audit(self,db,owner,tool,action,detail):
        db.execute('INSERT INTO tool_audit VALUES (?,?,?,?,?,?)',(str(uuid4()),owner,tool,action,detail[:1000],now()))

    def approve(self,owner,name,arguments):
        tool,parsed,digest = self._validated(name,arguments)
        approval = str(uuid4())
        expires=(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat()
        with self.repository.transaction() as db:
            db.execute('INSERT INTO tool_approvals VALUES (?,?,?,?,?,0)',(approval,owner,name,digest,expires))
            self._audit(db,owner,name,'approved',approval)
        return {'approval_id':approval,'tool':name,'arguments':parsed.model_dump(mode='json'),'expires':expires}

    def grant(self,owner,name,active):
        if name not in self.tools or self.tools[name].write:
            raise ToolError('invalid_grant','Only read tools can receive reusable grants')
        expires=(datetime.now(timezone.utc)+timedelta(days=365)).isoformat()
        with self.repository.transaction() as db:
            db.execute('INSERT INTO tool_grants VALUES (?,?,?,?) ON CONFLICT(owner,tool) DO UPDATE SET active=excluded.active,expires=excluded.expires',(owner,name,int(active),expires))
            self._audit(db,owner,name,'grant_enabled' if active else 'grant_revoked','Owner settings action')
        return {'tool':name,'active':active,'expires':expires}

    def grants(self,owner):
        with self.repository.transaction() as db:
            return [dict(r) for r in db.execute('SELECT * FROM tool_grants WHERE owner=? ORDER BY tool',(owner,)).fetchall()]

    def runs(self,owner):
        with self.repository.transaction() as db:
            rows=db.execute('SELECT * FROM tool_runs WHERE owner=? ORDER BY created_at DESC LIMIT 50',(owner,)).fetchall()
        return [self._run(r) for r in rows]

    @staticmethod
    def _run(row):
        data=dict(row)
        data['result']=json.loads(data['result']) if data['result'] else None
        return data

    def execute(self,owner,name,arguments,request_key,approval_id=None,cloud=False):
        run_id=str(uuid4())
        attempted=False
        try:
            tool,parsed,digest=self._validated(name,arguments)
            if cloud and tool.private:
                raise ToolError('private_context','This tool contains private data; use local-only model routing')
            with self.repository.transaction() as db:
                previous=db.execute('SELECT * FROM tool_runs WHERE owner=? AND request_key=?',(owner,request_key)).fetchone()
                if previous:
                    if previous['arguments_hash']!=digest or previous['tool']!=name:
                        raise ToolError('idempotency_conflict','Request key was already used for a different action')
                    if not tool.write and not db.execute('SELECT tool FROM tool_grants WHERE owner=? AND tool=? AND active=1 AND expires>?',(owner,name,now())).fetchone():
                        raise ToolError('permission_denied','Read grant was revoked or expired')
                    return self._run(previous)
                approved=False
                if approval_id:
                    changed=db.execute('UPDATE tool_approvals SET consumed=1 WHERE id=? AND owner=? AND tool=? AND arguments_hash=? AND expires>? AND consumed=0',(approval_id,owner,name,digest,now()))
                    approved=changed.rowcount==1
                    if not approved: raise ToolError('approval_invalid','Approval expired, consumed or does not match this action')
                grant=db.execute('SELECT * FROM tool_grants WHERE owner=? AND tool=? AND active=1 AND expires>?',(owner,name,now())).fetchone()
                if not approved and (tool.write or not grant):
                    raise ToolError('permission_denied','Review and approve this exact action first')
                db.execute('INSERT INTO tool_runs VALUES (?,?,?,?,?,?,NULL,NULL,?,NULL)',(run_id,owner,name,request_key,digest,'running',now()))
                attempted=True
                self._audit(db,owner,name,'started',run_id)
                if tool.write:
                    # Writes are strictly local transactional mutations. Mutation,
                    # approval consumption and completed result commit together.
                    result=tool.handler(parsed,owner,db)
                    encoded=json.dumps(result,ensure_ascii=False)
                    db.execute("UPDATE tool_runs SET state='completed',result=?,finished_at=? WHERE id=?",(encoded,now(),run_id))
                    self._audit(db,owner,name,'completed',run_id)
            if not tool.write:
                result=tool.handler(parsed,owner,None)
                encoded=json.dumps(result,ensure_ascii=False)
                if len(encoded)>150000: raise ToolError('result_limit','Tool result exceeded its budget')
                with self.repository.transaction() as db:
                    db.execute("UPDATE tool_runs SET state='completed',result=?,finished_at=? WHERE id=?",(encoded,now(),run_id))
                    self._audit(db,owner,name,'completed',run_id)
            return {'id':run_id,'tool':name,'state':'completed','result':result,'error':None}
        except Exception as exc:
            code=exc.code if isinstance(exc,ToolError) else 'tool_failed'
            message=exc.message if isinstance(exc,ToolError) else 'Tool failed; inspect configuration or retry with a new request key'
            with self.repository.transaction() as db:
                if attempted:
                    db.execute('INSERT INTO tool_runs VALUES (?,?,?,?,?,?,NULL,?,?,?) ON CONFLICT(owner,request_key) DO NOTHING',(run_id,owner,name,request_key,digest,'failed',code,now(),now()))
                db.execute("UPDATE tool_runs SET state='failed',error=?,finished_at=? WHERE id=? AND owner=?",(code,now(),run_id,owner))
                self._audit(db,owner,name,'failed',code)
            raise ToolError(code,message) from exc
