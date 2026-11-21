"""Authenticated review flow using only a synthetic source repository."""
from uuid import uuid4
from test_foundation import client
from test_jobs import setup
from src.interfaces import jobs_api


def test_jobs_require_auth_and_exact_approval(client, setup, monkeypatch):
    _, store = setup
    monkeypatch.setattr(jobs_api, 'get_store', lambda: store)
    assert client.get('/api/jobs').status_code == 401
    assert client.post('/api/jobs/preflight').status_code == 401
    client.post('/api/pair', json={'token': 'test-owner-token-123456'})
    assert client.get('/api/jobs/capabilities').json()['adapter'] == 'codex-cloud'
    body = dict(repository='test', objective='Fix the addition function.', paths=['.'], request_key=str(uuid4()))
    assert client.post('/api/jobs', json={**body, 'owner': 'someone'}).status_code == 422
    job = client.post('/api/jobs', json=body).json()
    assert job['state'] == 'waiting_for_approval'
    assert store.claim('test-worker') is None
    prefix = '/api/jobs/' + job['id']
    assert 'return a-b' in client.get(prefix+'/source', params={'path': 'maths.py'}).json()['content']
    assert client.get(prefix+'/source', params={'path': '.env'}).status_code == 403
    assert client.get(prefix+'/source', params={'path': '../manifest.json'}).status_code == 403
    assert client.post(prefix+'/approve', json={'approval_digest': '0'*64}).status_code == 409
    assert client.post(prefix+'/approve', json={'approval_digest': job['approval_digest']}).json()['state'] == 'queued'
    assert client.post(prefix+'/cancel').json()['state'] == 'cancelled'
    assert store.claim('test-worker') is None
    assert [e['event'] for e in client.get(prefix+'/events').json()['events']] == ['prepared', 'approved', 'cancel_requested']

