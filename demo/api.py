"""Isolated, single-worker visitor preview. No owner or paid-provider dependencies."""
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
import hashlib
import json
import secrets
import time
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

COOKIE = "companion_visit"
TTL_SECONDS = 900
SAMPLES = {
    "en": "Pick one task you can finish today. The list can survive the suspense.",
    "ta": "இன்று முடிக்கக்கூடிய ஒரு வேலையைத் தேர்ந்தெடு. பட்டியல் காத்திருக்கட்டும்.",
    "tanglish": "Innaikku mudikka mudiyura oru velaiya therndhedu. List konjam kaathirukkattum.",
}


@dataclass
class Visit:
    deadline: float
    count: int = 0
    turn: UUID | None = None
    streaming: bool = False
    language: str = "en"


class TurnRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    language: Literal["en", "ta", "tanglish"] = "en"


def create_app(clock=time.monotonic, capacity: int = 64) -> FastAPI:
    visits: dict[bytes, Visit] = {}

    def prune():
        for key, visit in list(visits.items()):
            if visit.deadline <= clock():
                del visits[key]

    async def sweep():
        while True:
            await asyncio.sleep(1)
            prune()

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(sweep())
        try:
            yield
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            visits.clear()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["visitor.localhost"])

    @app.middleware("http")
    async def visit_headers(request: Request, call_next):
        origin = request.headers.get("origin")
        if request.method in {"POST", "DELETE"} and (
            request.headers.get("x-demo-client") != "1"
            or (origin is not None and origin != str(request.base_url).rstrip("/"))
        ):
            return Response(status_code=403, headers={"Cache-Control":"no-store"})
        if request.url.path == "/demo/turns" and request.method == "POST":
            length = request.headers.get("content-length", "")
            if not length.isdigit() or int(length) > 4096:
                return Response(status_code=413)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    def key(request):
        return hashlib.sha256(request.cookies.get(COOKIE, "").encode()).digest()

    def current_visit(request):
        prune()
        visit = visits.get(key(request))
        if visit is None:
            raise HTTPException(401, "Start a new visit.")
        return visit

    @app.post("/demo/visit")
    async def begin(request: Request, response: Response):
        prune()
        existing = visits.get(key(request))
        if existing:
            return {"expires_in_seconds": int(existing.deadline-clock())}
        if len(visits) >= capacity:
            raise HTTPException(429, "Demo visit limit reached.")
        token = secrets.token_urlsafe(32)
        visits[hashlib.sha256(token.encode()).digest()] = Visit(clock()+TTL_SECONDS)
        response.set_cookie(COOKIE,token,max_age=TTL_SECONDS,path="/demo/",httponly=True,
                            samesite="strict",secure=request.url.scheme=="https")
        response.status_code = 201
        return {"expires_in_seconds": TTL_SECONDS}

    @app.get("/demo/visit")
    async def current(request: Request):
        return {"expires_in_seconds": int(current_visit(request).deadline-clock())}

    @app.delete("/demo/visit",status_code=204)
    async def end(request: Request):
        visits.pop(key(request),None)
        response = Response(status_code=204)
        response.delete_cookie(COOKIE,path="/demo/",httponly=True,samesite="strict",secure=request.url.scheme=="https")
        return response

    @app.post("/demo/turns",status_code=201)
    async def prepare(request: Request, body: TurnRequest):
        visit = current_visit(request)
        if not body.message.strip():
            raise HTTPException(422,"Enter a message.")
        if visit.turn or visit.streaming or visit.count >= 5:
            raise HTTPException(429,"Active turn or visit quota reached.")
        visit.turn = uuid4()
        visit.language = body.language
        visit.count += 1
        return {"id":visit.turn,"provider":"scripted-preview","turns_remaining":5-visit.count}

    @app.post("/demo/turns/{turn}/stream")
    async def stream(request: Request, turn: UUID):
        visit = current_visit(request)
        if visit.turn != turn:
            raise HTTPException(404,"Turn unavailable.")
        if visit.streaming or sum(v.streaming for v in visits.values()) >= 4:
            raise HTTPException(429,"Stream capacity reached.")
        visit.streaming = True
        owner_key = key(request)

        def event(kind, content=""):
            return "data: " + json.dumps({"type":kind,"turn_id":str(turn),"content":content},ensure_ascii=False) + "\n\n"

        async def events():
            try:
                yield event("start")
                for word in SAMPLES[visit.language].split():
                    await asyncio.sleep(.06)
                    if visit.turn != turn or visits.get(owner_key) is not visit or clock() >= visit.deadline:
                        yield event("cancelled")
                        return
                    yield event("chunk", word+" ")
                yield event("end")
            finally:
                visit.streaming = False
                visit.turn = None
        return StreamingResponse(events(),media_type="text/event-stream",headers={"X-Accel-Buffering":"no"})

    @app.post("/demo/turns/{turn}/stop",status_code=204)
    async def stop(request: Request, turn: UUID):
        visit = current_visit(request)
        if visit.turn != turn:
            raise HTTPException(404,"Turn unavailable.")
        visit.turn = None
        return Response(status_code=204)

    return app


app = create_app()
