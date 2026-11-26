"""Isolated, single-worker visitor preview. No owner or paid-provider dependencies."""
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import secrets
import time
from typing import Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .dialogue import PROMPTS, response as scripted_response

COOKIE = "companion_visit"
TTL_SECONDS = 900
WEB = Path(__file__).with_name("web")
TURN_LIMIT = 5


@dataclass
class Visit:
    deadline: float
    id: UUID = field(default_factory=uuid4)
    count: int = 0
    turn: UUID | None = None
    streaming: bool = False
    reply: str = ""
    remembers_firefly: bool = False
    pending_memory: bool = False


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
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        )
        response.headers["Permissions-Policy"] = "microphone=(), camera=(), geolocation=()"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    def key(request):
        return hashlib.sha256(request.cookies.get(COOKIE, "").encode()).digest()

    def current_visit(request):
        prune()
        visit = visits.get(key(request))
        if visit is None:
            raise HTTPException(401, "Start a new visit.")
        expected = request.headers.get("x-demo-visit")
        if expected is not None and expected != str(visit.id):
            raise HTTPException(409, "This visit was replaced in another tab.")
        return visit

    @app.get("/")
    async def page():
        return FileResponse(WEB / "index.html")

    @app.get("/assets/{name}")
    async def asset(name: str):
        types = {"visitor.js": "text/javascript", "visitor.css": "text/css"}
        if name not in types:
            raise HTTPException(404)
        return FileResponse(WEB / name, media_type=types[name])

    @app.get("/demo/scenes")
    async def scenes():
        return PROMPTS

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
        visit = current_visit(request)
        return {"expires_in_seconds": math.ceil(visit.deadline-clock()),
                "visit_id": visit.id, "turns_remaining": TURN_LIMIT-visit.count, "active_turn": visit.turn}

    @app.delete("/demo/visit",status_code=204)
    async def end(request: Request):
        if request.headers.get("x-demo-visit") is not None:
            current_visit(request)
        visits.pop(key(request),None)
        response = Response(status_code=204)
        response.delete_cookie(COOKIE,path="/demo/",httponly=True,samesite="strict",secure=request.url.scheme=="https")
        return response

    @app.post("/demo/turns",status_code=201)
    async def prepare(request: Request, body: TurnRequest):
        visit = current_visit(request)
        if not body.message.strip():
            raise HTTPException(422,"Enter a message.")
        if visit.turn or visit.streaming or visit.count >= TURN_LIMIT:
            raise HTTPException(429,"Active turn or visit quota reached.")
        visit.turn = uuid4()
        visit.reply, visit.pending_memory = scripted_response(body.message, body.language, visit.remembers_firefly)
        visit.count += 1
        return {"id":visit.turn,"provider":"scripted-preview","turns_remaining":TURN_LIMIT-visit.count}

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
                for word in visit.reply.split():
                    await asyncio.sleep(.06)
                    if visit.turn != turn or visits.get(owner_key) is not visit or clock() >= visit.deadline:
                        yield event("cancelled")
                        return
                    yield event("chunk", word+" ")
                if visit.turn != turn or visits.get(owner_key) is not visit or clock() >= visit.deadline:
                    yield event("cancelled")
                    return
                visit.remembers_firefly |= visit.pending_memory
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
