from test_foundation import client
from src.interfaces import api,launch

def test_launch_ticket_is_single_use_and_cookie_authenticates(client,monkeypatch):
    monkeypatch.setattr(launch,'connect',api.connect)
    ticket=launch.issue()
    result=client.post('/api/launch',json={'token':ticket})
    assert result.status_code == 200
    assert 'HttpOnly' in result.headers['set-cookie']
    assert client.get('/api/settings').status_code == 200
    assert client.post('/api/launch',json={'token':ticket}).status_code == 401

def test_expired_launch_ticket_rejected(client,monkeypatch):
    monkeypatch.setattr(launch,'connect',api.connect)
    ticket=launch.issue()
    with api.connect() as db:
        db.execute('UPDATE launch_tickets SET expires=0')
    assert client.post('/api/launch',json={'token':ticket}).status_code == 401
