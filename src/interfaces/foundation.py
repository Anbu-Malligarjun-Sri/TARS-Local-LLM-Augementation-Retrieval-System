"""Single-owner authentication and transactional foundation state.

Configure OWNER_TOKEN in the server environment. Browser pairing exchanges that
secret for a revocable, hashed, HttpOnly device session. No secret in WS URLs.
"""
import hashlib
import secrets
import sqlite3
import time
from pathlib import Path
from fastapi import HTTPException
from src.utils.config import get_config

ORIGINS = {"http://localhost:8081", "http://127.0.0.1:8081"}

def connect():
    path = get_config().project_root / '.runtime' / 'foundation.sqlite3'
    path.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE IF NOT EXISTS devices (token TEXT PRIMARY KEY, expires REAL)')
    db.execute('CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, value TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS turns (id TEXT PRIMARY KEY, conversation TEXT, state TEXT, error TEXT)')
    return db

def authenticated(headers, cookies):
    expected = get_config().owner_token
    if not expected:
        return False
    bearer = headers.get('authorization', '').removeprefix('Bearer ')
    if bearer and secrets.compare_digest(bearer, expected):
        return True
    token = cookies.get('tars_device', '')
    with connect() as db:
        return db.execute('SELECT 1 FROM devices WHERE token=? AND expires>?',
                          (hashlib.sha256(token.encode()).hexdigest(), time.time())).fetchone() is not None

def pair(token):
    expected = get_config().owner_token
    if not expected or not secrets.compare_digest(token, expected):
        raise HTTPException(401, 'Invalid pairing token')
    value = secrets.token_urlsafe(32)
    with connect() as db:
        db.execute('INSERT INTO devices VALUES (?,?)',
                   (hashlib.sha256(value.encode()).hexdigest(), time.time()+86400*30))
    return value
