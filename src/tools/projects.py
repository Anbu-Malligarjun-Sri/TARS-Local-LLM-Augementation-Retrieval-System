"""Persistent projects/tasks; all mutations share the tool-run transaction."""
import json
from datetime import datetime,timezone
from typing import Literal
from uuid import UUID,uuid4
from pydantic import Field,field_validator
from src.memory.repository import now
from .gateway import Arguments,Tool,ToolError

SCHEMA='''
CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, owner TEXT NOT NULL, name TEXT NOT NULL, notes TEXT NOT NULL, status TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, owner TEXT NOT NULL, project_id TEXT NOT NULL REFERENCES projects(id), title TEXT NOT NULL, notes TEXT NOT NULL, status TEXT NOT NULL, priority TEXT NOT NULL, due_at TEXT, version INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS project_events (id TEXT PRIMARY KEY, owner TEXT NOT NULL, entity_id TEXT NOT NULL, action TEXT NOT NULL, snapshot TEXT NOT NULL, created_at TEXT NOT NULL);
'''
class ProjectCreate(Arguments):
    name: str=Field(min_length=1,max_length=200)
    notes: str=Field(default='',max_length=4000)
class ProjectList(Arguments):
    include_archived: bool=False
class ProjectUpdate(Arguments):
    id: UUID
    expected_version: int=Field(ge=1)
    name: str=Field(min_length=1,max_length=200)
    notes: str=Field(default='',max_length=4000)
    status: Literal['active','archived']='active'
class TaskCreate(Arguments):
    project_id: UUID
    title: str=Field(min_length=1,max_length=300)
    notes: str=Field(default='',max_length=4000)
    priority: Literal['low','normal','high']='normal'
    due_at: str|None=None
    @field_validator('due_at')
    @classmethod
    def due_date(cls,value):
        if value is not None and datetime.fromisoformat(value).tzinfo is None:
            raise ValueError('Task due time must include a timezone')
        return datetime.fromisoformat(value).astimezone(timezone.utc).isoformat() if value is not None else None
class TaskUpdate(TaskCreate):
    id: UUID
    expected_version: int=Field(ge=1)
    status: Literal['todo','doing','blocked','done','archived']='todo'
class TaskList(Arguments):
    project_id: UUID|None=None
    include_completed: bool=False

class Projects:
    def __init__(self,repository):
        self.repository=repository
        with repository.transaction() as db:
            for statement in SCHEMA.split(';'):
                if statement.strip():db.execute(statement)
    def record(self,db,owner,entity,action,snapshot):
        db.execute('INSERT INTO project_events VALUES (?,?,?,?,?,?)',(str(uuid4()),owner,entity,action,json.dumps(snapshot),now()))
    def project_create(self,args,owner,db):
        entity=str(uuid4()); timestamp=now()
        db.execute('INSERT INTO projects VALUES (?,?,?,?,?,?,?,?)',(entity,owner,args.name,args.notes,'active',1,timestamp,timestamp))
        result={'id':entity,'name':args.name,'notes':args.notes,'status':'active','version':1}
        self.record(db,owner,entity,'created',result)
        return result
    def project_list(self,args,owner,db):
        with self.repository.transaction() as connection:
            rows=connection.execute('SELECT * FROM projects WHERE owner=? ORDER BY updated_at DESC LIMIT 100',(owner,)).fetchall()
        return {'projects':[dict(r) for r in rows if args.include_archived or r['status']=='active'],'retrieved_at':now()}
    def project_update(self,args,owner,db):
        changed=db.execute('UPDATE projects SET name=?,notes=?,status=?,version=version+1,updated_at=? WHERE id=? AND owner=? AND version=?',(args.name,args.notes,args.status,now(),str(args.id),owner,args.expected_version))
        if changed.rowcount!=1:raise ToolError('conflict','Project missing or changed; refresh before editing')
        result=dict(db.execute('SELECT * FROM projects WHERE id=? AND owner=?',(str(args.id),owner)).fetchone())
        self.record(db,owner,str(args.id),'updated',result);return result
    def task_create(self,args,owner,db):
        if not db.execute("SELECT id FROM projects WHERE id=? AND owner=? AND status='active'",(str(args.project_id),owner)).fetchone():
            raise ToolError('project_missing','Select an active project belonging to you')
        entity=str(uuid4()); timestamp=now()
        db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?,?)',(entity,owner,str(args.project_id),args.title,args.notes,'todo',args.priority,args.due_at,1,timestamp,timestamp))
        result={'id':entity,**args.model_dump(mode='json'),'status':'todo','version':1}
        self.record(db,owner,entity,'created',result);return result
    def task_list(self,args,owner,db):
        with self.repository.transaction() as connection:
            rows=connection.execute('SELECT t.*,p.name AS project_name FROM tasks t JOIN projects p ON p.id=t.project_id AND p.owner=t.owner WHERE t.owner=? ORDER BY t.updated_at DESC LIMIT 200',(owner,)).fetchall()
        return {'tasks':[dict(r) for r in rows if (args.project_id is None or r['project_id']==str(args.project_id)) and (args.include_completed or r['status'] not in {'done','archived'})],'retrieved_at':now()}
    def task_update(self,args,owner,db):
        if not db.execute('SELECT id FROM projects WHERE id=? AND owner=?',(str(args.project_id),owner)).fetchone():
            raise ToolError('project_missing','Project not found')
        changed=db.execute('UPDATE tasks SET project_id=?,title=?,notes=?,status=?,priority=?,due_at=?,version=version+1,updated_at=? WHERE id=? AND owner=? AND version=?',(str(args.project_id),args.title,args.notes,args.status,args.priority,args.due_at,now(),str(args.id),owner,args.expected_version))
        if changed.rowcount!=1:raise ToolError('conflict','Task missing or changed; refresh before editing')
        result=dict(db.execute('SELECT * FROM tasks WHERE id=? AND owner=?',(str(args.id),owner)).fetchone())
        self.record(db,owner,str(args.id),'updated',result);return result
    def tools(self):
        return [Tool(name,description,schema,write,True,handler) for name,description,schema,write,handler in [
            ('projects.list','Read owner projects',ProjectList,False,self.project_list),
            ('projects.create','Create a local project',ProjectCreate,True,self.project_create),
            ('projects.update','Edit or archive a local project',ProjectUpdate,True,self.project_update),
            ('tasks.list','Read owner tasks',TaskList,False,self.task_list),
            ('tasks.create','Create a local task',TaskCreate,True,self.task_create),
            ('tasks.update','Edit, complete or reopen a local task',TaskUpdate,True,self.task_update)]]
