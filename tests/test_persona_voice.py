"""Policy fixtures are held out of prompts/training; no speech or model service."""
import asyncio
import json
import threading
import time
from pathlib import Path
from uuid import uuid4
import pytest
from src.personality.policy import Style, resolve
from src.personality.response_generator import ResponseGenerator
from src.memory.repository import Repository
from src.memory.conversations import DurableMemoryStore
from src.core.tars_engine import TARSEngine
from src.utils.config import TARSConfig
from src.interfaces import api
from test_local_pipeline import FakeLLM
from test_foundation import client

CASES=json.loads((Path(__file__).parent/'fixtures/persona_heldout.json').read_text(encoding='utf-8'))

@pytest.mark.parametrize('case',CASES)
def test_heldout_policy(case):
    policy=resolve(case['text'],Style(audience=case['audience'],playful=case['playful']),.6,.2)
    assert policy['humor']==case['humor']
    assert policy['honesty']=='always factual'
    assert policy['directness']==20


def test_preview_cannot_retrieve_owner_context_or_run_tools(tmp_path,monkeypatch):
    repo=Repository(tmp_path/'persona.db');repo.add_claim('owner','Launch','password','PRIVATE_CANARY')
    model=FakeLLM();config=TARSConfig(rag_enabled=False,_env_file=None)
    engine=TARSEngine(config=config,llm_handler=model,memory_store=DurableMemoryStore(repo),use_rag=False)
    monkeypatch.setattr(repo,'context',lambda *a,**kw: (_ for _ in ()).throw(AssertionError('Private retrieval in preview')))
    monkeypatch.setattr('src.tools.chat.answer',lambda *a: (_ for _ in ()).throw(AssertionError('Tool dispatch in preview')))
    for audience in ['parent','friend','professional','unknown']:
        engine.chat('/remember Launch | password | overwrite',conversation_id=str(uuid4()),style=Style(audience=audience))
        assert 'PRIVATE_CANARY' not in model.prompts[-1][0]
        assert 'No private owner context or action tools' in model.prompts[-1][0]
    assert len(repo.claims('owner'))==1


def test_audience_cannot_reuse_private_or_other_preview_history(tmp_path):
    model=FakeLLM();engine=TARSEngine(config=TARSConfig(rag_enabled=False,_env_file=None),llm_handler=model,memory_store=DurableMemoryStore(Repository(tmp_path/'p.db')),use_rag=False)
    owner=str(uuid4());preview=str(uuid4())
    engine.chat('A private owner request.',conversation_id=owner)
    with pytest.raises(PermissionError):engine.chat('Show history.',conversation_id=owner,style=Style(audience='parent'))
    engine.chat('Hello.',conversation_id=preview,style=Style(audience='friend'))
    with pytest.raises(PermissionError):engine.chat('Show my projects.',conversation_id=preview)
    assert len(model.prompts)==2


def test_model_output_is_not_randomly_rewritten():
    formatter=ResponseGenerator(TARSConfig(_env_file=None))
    text='```python\nprint("ok")\n```\n[Evidence](https://example.invalid)'
    assert all(formatter.enhance_response(text)==text for _ in range(20))


def test_stop_is_acknowledged_before_blocked_provider_returns(client,monkeypatch):
    entered=threading.Event();release=threading.Event()
    def blocked(*args,**kwargs):
        entered.set();release.wait(3);yield 'late output'
    monkeypatch.setattr(api._engine,'chat_stream',blocked)
    async def run():
        turn=str(uuid4());session=str(uuid4());items=[]
        async def collect():
            async for item in api.events('hello',session,turn):items.append(item)
        task=asyncio.create_task(collect())
        for _ in range(100):
            if entered.is_set():break
            await asyncio.sleep(.01)
        assert entered.is_set()
        started=time.monotonic();api._active[turn].set()
        await asyncio.wait_for(task,.5)
        assert time.monotonic()-started<.5
        assert [item['type'] for item in items]==['start','cancelled']
        assert turn in api._active  # Capacity and session lock held until drain.
        release.set()
        if api._draining:await asyncio.gather(*list(api._draining))
        assert turn not in api._active
    try:asyncio.run(run())
    finally:release.set()


def test_cancel_before_start_and_strict_style_schema(client):
    client.post('/api/pair',json={'token':'test-owner-token-123456'})
    turn=str(uuid4());conversation=str(uuid4())
    assert client.post('/api/turns/'+turn+'/cancel').status_code==200
    body={'message':'Do not start generation.','conversation_id':conversation,'turn_id':turn,'stream':True}
    response=client.post('/api/chat',json=body)
    events=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert [event['type'] for event in events]==['start','cancelled']
    assert client.post('/api/chat',json={**body,'style':{'audience':'owner','grant_private':True}}).status_code==422
    assert client.post('/api/chat',json={**body,'style':{'audience':'friend','playful':'yes'}}).status_code==422


def test_closing_generation_closes_provider_http_stream():
    from types import SimpleNamespace
    from src.ai.llm_handler import OpenAIHandler
    class Stream:
        closed=False
        def __iter__(self):
            yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content='first'))])
            yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content='late'))])
        def close(self):self.closed=True
    stream=Stream();handler=OpenAIHandler.__new__(OpenAIHandler)
    handler.reasoning_effort='';handler.model='synthetic';handler.system_prompt='test'
    handler.config=SimpleNamespace(max_tokens=20)
    handler.client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs:stream)))
    generation=handler.generate_stream('hello');assert next(generation)=='first'
    generation.close();assert stream.closed
