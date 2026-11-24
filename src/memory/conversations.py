"""Conversation adapter and hash-checked, repeatable legacy import."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
import hashlib
import json
from zoneinfo import ZoneInfo
from src.core.memory_store import Conversation, Message
from .repository import now
from .assertions import assertions
import logging


class DurableMemoryStore:
    def __init__(self, repository, owner='owner'):
        self.repository = repository
        self.owner = owner
        self.active_conversation_id = None

    def create_conversation(self, conversation_id=None):
        conversation_id = str(conversation_id or uuid4())
        with self.repository.transaction() as db:
            existing = db.execute('SELECT owner FROM conversations WHERE id=?', (conversation_id,)).fetchone()
            if existing and existing['owner'] != self.owner:
                raise PermissionError('Conversation belongs to another owner')
            db.execute('INSERT INTO conversations VALUES (?,?,?,NULL) ON CONFLICT DO NOTHING', (conversation_id,self.owner,now()))
        self.active_conversation_id = conversation_id
        return self.get_conversation(conversation_id)

    def get_conversation(self, conversation_id=None):
        selected = conversation_id or self.active_conversation_id
        with self.repository.transaction() as db:
            row = db.execute('SELECT * FROM conversations WHERE id=? AND owner=?', (selected,self.owner)).fetchone()
            if not row:
                return None
            messages = db.execute('SELECT * FROM messages WHERE conversation=? AND owner=? ORDER BY created_at,id', (selected,self.owner)).fetchall()
        return Conversation(id=row['id'],created_at=row['created_at'],metadata={'legacy_id':row['legacy_id']},
                            messages=[Message(role=m['role'],content=m['content'],timestamp=m['created_at'],metadata=json.loads(m['metadata'])) for m in messages])

    def get_or_create_active(self):
        return self.get_conversation() or self.create_conversation()

    def add_message(self, role, content, conversation_id=None, metadata=None):
        selected = conversation_id or self.active_conversation_id or str(uuid4())
        self.create_conversation(selected)
        timestamp = now()
        message_id = str(uuid4())
        captured = []
        with self.repository.transaction() as db:
            db.execute('INSERT INTO messages VALUES (?,?,?,?,?,?,?)', (message_id,selected,self.owner,role,content,timestamp,json.dumps(metadata or {})))
            if role == 'user' and (metadata or {}).get('capture_assertions') and metadata.get('audience') == 'owner':
                for predicate,value in assertions(content):
                    claim = self.repository.capture(db,self.owner,predicate,value,selected,message_id)
                    if claim:
                        captured.append(claim)
        for claim in captured:
            try:
                self.repository.index_captured(self.owner,claim)
            except Exception:
                logging.getLogger(__name__).warning('Memory index deferred; canonical fact available.')
        return Message(role=role,content=content,timestamp=timestamp,metadata=metadata or {})

    def get_history(self, conversation_id=None, max_messages=None):
        conversation = self.get_conversation(conversation_id)
        return conversation.get_history(max_messages) if conversation else []

    def clear_conversation(self, conversation_id=None):
        with self.repository.transaction() as db:
            db.execute('DELETE FROM messages WHERE conversation=? AND owner=?', (conversation_id or self.active_conversation_id,self.owner))

    def delete_conversation(self, conversation_id):
        with self.repository.transaction() as db:
            db.execute('DELETE FROM messages WHERE conversation=? AND owner=?', (conversation_id,self.owner))
            deleted = db.execute('DELETE FROM conversations WHERE id=? AND owner=?', (conversation_id,self.owner)).rowcount
        return bool(deleted)

    def list_conversations(self):
        with self.repository.transaction() as db:
            rows = db.execute('SELECT c.id,c.created_at,c.legacy_id,COUNT(m.id) AS message_count FROM conversations c LEFT JOIN messages m ON m.conversation=c.id AND m.owner=c.owner WHERE c.owner=? GROUP BY c.id,c.created_at,c.legacy_id ORDER BY c.created_at DESC', (self.owner,)).fetchall()
        return [dict(row) for row in rows]


def import_legacy(repository, directory, backup_directory, owner='owner', timezone_name='UTC'):
    directory, backup_directory = Path(directory), Path(backup_directory)
    files = sorted(directory.glob('*.json'))
    prepared = []
    # Parse and validate every source before any mutation; originals are never changed.
    for path in files:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw.decode('utf-8'))
        legacy = str(data['id'])
        try:
            canonical = str(UUID(legacy))
        except ValueError:
            canonical = str(uuid5(NAMESPACE_URL, f'tars:{owner}:{legacy}'))
        messages = data.get('messages',[])
        if not isinstance(messages,list) or any(not isinstance(m,dict) or m.get('role') not in {'user','assistant','system'} or not isinstance(m.get('content'),str) for m in messages):
            raise ValueError(f'Invalid legacy messages: {path.name}')
        prepared.append((path,raw,digest,data,canonical))
    backup_directory.mkdir(parents=True,exist_ok=True)
    with repository.transaction() as db:
        for path,raw,digest,data,canonical in prepared:
            old = db.execute('SELECT digest FROM imports WHERE owner=? AND source=?', (owner,path.name)).fetchone()
            if old and old['digest'] != digest:
                raise ValueError(f'Legacy file changed after import: {path.name}; review before importing')
    for path,raw,digest,data,canonical in prepared:
        snapshot = backup_directory / (digest+'.json')
        if snapshot.exists() and hashlib.sha256(snapshot.read_bytes()).hexdigest() != digest:
            raise ValueError('Legacy snapshot integrity failure')
        if not snapshot.exists():
            snapshot.write_bytes(raw)
    imported = 0
    with repository.transaction() as db:
        for path,raw,digest,data,canonical in prepared:
            old = db.execute('SELECT digest FROM imports WHERE owner=? AND source=?', (owner,path.name)).fetchone()
            if old:
                continue
            # Never overwrite live conversations or a different legacy file with the same ID.
            if db.execute('SELECT id FROM conversations WHERE id=?', (canonical,)).fetchone():
                raise ValueError(f'Conversation ID collision: {path.name}')
            db.execute('INSERT INTO conversations VALUES (?,?,?,?)', (canonical,owner,data.get('created_at',now()),str(data['id'])))
            for index,message in enumerate(data.get('messages',[])):
                message_id = str(uuid5(NAMESPACE_URL, f'{owner}:{path.name}:{index}'))
                # Preserve old timestamp verbatim; position breaks ties deterministically.
                metadata = {**message.get('metadata',{}),'legacy_position':index,'legacy_timestamp':message.get('timestamp')}
                base = datetime.fromisoformat(data.get('created_at',now()))
                if base.tzinfo is None:
                    base = base.replace(tzinfo=timezone.utc if timezone_name == "UTC" else ZoneInfo(timezone_name))
                    metadata['legacy_timezone_assumption'] = timezone_name
                timestamp = (base.astimezone(timezone.utc) + timedelta(microseconds=index)).isoformat()
                db.execute('INSERT INTO messages VALUES (?,?,?,?,?,?,?)', (message_id,canonical,owner,message['role'],message['content'],timestamp,json.dumps(metadata)))
            count = db.execute('SELECT COUNT(*) AS n FROM messages WHERE conversation=? AND owner=?', (canonical,owner)).fetchone()['n']
            if count != len(data.get('messages',[])):
                raise ValueError('Import count mismatch')
            db.execute('INSERT INTO imports VALUES (?,?,?,?)', (owner,path.name,digest,canonical))
            imported += 1
    return {'files':len(files),'imported':imported,'messages':sum(len(x[3].get('messages',[])) for x in prepared)}
