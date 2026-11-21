"""Foundation contract tests; no live models or private runtime files."""
import asyncio
import json
import sqlite3
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from src.interfaces import api, foundation
from src.utils.config import TARSConfig
from src.ai.llm_handler import MultiProviderLLM
from test_local_pipeline import make_engine

@pytest.fixture
def client(monkeypatch, tmp_path):
    api._rates.clear()
    config = TARSConfig(owner_token='test-owner-token-123456', rag_enabled=False, _env_file=None)
    monkeypatch.setattr(foundation, 'get_config', lambda: config)
    monkeypatch.setattr(api, 'get_config', lambda: config)
    def database():
        db = sqlite3.connect(tmp_path / 'state.db')
        db.executescript('CREATE TABLE IF NOT EXISTS devices(token TEXT PRIMARY KEY, expires REAL); CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY,value TEXT); CREATE TABLE IF NOT EXISTS turns(id TEXT PRIMARY KEY,conversation TEXT,state TEXT,error TEXT);')
        return db
    monkeypatch.setattr(foundation, 'connect', database)
    monkeypatch.setattr(api, 'connect', database)
    engine, _, _ = make_engine()
    monkeypatch.setattr(api, '_engine', engine)
    with TestClient(api.app) as connection:
        yield connection


def test_pairing_origins_revocation_and_explicit_history(client):
    assert client.get('/api/settings').status_code == 401
    assert client.post('/api/pair', json={'token': 'wrong-token-1234567'}).status_code == 401
    assert client.post('/api/pair', json={'token': 'test-owner-token-123456'}).status_code == 200
    assert client.get('/api/settings').status_code == 200
    assert client.get('/api/history').status_code == 422
    assert client.get('/api/settings', headers={'origin': 'https://attacker.example'}).status_code == 403
    assert client.delete('/api/pair').status_code == 200
    assert client.get('/api/settings').status_code == 401


def test_sse_preserves_multiline_and_failure_is_terminal(client, monkeypatch):
    client.post('/api/pair', json={'token': 'test-owner-token-123456'})
    def chunks(*args, **kwargs):
        yield '```python\nprint("ok")\n```'
        raise RuntimeError('secret provider details')
    monkeypatch.setattr(api._engine, 'chat_stream', chunks)
    response = client.post('/api/chat', json={'message':'hello', 'stream':True, 'conversation_id': str(uuid4())})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert [e['type'] for e in events] == ['start','chunk','error']
    assert events[1]['content'] == '```python\nprint("ok")\n```'
    assert 'secret provider details' not in response.text
    assert len({e['turn_id'] for e in events}) == 1
    assert [e['sequence'] for e in events] == [1,2,3]


def test_cloud_default_rejects_primary():
    with pytest.raises(ValueError, match='ALLOW_CLOUD'):
        MultiProviderLLM(TARSConfig(llm_provider='openai', _env_file=None))


def test_local_fallback_list_excludes_cloud():
    model = MultiProviderLLM(TARSConfig(openai_api_key='fake', gemini_api_key='fake', _env_file=None))
    assert all(type(h).__name__ in {'LMStudioHandler','OllamaHandler'} for h in [model.primary_handler, *model.fallback_handlers])


def test_cancellation_records_partial_turn(client, monkeypatch):
    async def run():
        turn = str(uuid4())
        received = []
        async for event in api.events('hello', str(uuid4()), turn):
            received.append(event)
            if event['type'] == 'chunk':
                api._active[turn].set()
        return received
    received = asyncio.run(run())
    assert received[-1]['type'] == 'cancelled'
    assert not api._active


def test_settings_survive_engine_recreation(client, monkeypatch):
    client.post('/api/pair', json={'token': 'test-owner-token-123456'})
    def update(**values):
        for key, value in values.items():
            if value is not None:
                setattr(api.get_config(), 'tars_' + key + '_level', value)
        c = api.get_config()
        return {key: round(getattr(c, 'tars_' + key + '_level')*100) for key in ('humor','honesty','discretion')}
    monkeypatch.setattr(api._engine, 'update_personality', update)
    assert client.put('/api/settings', json={'humor': 24}).status_code == 200
    original = api._engine
    monkeypatch.setattr(api, 'get_tars_engine', lambda: original)
    api._engine = None
    assert client.get('/api/settings').json()['humor'] == 24
    assert client.put('/api/settings', json={'trustLevel': 100}).status_code == 422


def test_concurrent_sessions_and_same_session_serialization(client, monkeypatch):
    import time
    engine = api._engine
    active = set()
    overlap = []
    def stream(message, conversation_id, **turn_options):
        assert conversation_id not in active
        active.add(conversation_id)
        overlap.append(len(active))
        time.sleep(.03)
        yield message
        active.remove(conversation_id)
    monkeypatch.setattr(engine, 'chat_stream', stream)
    async def run():
        async def collect(session, message):
            return [event async for event in api.events(message, session, str(uuid4()))]
        a, b = str(uuid4()), str(uuid4())
        return await asyncio.gather(collect(a,'first'), collect(b,'second'), collect(a,'third'))
    results = asyncio.run(run())
    assert [events[-1]['full_response'] for events in results] == ['first','second','third']
    assert max(overlap) == 2
