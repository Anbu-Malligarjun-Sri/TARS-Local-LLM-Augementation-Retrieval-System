import pytest
from test_foundation import client
from src.interfaces import memory_api
from src.memory.repository import Repository

@pytest.fixture
def memory_client(client,monkeypatch,tmp_path):
    repo = Repository(tmp_path/'memories.db')
    monkeypatch.setattr(memory_api,'get_repository',lambda:repo)
    yield client,repo

def test_memory_api_auth_crud_provenance_and_scope(memory_client):
    client,repo = memory_client
    assert client.get('/api/memory').status_code == 401
    assert client.post('/api/memory',json={'subject':'x','predicate':'y','value':'z'}).status_code == 401
    client.post('/api/pair',json={'token':'test-owner-token-123456'})
    response = client.post('/api/memory',json={'subject':'Mother','predicate':'prefers','value':'respectful calls','owner':'attacker'})
    assert response.status_code == 200
    first = response.json()['claim']
    assert first['owner'] == 'owner'
    assert repo.claims('attacker') == []
    assert client.get('/api/memory/'+first['id']).json()['source_kind'] == 'owner_assertion'
    second = client.put('/api/memory/'+first['id'],json={'subject':'Mother','predicate':'prefers','value':'warm respectful calls'}).json()['claim']
    assert client.get('/api/memory/graph').json()['edges'][0]['target'] == 'warm respectful calls'
    assert client.get('/api/memory/search',params={'query':'Mother'}).json()['claims'][0]['id'] == second['id']
    assert len(client.get('/api/memory/export').json()['claims']) == 2
    assert client.delete('/api/memory/'+second['id']).status_code == 200
    assert client.get('/api/memory').json()['claims'] == []
    assert client.get('/api/memory/'+first['id']).json()['source_content'] == '[forgotten]'
    assert client.get('/api/memory/graph').json()['edges'] == []

def test_projection_recovery_and_validation(memory_client):
    client,repo = memory_client
    client.post('/api/pair',json={'token':'test-owner-token-123456'})
    bad = client.post('/api/memory',json={'subject':' ','predicate':'x','value':'y'})
    assert bad.status_code == 422
    assert client.post('/api/memory',json={'subject':'x','predicate':'y','value':'z','valid_to':'tomorrow'}).status_code == 422
    assert client.get('/api/memory/not-a-uuid').status_code == 422
    assert client.post('/api/memory/rebuild').status_code == 200
