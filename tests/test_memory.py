import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4
import pytest
from src.memory.repository import Repository
from src.memory.conversations import DurableMemoryStore, import_legacy
from src.core.tars_engine import TARSEngine
from src.utils.config import TARSConfig
from test_local_pipeline import FakeLLM, FakePersonality

@pytest.fixture
def repo(tmp_path):
    return Repository(tmp_path/'memory.db')

def test_claim_correction_forget_rebuild_restore(repo,tmp_path):
    claim = repo.add_claim('owner','Me','works_on','TARS')
    assert repo.retrieve('owner','TARS')[0]['source_id'] == claim['source_id']
    assert repo.status('owner')['pending_events'] == 1
    repo.project('owner')
    corrected = repo.add_claim('owner','Me','works_on','Personal intelligence',supersedes=claim['id'])
    assert repo.get_claim('owner',claim['id'])['state'] == 'superseded'
    assert repo.graph('owner')['edges'][0]['target'] == 'Personal intelligence'
    repo.project('owner')
    backup = repo.backup(tmp_path/'backup.db')
    restored = Repository(backup)
    assert restored.get_claim('owner',corrected['id'])['value'] == 'Personal intelligence'
    repo.forget('owner',corrected['id'])
    repo.project('owner')
    assert repo.retrieve('owner','Personal intelligence TARS') == []
    assert repo.graph('owner') == {'nodes':[],'edges':[]}
    assert repo.get_claim('owner',claim['id'])['source_content'] == '[forgotten]'
    assert repo.get_claim('owner',corrected['id'])['value'] == '[forgotten]'
    with repo.transaction() as db:
        assert db.execute('SELECT COUNT(*) AS n FROM vectors').fetchone()['n'] == 0

def test_owner_audience_cloud_and_expiration(repo):
    private = repo.add_claim('owner','Alice','phone','secret')
    shared = repo.add_claim('owner','Alice','likes','astronomy',audiences=['owner','friend'],sensitivity='shared',cloud_allowed=True)
    repo.add_claim('other','Alice','likes','private-other')
    repo.add_claim('owner','Alice','status','expired',valid_to='2000-01-01T00:00:00+00:00')
    assert [c['id'] for c in repo.retrieve('owner','Alice',audience='friend')] == [shared['id']]
    assert 'secret' not in repo.context('owner','Alice',cloud=True)
    assert 'private-other' not in repo.context('owner','Alice')
    assert 'expired' not in repo.context('owner','Alice')
    with pytest.raises(KeyError):
        repo.forget('other',private['id'])

def test_import_idempotent_and_never_reimports_cleared_content(repo,tmp_path):
    source = tmp_path/'legacy'; source.mkdir()
    path = source/'old.json'
    raw = json.dumps({'id':'conv_old','created_at':'2020-01-01T00:00:00','messages':[{'role':'user','content':str(i)} for i in range(70)]})
    path.write_text(raw)
    report = import_legacy(repo,source,tmp_path/'snapshots')
    assert report == {'files':1,'imported':1,'messages':70}
    store = DurableMemoryStore(repo)
    cid = store.list_conversations()[0]['id']
    assert [m['content'] for m in store.get_history(cid)] == [str(i) for i in range(70)]
    assert import_legacy(repo,source,tmp_path/'snapshots')['imported'] == 0
    store.clear_conversation(cid)
    import_legacy(repo,source,tmp_path/'snapshots')
    assert store.get_history(cid) == []
    assert path.read_text() == raw
    path.write_text(raw+' ')
    with pytest.raises(ValueError,match='changed'):
        import_legacy(repo,source,tmp_path/'snapshots')

def test_database_history_restart_and_concurrent_append(repo):
    store = DurableMemoryStore(repo)
    cid = str(uuid4())
    def append(i):
        store.add_message('user',str(i),cid)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(append,range(80)))
    restarted = DurableMemoryStore(Repository(repo.path))
    assert len(restarted.get_history(cid)) == 80
    with pytest.raises(PermissionError):
        DurableMemoryStore(repo,'other').add_message('user','no',cid)

def test_two_models_receive_identical_personal_context(repo):
    fact = repo.add_claim('owner','My mother','prefers','respectful replies',cloud_allowed=True)
    class AlternateProvider(FakeLLM):
        def generate(self,message,conversation_history=None):
            super().generate(message,conversation_history)
            return 'A different model response'
    for model,cloud in [(FakeLLM(),False),(AlternateProvider(),True)]:
        engine = TARSEngine(config=TARSConfig(rag_enabled=False,allow_cloud=cloud,_env_file=None), llm_handler=model,
                            memory_store=DurableMemoryStore(Repository(repo.path)),response_generator=FakePersonality(),use_rag=False)
        engine.chat('How does my mother prefer replies?',conversation_id=str(uuid4()))
        assert fact['id'] in model.prompts[0][0]
        assert 'respectful replies' in model.prompts[0][0]

def test_projection_failure_does_not_drop_fact(repo):
    repo.add_claim('owner','Project','status','ready')
    repo.embedder = lambda _: (_ for _ in ()).throw(RuntimeError('offline'))
    with pytest.raises(RuntimeError):
        repo.project('owner')
    assert repo.retrieve('owner','Project')[0]['value'] == 'ready'

def test_local_context_cannot_escape_through_old_history(repo):
    store = DurableMemoryStore(repo)
    model = FakeLLM()
    config = TARSConfig(rag_enabled=False,_env_file=None)
    engine = TARSEngine(config=config,llm_handler=model,memory_store=store,response_generator=FakePersonality(),use_rag=False)
    repo.add_claim('owner','My project','codename','Private constellation')
    cid = str(uuid4())
    engine.chat('What is my project codename?',conversation_id=cid)
    config.allow_cloud = True
    with pytest.raises(PermissionError,match='local-only'):
        engine.chat('Tell me more',conversation_id=cid)
    assert len(model.prompts) == 1


def test_semantic_projection_is_versioned_and_deletion_wins_race(repo):
    claim = repo.add_claim('owner','Me','enjoys','astronomy')
    def slow_embed(text):
        repo.forget('owner',claim['id'])
        return [1.0]+[0.0]*127
    repo.embedder = slow_embed
    repo.project('owner')
    with repo.transaction() as db:
        assert db.execute('SELECT COUNT(*) AS n FROM vectors').fetchone()['n'] == 0
        assert db.execute('SELECT COUNT(*) AS n FROM edges').fetchone()['n'] == 0
    assert repo.claims('owner') == []


def test_corrupt_import_does_not_partially_commit(repo,tmp_path):
    source = tmp_path/'bad-source'; source.mkdir()
    (source/'a.json').write_text(json.dumps({'id':'a','messages':[{'role':'user','content':'safe'}]}))
    (source/'b.json').write_text('{broken')
    with pytest.raises(ValueError):
        import_legacy(repo,source,tmp_path/'bad-snapshots')
    assert DurableMemoryStore(repo).list_conversations() == []
