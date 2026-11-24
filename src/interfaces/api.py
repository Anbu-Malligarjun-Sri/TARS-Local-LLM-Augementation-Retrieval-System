"""
TARS FastAPI Backend
REST API for interacting with TARS chatbot.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict
from src.personality.policy import Style
from typing import Optional, List
import asyncio
import json
import time
import threading
from datetime import datetime, timezone
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from src.interfaces.foundation import ORIGINS, authenticated, pair, connect
from fastapi import Request, Response, Query
from pydantic import ValidationError
import logging
import sys
from pathlib import Path
from uuid import UUID, uuid4

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core import TARSEngine, get_tars_engine
from src.utils.config import get_config


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tars.api")


# Pydantic models for request/response
class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    style: Style = Field(default_factory=Style)
    turn_id: UUID | None = None
    message: str = Field(..., min_length=1, max_length=16000, description="User message to send to TARS")
    enhance_response: bool = Field(True, description="Whether to add personality enhancements")
    stream: bool = Field(False, description="Whether to stream the response")
    conversation_id: UUID = Field(..., description="Conversation to continue")


class ChatResponse(BaseModel):
    response: str = Field(..., description="TARS response")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")


class SettingsRequest(BaseModel):
    humor: Optional[int] = Field(None, ge=0, le=100, description="Humor level (0-100)")
    honesty: Optional[int] = Field(None, ge=0, le=100, description="Honesty level (0-100)")
    discretion: Optional[int] = Field(None, ge=0, le=100, description="Discretion level (0-100)")
    responseSpeed: Optional[int] = Field(None, ge=0, le=100, description="Response speed (0=slow/thoughtful, 100=fast)")
    verbosity: Optional[int] = Field(None, ge=0, le=100, description="Verbosity (0=terse, 100=detailed)")
    cautionLevel: Optional[int] = Field(None, ge=0, le=100, description="Caution level (0=bold, 100=careful)")
    trustLevel: Optional[int] = Field(None, ge=0, le=100, description="Trust level (0=skeptical, 100=trusting)")


class SettingsResponse(BaseModel):
    humor: int = Field(..., description="Current humor level")
    honesty: int = Field(..., description="Current honesty level")
    discretion: int = Field(..., description="Current discretion level")
    responseSpeed: int = Field(60, description="Response speed setting")
    verbosity: int = Field(50, description="Verbosity setting")
    cautionLevel: int = Field(40, description="Caution level setting")
    trustLevel: int = Field(70, description="Trust level setting")


class RAGStatsResponse(BaseModel):
    total_documents: int
    loaded_datasets: int
    topics: List[str]
    embedding_model: str
    embedding_dimension: int


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    rag_enabled: bool
    voice_enabled: bool


# Create FastAPI app
app = FastAPI(
    title="TARS API",
    description="REST API for TARS - The sarcastic AI chatbot from Interstellar",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ORIGINS),  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global TARS engine instance
_engine: TARSEngine | None = None


_engine_lock = threading.Lock()

def get_engine() -> TARSEngine:
    """Get or create the TARS engine."""
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = get_tars_engine()
            with connect() as db:
                row = db.execute("SELECT value FROM settings WHERE id=1").fetchone()
            if row:
                saved = json.loads(row[0])
                _engine.update_personality(**{k: v / 100 for k, v in saved.items()})
        return _engine

# === Health & Status ===

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with welcome message."""
    return {
        "message": "TARS online. Humor at 60%, honesty at 90%. Ready for your queries.",
        "docs": "/docs",
        "version": "2.0.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health status."""
    config = get_config()
    engine = await asyncio.to_thread(get_engine)
    
    return HealthResponse(
        status="configured (provider not probed)",
        llm_provider=config.llm_provider,
        rag_enabled=engine.use_rag,
        voice_enabled=False
    )


# === Chat Endpoints ===

# Bounded generation workers. A cancelled SDK call retains its worker until its
# finite network timeout, preventing unbounded abandoned threads.
_executor = ThreadPoolExecutor(max_workers=4)
_locks = {}
_active = {}
_rates = defaultdict(deque)

@app.middleware("http")
async def private_access(request: Request, call_next):
    from starlette.responses import JSONResponse
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = _rates[(key, request.url.path in {"/api/pair", "/api/launch"})]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    limit = 10 if request.url.path in {"/api/pair", "/api/launch"} else 120
    if len(bucket) >= limit:
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
    bucket.append(now)
    length = request.headers.get("content-length", "0")
    limits = {'/api/media/transcribe':640000, '/api/media/faces/enroll':150000, '/api/media/faces/match':150000}
    limit_bytes = limits.get(request.url.path,65536)
    if request.url.path in limits and 'content-length' not in request.headers:
        return JSONResponse({"detail":"Content length required"},status_code=411)
    if not length.isdigit() or int(length) > limit_bytes:
        return JSONResponse({"detail": "Payload too large"}, status_code=413)
    origin = request.headers.get("origin")
    if origin and origin not in ORIGINS:
        return JSONResponse({"detail": "Origin denied"}, status_code=403)
    if request.method == "OPTIONS":
        return await call_next(request)
    if request.url.path not in {"/api/pair", "/api/launch"} and not authenticated(request.headers, request.cookies):
        return JSONResponse({"detail": "Pair this device first; configure OWNER_TOKEN on the server"}, status_code=401)
    return await call_next(request)

class PairRequest(BaseModel):
    token: str = Field(min_length=16, max_length=512)

@app.post("/api/pair")
async def pair_device(body: PairRequest, response: Response, request: Request):
    response.set_cookie("tars_device", pair(body.token), httponly=True,
                        samesite="strict", secure=request.url.scheme == "https", max_age=86400*30)
    return {"status": "paired"}

@app.post("/api/launch")
async def launch_device(body: PairRequest, response: Response, request: Request):
    from src.interfaces.launch import redeem
    response.set_cookie("tars_device", redeem(body.token), httponly=True,
                        samesite="strict", secure=request.url.scheme == "https", max_age=86400*30)
    return {"status":"paired"}

@app.delete("/api/pair")
async def unpair(request: Request, response: Response):
    import hashlib
    with connect() as db:
        db.execute("DELETE FROM devices WHERE token=?", (hashlib.sha256(request.cookies.get("tars_device", "").encode()).hexdigest(),))
    response.delete_cookie("tars_device")
    return {"status": "unpaired"}

_pending_cancels = {}
_draining = set()

async def events(message, conversation_id, turn_id, style=None):
    if len(_active) >= 4 or turn_id in _active:
        yield {"schema_version": 1, "type": "error", "turn_id": turn_id, "conversation_id": conversation_id,
               "content": "Generation capacity reached or turn already active; retry shortly."}
        return
    sequence = 0
    cancelled = threading.Event()
    def event(kind, **payload):
        nonlocal sequence
        sequence += 1
        return dict(schema_version=1, type=kind, conversation_id=conversation_id,
                    turn_id=turn_id, message_id=turn_id, sequence=sequence,
                    timestamp=datetime.now(timezone.utc).isoformat(), **payload)
    try:
        with connect() as db:
            db.execute("INSERT INTO turns VALUES (?,?,?,?)", (turn_id, conversation_id, "running", None))
    except Exception:
        yield event("error", content="Turn ID already used or turn storage unavailable; submit a new turn.")
        return
    _active[turn_id] = cancelled
    if _pending_cancels.pop(turn_id, 0) > time.monotonic():cancelled.set()
    state = "error";full = "";iterator = None;pending = None
    lock = _locks.setdefault(conversation_id, asyncio.Lock());acquired = False
    lock_task = None
    async def cleanup():
        try:
            if pending is not None:
                try:await asyncio.shield(pending)
                except (Exception, asyncio.CancelledError):pass
            if iterator is not None:
                try:await asyncio.to_thread(iterator.close)
                except (ValueError, RuntimeError):pass
            if state != "completed" and full:
                await asyncio.to_thread(get_engine().memory.add_message, "assistant", full,
                    conversation_id=conversation_id, metadata={"turn_id": turn_id, "state": state})
        finally:
            if acquired:lock.release()
            _active.pop(turn_id, None)
            with connect() as db:db.execute("UPDATE turns SET state=? WHERE id=?", (state, turn_id))
    try:
        yield event("start")
        lock_task = asyncio.create_task(lock.acquire())
        deadline = time.monotonic() + get_config().request_timeout
        while not lock_task.done():
            if cancelled.is_set():
                state = "cancelled";yield event(state);return
            if time.monotonic() > deadline:raise TimeoutError()
            await asyncio.wait({lock_task}, timeout=.025)
        acquired = await lock_task
        engine = await asyncio.to_thread(get_engine)
        iterator = iter(engine.chat_stream(message, conversation_id=conversation_id,
                                           style=style or Style(), cancel_event=cancelled))
        sentinel = object()
        while True:
            if cancelled.is_set():
                state = "cancelled";yield event(state);return
            if time.monotonic() > deadline:raise TimeoutError()
            pending = asyncio.get_running_loop().run_in_executor(_executor, next, iterator, sentinel)
            while not pending.done():
                if cancelled.is_set():
                    state = "cancelled";yield event(state);return
                if time.monotonic() > deadline:raise TimeoutError()
                await asyncio.wait({pending}, timeout=.025)
            if cancelled.is_set():
                state = "cancelled";yield event(state);return
            chunk = pending.result();pending = None
            if cancelled.is_set():
                state = "cancelled";yield event(state);return
            if chunk is sentinel:
                state = "completed";yield event("end", full_response=full);return
            full += chunk
            yield event("chunk", content=chunk)
    except asyncio.CancelledError:
        state = "cancelled";cancelled.set();raise
    except Exception:
        cancelled.set()
        logger.exception("Turn failed: %s", turn_id)
        yield event("error", content="Generation failed. Check the audience/conversation selection or retry.")
    finally:
        cancelled.set()
        if lock_task is not None and not acquired:
            if not lock_task.done():lock_task.cancel()
            else:
                try:
                    if lock_task.result():acquired = True
                except asyncio.CancelledError:pass
        # Keep the lease/capacity and conversation lock until the SDK next()
        # returns; never close a generator executing in another thread.
        task = asyncio.create_task(cleanup());_draining.add(task)
        task.add_done_callback(_draining.discard)
        if pending is None or pending.done():await asyncio.shield(task)

@app.post("/api/turns/{turn_id}/cancel")
async def cancel_turn(turn_id: UUID):
    key = str(turn_id);flag = _active.get(key)
    if flag:
        flag.set()
    else:
        now = time.monotonic()
        for expired in [k for k,v in _pending_cancels.items() if v < now]:_pending_cancels.pop(expired, None)
        if len(_pending_cancels) >= 256:_pending_cancels.pop(next(iter(_pending_cancels)))
        _pending_cancels[key] = now + 60
    return {"status": "cancellation_requested"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    conversation_id = str(request.conversation_id)
    turn_id = str(request.turn_id or uuid4())
    if request.stream:
        async def stream():
            async for item in events(request.message, conversation_id, turn_id, request.style):
                yield "data: " + json.dumps(item) + "\n\n"
        return StreamingResponse(stream(), media_type="text/event-stream")
    result = ""
    async for item in events(request.message, conversation_id, turn_id, request.style):
        if item["type"] == "chunk":
            result += item["content"]
        if item["type"] == "error":
            raise HTTPException(503, item["content"])
    return {"response": result, "conversation_id": conversation_id, "turn_id": turn_id}

@app.get("/api/chat/greeting")
async def get_greeting():
    return {"greeting": "TARS online. Ready when you are."}

@app.websocket("/api/ws/chat")
async def websocket_chat(websocket: WebSocket):
    if websocket.headers.get("origin") not in ORIGINS | {None} or not authenticated(websocket.headers, websocket.cookies):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    await websocket.send_json({"type": "greeting", "content": "TARS connected."})
    try:
        while True:
            raw = await websocket.receive_text()
            if len(raw.encode()) > 65536:
                await websocket.close(code=1009)
                return
            try:
                data = json.loads(raw)
            except ValueError:
                await websocket.send_json({"type": "error", "content": "Invalid JSON"})
                continue
            try:
                request = ChatRequest.model_validate(data)
            except ValidationError:
                await websocket.send_json({"type": "error", "content": "Invalid chat request"})
                continue
            async for item in events(request.message, str(request.conversation_id), str(request.turn_id or uuid4()), request.style):
                await websocket.send_json(item)
    except WebSocketDisconnect:
        pass

# === Settings Endpoints ===

@app.get("/api/settings", response_model=SettingsResponse)
async def get_settings():
    """Get current TARS personality settings."""
    await asyncio.to_thread(get_engine)
    config = get_config()
    
    return SettingsResponse(
        humor=int(config.tars_humor_level * 100),
        honesty=int(config.tars_honesty_level * 100),
        discretion=int(config.tars_discretion_level * 100),
        responseSpeed=60,
        verbosity=50,
        cautionLevel=40,
        trustLevel=70
    )


@app.put("/api/settings", response_model=SettingsResponse)
async def update_settings(request: SettingsRequest):
    """Update TARS personality settings."""
    if _active:
        raise HTTPException(409, "Wait for active turns before changing settings")
    engine = await asyncio.to_thread(get_engine)
    
    humor = request.humor / 100 if request.humor is not None else None
    honesty = request.honesty / 100 if request.honesty is not None else None
    discretion = request.discretion / 100 if request.discretion is not None else None
    
    if any(getattr(request, key) is not None for key in ("responseSpeed", "verbosity", "cautionLevel", "trustLevel")):
        raise HTTPException(422, "Extended settings are not supported")
    settings = engine.update_personality(humor=humor, honesty=honesty, discretion=discretion)
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO settings VALUES (1,?)", (json.dumps(settings),))
    
    return SettingsResponse(
        humor=settings["humor"],
        honesty=settings["honesty"],
        discretion=settings["discretion"],
        responseSpeed=request.responseSpeed if request.responseSpeed is not None else 60,
        verbosity=request.verbosity if request.verbosity is not None else 50,
        cautionLevel=request.cautionLevel if request.cautionLevel is not None else 40,
        trustLevel=request.trustLevel if request.trustLevel is not None else 70
    )


# === History Endpoints ===

@app.get("/api/history")
async def get_history(conversation_id: UUID):
    """Get conversation history."""
    engine = await asyncio.to_thread(get_engine)
    selected_id = str(conversation_id) if conversation_id else None
    history = engine.get_conversation_history(selected_id)
    conversation = engine.memory.get_conversation(selected_id)
    audience = next((m.metadata.get("audience", "owner") for m in conversation.messages if m.role == "user"), "owner") if conversation else "owner"
    
    return {
        "conversation_id": selected_id or engine.memory.active_conversation_id,
        "messages": history,
        "audience": audience,
        "count": len(history)
    }


@app.delete("/api/history")
async def clear_history(conversation_id: UUID):
    """Clear conversation history."""
    if _active:
        raise HTTPException(409, "Wait for active turns before clearing history")
    engine = await asyncio.to_thread(get_engine)
    engine.clear_memory(str(conversation_id) if conversation_id else None)
    
    return {"message": "Conversation history cleared", "status": "success"}


# === RAG Endpoints ===

@app.get("/api/rag/stats", response_model=RAGStatsResponse)
async def get_rag_stats():
    """Get RAG system statistics."""
    engine = await asyncio.to_thread(get_engine)
    
    if not engine.use_rag or not engine.rag_system:
        raise HTTPException(status_code=503, detail="RAG system not enabled")
    
    stats = engine.rag_system.get_stats()
    return RAGStatsResponse(**stats)


@app.post("/api/rag/index")
async def index_datasets(directory: str = None):
    """Index datasets for RAG. Uses default directory if not specified."""
    engine = await asyncio.to_thread(get_engine)
    
    if not engine.use_rag or not engine.rag_system:
        raise HTTPException(status_code=503, detail="RAG system not enabled")
    
    try:
        if directory:
            allowed = (get_config().project_root / "Datasets Questions and Answers of TARS").resolve()
            selected = Path(directory).resolve()
            if not selected.is_relative_to(allowed):
                raise HTTPException(403, "Ingestion path denied")
            count = await asyncio.to_thread(engine.rag_system.index_directory, selected)
        else:
            # Re-index default datasets
            config = get_config()
            datasets_dir = config.project_root / "Datasets Questions and Answers of TARS"
            count = await asyncio.to_thread(engine.rag_system.index_directory, datasets_dir)
        
        return {"indexed": count, "total": engine.rag_system.get_stats()["total_documents"]}
    
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Indexing failed")


@app.post("/api/rag/search")
async def search_rag(query: str, n_results: int = Query(default=5, ge=1, le=20), topic: str = None):
    """Search the RAG knowledge base."""
    engine = await asyncio.to_thread(get_engine)
    
    if not engine.use_rag or not engine.rag_system:
        raise HTTPException(status_code=503, detail="RAG system not enabled")
    
    context = await asyncio.to_thread(engine.rag_system.retrieve, query, n_results=n_results, topic=topic)
    
    return {"query": query, "results": context}


# Run with uvicorn
def run_api(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Run the API server."""
    import uvicorn
    uvicorn.run("src.interfaces.api:app", host=host, port=port, reload=reload)





# Routes inherit the application's owner authentication/origin middleware.
from src.interfaces.media_api import router as media_router
app.include_router(media_router)
from src.interfaces.memory_api import router as memory_router
app.include_router(memory_router)
from src.interfaces.tools_api import router as tools_router
app.include_router(tools_router)
from src.interfaces.jobs_api import router as jobs_router
app.include_router(jobs_router)

@app.get("/api/conversations")
async def list_conversations():
    engine = await asyncio.to_thread(get_engine)
    return {"conversations": await asyncio.to_thread(engine.memory.list_conversations)}

if __name__ == "__main__":
    run_api()
