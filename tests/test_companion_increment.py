import base64
import json
from uuid import uuid4

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from demo.api import create_app
from src.core.tars_engine import TARSEngine
from src.interfaces import media_api
from src.memory.assertions import assertions
from src.memory.conversations import DurableMemoryStore
from src.memory.repository import Repository
from src.personality.policy import Style, reply_language
from src.utils.config import TARSConfig
from test_local_pipeline import FakeLLM


def test_owner_assertions_persist_across_models_and_link_to_message(tmp_path):
    path = tmp_path/'memory.sqlite3'

    def engine(model):
        return TARSEngine(TARSConfig(_env_file=None),llm_handler=model,
                          memory_store=DurableMemoryStore(Repository(path)),use_rag=False)

    first = engine(FakeLLM())
    session = str(uuid4())
    first.chat('My name is Rani. I like chess.',conversation_id=session)
    first.chat('My name is Rani.',conversation_id=session)
    first.chat('My name is Nila.',conversation_id=session)
    first.chat('I live in Previewville.',conversation_id=str(uuid4()),style=Style(audience='friend'))
    model = FakeLLM()
    second = engine(model)
    list(second.chat_stream('En peru enna?',conversation_id=str(uuid4())))
    assert 'Nila' in model.prompts[-1][0]
    repo = second.memory.repository
    assert set(repo.graph('owner')['nodes']) == {'Me','Nila','chess'}
    assert repo.retrieve('owner','name',cloud=True)==[]
    fact = next(c for c in repo.claims('owner') if c['predicate']=='name')
    source = json.loads(repo.get_claim('owner',fact['id'])['source_content'])
    assert source['conversation_id']==session
    with repo.transaction() as db:
        assert db.execute('SELECT content FROM messages WHERE id=?',(source['message_id'],)).fetchone()[0]=='My name is Nila.'
    repo.forget('owner',fact['id'])
    assert repo.graph('owner')['nodes']==['Me','chess']


@pytest.mark.parametrize('text', [
    'If my name is Rain, what happens?', "My name is Rani. Don't save this.",
    'I like tea or coffee', 'My password is imaginary', 'My name is "Example".',
])
def test_no_automatic_claim_for_ambiguous_or_excluded_statement(text):
    assert assertions(text)==[]


@pytest.mark.parametrize(('text','expected'), [
    ('Enna panra','ta-Latn'),('Indha report epdi irukku?','ta-Latn'),
    ('Naalaikku lunch enga saapdalaam?','ta-Latn'),('Meeting notes konjam anuppu','ta-Latn'),
    ('Namma plan pathi pesalaama?','ta-Latn'),('Enna panreenga, answer in English','en-IN'),
    ('ஒரு கதை சொல்லு','ta-IN'),('Give me the Tamil alphabet in English','en-IN'),
    ('Should I change the meeting time?','en-IN'),('Can you review my notes?','en-IN'),
])
def test_romanized_and_mixed_turns(text,expected):
    assert reply_language(text)==expected


def test_scoped_turn_lifecycle_and_budget():
    app=create_app()
    opts=dict(base_url="http://visitor.localhost",headers={'X-Demo-Client':'1'})
    with TestClient(app,**opts) as alice, TestClient(app,**opts) as bob:
        alice.post('/demo/visit')
        bob.post('/demo/visit')
        def turn():
            return alice.post('/demo/turns',json={'message':'Plan today','language':'tanglish'})
        initial=turn().json()['id']
        assert bob.post(f'/demo/turns/{initial}/stream').status_code==404
        assert bob.post(f'/demo/turns/{initial}/stop').status_code==404
        assert alice.post(f'/demo/turns/{initial}/stop').status_code==204
        assert alice.post(f'/demo/turns/{initial}/stream').status_code==404
        for _ in range(4):
            identifier=turn().json()['id']
            stream=alice.post(f'/demo/turns/{identifier}/stream')
            events=[json.loads(line[6:]) for line in stream.text.splitlines() if line.startswith('data: ')]
            assert events[0]['type']=='start' and events[-1]['type']=='end'
            assert 'Innaikku' in stream.text
        assert turn().status_code==429


def test_face_profiles_consent_unknown_and_removal(tmp_path,monkeypatch):
    app=FastAPI()
    app.include_router(media_api.router)
    monkeypatch.setattr(media_api,'RUNTIME',tmp_path)
    client=TestClient(app)
    body={'rgb':base64.b64encode(bytes(192*192*3)).decode(),'consent':False}
    assert client.post('/api/media/faces/enroll',json={**body,'name':'Example'}).status_code==403
    vector=np.eye(3,dtype=np.float32)[0].copy()
    monkeypatch.setattr(media_api,'feature',lambda body: vector)
    body['consent']=True
    first=client.post('/api/media/faces/enroll',json={**body,'name':'Example A'}).json()
    vector[:]=[0,1,0]
    client.post('/api/media/faces/enroll',json={**body,'name':'Example B'}).raise_for_status()
    assert client.post('/api/media/faces/match',json=body).json()=={'name':'Example B'}
    vector[:]=[0,0,1]
    assert client.post('/api/media/faces/match',json=body).json()=={'name':None}
    client.delete('/api/media/faces/'+first['id']).raise_for_status()
    assert [p['name'] for p in client.get('/api/media/faces').json()]==['Example B']
