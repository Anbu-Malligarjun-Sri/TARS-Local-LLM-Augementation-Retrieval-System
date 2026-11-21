"""Authenticated owner memory routes. Request fields never choose the principal."""
import asyncio
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from src.memory.service import get_repository

router = APIRouter(prefix='/api/memory', tags=['personal memory'])
OWNER = 'owner'

class ClaimRequest(BaseModel):
    subject: str = Field(min_length=1,max_length=2000)
    predicate: str = Field(min_length=1,max_length=2000)
    value: str = Field(min_length=1,max_length=2000)
    audiences: list[Literal['owner','family','friend','professional']] = Field(default_factory=lambda:['owner'],min_length=1,max_length=4)
    sensitivity: Literal['private','shared'] = 'private'
    cloud_allowed: bool = False
    valid_to: str | None = None

async def mutation(body, supersedes=None):
    repo = get_repository()
    try:
        claim = await asyncio.to_thread(repo.add_claim,OWNER,**body.model_dump(),supersedes=supersedes)
    except KeyError:
        raise HTTPException(404,'Memory not found')
    except ValueError as error:
        raise HTTPException(422,str(error))
    try:
        await asyncio.to_thread(repo.project,OWNER)
    except Exception:
        # The accepted canonical fact remains readable; projection lag is visible.
        pass
    return {'claim':claim,'status':await asyncio.to_thread(repo.status,OWNER)}

@router.get('')
async def list_memories():
    repo = get_repository()
    return {'claims':await asyncio.to_thread(repo.claims,OWNER),'status':await asyncio.to_thread(repo.status,OWNER)}

@router.post('')
async def add_memory(body: ClaimRequest):
    return await mutation(body)

@router.get('/graph')
async def graph():
    return await asyncio.to_thread(get_repository().graph,OWNER)

@router.get('/export')
async def export():
    return await asyncio.to_thread(get_repository().export,OWNER)

@router.post('/rebuild')
async def rebuild():
    try:
        return await asyncio.to_thread(get_repository().project,OWNER)
    except Exception:
        raise HTTPException(503,'Projection rebuild failed; canonical facts remain available')

@router.get('/search')
async def search(query: str = Query(min_length=1,max_length=4000)):
    return {'claims':await asyncio.to_thread(get_repository().retrieve,OWNER,query)}

@router.get('/{claim_id}')
async def detail(claim_id: UUID):
    try:
        return await asyncio.to_thread(get_repository().get_claim,OWNER,str(claim_id))
    except KeyError:
        raise HTTPException(404,'Memory not found')

@router.put('/{claim_id}')
async def correct_memory(claim_id: UUID, body: ClaimRequest):
    return await mutation(body,str(claim_id))

@router.delete('/{claim_id}')
async def forget_memory(claim_id: UUID):
    try:
        await asyncio.to_thread(get_repository().forget,OWNER,str(claim_id))
    except KeyError:
        raise HTTPException(404,'Memory not found')
    return {'status':'forgotten','retention_note':'Live claims, their assertion sources and local indexes are redacted. Independent conversation history and previous backups are retained until separately deleted.'}
