"""Local operator launch links: single use, ten-minute lifetime, no owner secret in URL."""
import hashlib
import secrets
import time
from .foundation import connect
from fastapi import HTTPException


def issue():
    ticket=secrets.token_urlsafe(32)
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS launch_tickets (digest TEXT PRIMARY KEY, expires REAL NOT NULL)')
        db.execute('DELETE FROM launch_tickets WHERE expires<?',(time.time(),))
        db.execute('INSERT INTO launch_tickets VALUES (?,?)',(hashlib.sha256(ticket.encode()).hexdigest(),time.time()+600))
    return ticket


def redeem(ticket):
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS launch_tickets (digest TEXT PRIMARY KEY, expires REAL NOT NULL)')
        row=db.execute('DELETE FROM launch_tickets WHERE digest=? AND expires>? RETURNING digest',(hashlib.sha256(ticket.encode()).hexdigest(),time.time())).fetchone()
        if row is None:
            raise HTTPException(401,'Launch link expired or already used')
        token=secrets.token_urlsafe(32)
        db.execute('INSERT INTO devices VALUES (?,?)',(hashlib.sha256(token.encode()).hexdigest(),time.time()+86400*30))
    return token

if __name__=='__main__':
    print('http://localhost:8081/#launch='+issue())
