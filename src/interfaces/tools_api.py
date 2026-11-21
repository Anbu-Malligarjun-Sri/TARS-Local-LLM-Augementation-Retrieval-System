"""Routes inherit owner authentication; model output never invokes approvals."""
import asyncio
from uuid import UUID
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field,ConfigDict
from src.tools.gateway import ToolError
from src.tools.service import get_gateway
router=APIRouter(prefix='/api/tools',tags=['governed tools'])
class Action(BaseModel):
    model_config=ConfigDict(extra='forbid')
    tool:str=Field(min_length=1,max_length=80)
    arguments:dict=Field(default_factory=dict)
class Run(Action):
    request_key:UUID
    approval_id:UUID|None=None
class Grant(BaseModel):
    active:bool
async def call(function,*args,**kwargs):
    try:return await asyncio.to_thread(function,*args,**kwargs)
    except ToolError as error:
        status=403 if error.code in {'permission_denied','approval_invalid','private_context'} else 409 if error.code in {'conflict','idempotency_conflict'} else 422 if error.code in {'invalid_arguments','unknown_tool','invalid_grant','url_denied','calendar_invalid','calendar_range'} else 502
        raise HTTPException(status,{'code':error.code,'message':error.message})
@router.get('')
async def catalog():return {'tools':get_gateway().catalog()}
@router.get('/grants')
async def grants():return {'grants':await call(get_gateway().grants,'owner')}
@router.put('/grants/{tool}')
async def set_grant(tool:str,body:Grant):return await call(get_gateway().grant,'owner',tool,body.active)
@router.post('/approvals')
async def approve(body:Action):return await call(get_gateway().approve,'owner',body.tool,body.arguments)
@router.post('/run')
async def run(body:Run):return await call(get_gateway().execute,'owner',body.tool,body.arguments,str(body.request_key),str(body.approval_id) if body.approval_id else None)
@router.get('/runs')
async def runs():return {'runs':await call(get_gateway().runs,'owner')}
@router.get('/audit')
async def audit():
    def read():
        with get_gateway().repository.transaction() as db:
            return [dict(row) for row in db.execute('SELECT * FROM tool_audit WHERE owner=? ORDER BY created_at DESC LIMIT 100',('owner',)).fetchall()]
    return {'events':await asyncio.to_thread(read)}
