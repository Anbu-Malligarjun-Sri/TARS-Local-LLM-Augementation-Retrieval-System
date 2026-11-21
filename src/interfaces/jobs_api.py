"""Owner-only job preparation/review; no automatic source application endpoint."""
import asyncio,shutil
from uuid import UUID,uuid4
from fastapi import APIRouter,HTTPException,Query
from pydantic import BaseModel,ConfigDict,Field
from src.jobs.service import get_store
from src.jobs.store import JobRequest
from src.jobs.workspace import JobError,safe_relative,no_links
from src.agents.codex import CodexAdapter
router=APIRouter(prefix='/api/jobs',tags=['coding jobs'])
class Approval(BaseModel):
    model_config=ConfigDict(extra='forbid')
    approval_digest:str=Field(min_length=64,max_length=64)

async def call(function,*args):
    try:return await asyncio.to_thread(function,*args)
    except (JobError,ValueError) as error:raise HTTPException(409,str(error))

@router.get('/capabilities')
async def capabilities():
    store=get_store()
    return {'adapter':'codex-cloud','cloud_enabled':store.cloud_enabled,'codex_installed':bool(shutil.which('codex')),
            'repositories':[{'id':key,'label':key} for key in store.repositories],
            'checks':['python-syntax','python-unittest','pytest'],
            'limits':{'max_files':250,'max_snapshot_bytes':4000000,'max_timeout_seconds':900},
            'note':'Native sandbox preflight is required per job. Provider login is managed by installed Codex. No automatic source apply.'}

@router.post('/preflight')
async def preflight():
    try:
        adapter=CodexAdapter()
        return await call(adapter.preflight,get_store().root.parent/'preflight'/str(uuid4()))
    except JobError as error:raise HTTPException(409,str(error))

@router.get('')
async def list_jobs():return {'jobs':await call(get_store().list,'owner')}
@router.post('')
async def create_job(body:JobRequest):return await call(get_store().create,'owner',body)
@router.get('/{job_id}')
async def detail(job_id:UUID):return await call(get_store().get,'owner',str(job_id))
@router.post('/{job_id}/approve')
async def approve(job_id:UUID,body:Approval):return await call(get_store().approve,'owner',str(job_id),body.approval_digest)
@router.post('/{job_id}/cancel')
async def cancel(job_id:UUID):return await call(get_store().cancel,'owner',str(job_id))
@router.get('/{job_id}/events')
async def events(job_id:UUID):return {'events':await call(get_store().events,'owner',str(job_id))}
@router.get('/{job_id}/source')
async def source(job_id:UUID,path:str=Query(min_length=1,max_length=500)):
    store=get_store();job=await call(store.get,'owner',str(job_id))
    try:
        relative=safe_relative(path)
        if relative not in {f['path'] for f in job['manifest']['files']}:raise JobError('Not in the approved snapshot')
        baseline=store.folder(str(job_id))/'baseline';target=baseline/relative;no_links(target,baseline)
        return {'path':relative,'content':target.read_text(encoding='utf-8-sig')}
    except (JobError,ValueError,OSError) as error:raise HTTPException(403,str(error))
