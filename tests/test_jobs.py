"""Synthetic repository/queue/worker tests; no source credential or cloud access."""
from pathlib import Path
from uuid import uuid4
import json,subprocess,time
import pytest
from src.memory.repository import Repository
from src.jobs.store import JobStore,JobRequest
from src.jobs.workspace import JobError,artifacts
from src.jobs.worker import execute_job

@pytest.fixture
def setup(tmp_path):
    source=tmp_path/'source';source.mkdir();(source/'tests').mkdir()
    (source/'maths.py').write_text('def add(a,b):\n    return a-b\n')
    (source/'tests'/'test_math.py').write_text('import unittest\nfrom maths import add\nclass TestMath(unittest.TestCase):\n def test_add(self): self.assertEqual(add(2,3),5)\n')
    (source/'.env').write_text('OWNER_TOKEN=do-not-copy')
    (source/'data').mkdir();(source/'data'/'private.json').write_text('{"private":true}')
    subprocess.run(['git','init','-q',str(source)],check=True)
    subprocess.run(['git','-C',str(source),'add','.'],check=True)
    subprocess.run(['git','-C',str(source),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','baseline'],check=True)
    store=JobStore(Repository(tmp_path/'state.db'),tmp_path/'jobs',{'test':source},True)
    return source,store

def prepare(store,**kwargs):
    return store.create('owner',JobRequest(repository='test',objective='Fix addition to add both inputs correctly.',paths=['.'],checks=['python-syntax','python-unittest'],request_key=str(uuid4()),**kwargs))

def test_snapshot_excludes_private_and_is_immutable_approval(setup):
    source,store=setup;job=prepare(store);folder=store.folder(job['id'])
    assert not (folder/'workspace'/'.env').exists()
    assert not (folder/'workspace'/'data').exists()
    assert len(job['manifest']['files'])==2
    assert store.claim('worker') is None
    with pytest.raises(JobError):store.approve('owner',job['id'],'0'*64)
    (folder/'workspace'/'maths.py').write_text('changed')
    with pytest.raises(JobError,match='snapshot changed'):store.approve('owner',job['id'],job['approval_digest'])
    assert (source/'maths.py').read_text().endswith('return a-b\n')

def test_approval_owner_idempotency_and_cancel(setup):
    source,store=setup;key=str(uuid4())
    req=JobRequest(repository='test',objective='Fix addition to add numbers.',paths=['maths.py'],request_key=key)
    first=store.create('owner',req);assert store.create('owner',req)['id']==first['id']
    with pytest.raises(JobError):store.get('other',first['id'])
    store.approve('owner',first['id'],first['approval_digest'])
    with pytest.raises(JobError):store.approve('owner',first['id'],first['approval_digest'])
    store.cancel('owner',first['id']);assert store.claim('worker') is None
    assert store.get('owner',first['id'])['state']=='cancelled'

def test_expired_lease_is_not_blindly_retried(setup):
    source,store=setup;job=prepare(store);store.approve('owner',job['id'],job['approval_digest'])
    claimed=store.claim('one');assert claimed
    with store.repository.transaction() as db:db.execute("UPDATE coding_jobs SET lease_until='2000-01-01T00:00:00+00:00' WHERE id=?",(job['id'],))
    assert store.claim('two') is None
    assert store.get('owner',job['id'])['state']=='interrupted'
    assert store.heartbeat(job['id'],'one')=='lease_lost'
    assert not store.finish(job,'one','completed',{})

class FakeAdapter:
    def preflight(self,root,cancel):return {'available':True,'evidence':'synthetic test preflight'}
    def run(self,job,folder,cancel):
        path=folder/'workspace'/'maths.py';path.write_text('def add(a,b):\n    return a+b\n')
        (folder/'workspace'/'new.py').write_text('VALUE=1\n')
        return {'exit_code':0,'usage':{'output_tokens':10}}
    def check(self,profile,workspace,timeout,cancel):return {'profile':profile,'exit_code':0,'output':'synthetic test evidence'}

def test_worker_diff_and_actual_source_unchanged(setup):
    source,store=setup;job=prepare(store);store.approve('owner',job['id'],job['approval_digest']);claimed=store.claim('w')
    assert execute_job(store,claimed,'w',FakeAdapter())=='completed'
    result=store.get('owner',job['id'])['result']
    assert '+    return a+b' in result['patch']
    assert any(change['status']=='added' for change in result['changed_files'])
    assert result['checks_passed'] is True
    assert 'return a-b' in (source/'maths.py').read_text()

def test_sandbox_failure_does_not_invoke_agent(setup):
    source,store=setup;job=prepare(store);store.approve('owner',job['id'],job['approval_digest']);claimed=store.claim('w')
    class Blocked(FakeAdapter):
        def preflight(self,*a):return {'available':False,'evidence':'provisioner unavailable'}
        def run(self,*a):raise AssertionError('Must not invoke cloud adapter')
    assert execute_job(store,claimed,'w',Blocked())=='failed'
    result=store.get('owner',job['id'])
    assert 'no source was sent' in result['error']
    assert result['result']['checks_passed'] is None

@pytest.mark.parametrize('path',['../source','.runtime','C:/Windows','a\\b','/tmp'])
def test_path_escapes_rejected(setup,path):
    source,store=setup
    with pytest.raises(JobError):store.create('owner',JobRequest(repository='test',objective='Test invalid path selection.',paths=[path],request_key=str(uuid4())))

def test_failures_and_cancellation_are_not_success(setup):
    source,store=setup;job=prepare(store);store.approve('owner',job['id'],job['approval_digest']);claimed=store.claim('w')
    class Failed(FakeAdapter):
        def check(self,*args):return {'profile':args[0],'exit_code':1,'output':'real check failed (synthetic fixture)'}
    assert execute_job(store,claimed,'w',Failed())=='failed'
    assert store.get('owner',job['id'])['result']['checks_passed'] is False


def test_running_cancel_prevents_cloud_execution(setup):
    _,store=setup;job=prepare(store);store.approve('owner',job['id'],job['approval_digest']);claimed=store.claim('w')
    class Cancelled(FakeAdapter):
        def preflight(self,root,cancel):
            store.cancel('owner',job['id'])
            assert cancel()=='cancelled'
            return {'available':True,'evidence':'synthetic'}
        def run(self,*args):raise AssertionError('cancelled jobs cannot call cloud')
    assert execute_job(store,claimed,'w',Cancelled())=='cancelled'
    assert store.get('owner',job['id'])['state']=='cancelled'


def test_cloud_disabled_and_restart_preserves_waiting_jobs(setup):
    _,store=setup;job=prepare(store)
    restarted=JobStore(store.repository,store.root,store.repositories,False)
    assert restarted.get('owner',job['id'])['state']=='waiting_for_approval'
    with pytest.raises(JobError,match='not enabled'):restarted.approve('owner',job['id'],job['approval_digest'])


def test_process_bounds_and_stream_tail(tmp_path):
    import os,sys
    from src.jobs.process import bounded,ProcessLimit
    result=bounded([sys.executable,'-c',"print('tail',end='')"],tmp_path,os.environ.copy(),10)
    assert result['output']=='tail' and result['exit_code']==0
    with pytest.raises(ProcessLimit,match='deadline_exceeded'):
        bounded([sys.executable,'-c','import time;time.sleep(10)'],tmp_path,os.environ.copy(),.2)
    with pytest.raises(ProcessLimit,match='output_budget_exceeded'):
        bounded([sys.executable,'-c',"print('x'*10000)"],tmp_path,os.environ.copy(),10,max_output=100)


def test_codex_policy_and_environment_do_not_inherit_secrets(monkeypatch,tmp_path):
    from src.agents.codex import CodexAdapter
    monkeypatch.setenv('OWNER_TOKEN','secret-owner')
    monkeypatch.setenv('OPENAI_API_KEY','secret-provider')
    monkeypatch.setenv('GIT_DIR','outside')
    env=CodexAdapter.env()
    assert not {'OWNER_TOKEN','OPENAI_API_KEY','GIT_DIR'} & env.keys()
    command=CodexAdapter(executable='codex').sandbox_command(tmp_path,['python','check.py'])
    assert 'permissions.tars-job.network.enabled=false' in command
    assert ':root' in ' '.join(command) and 'deny' in ' '.join(command)


def test_patch_handles_missing_final_newline(setup):
    _,store=setup;job=prepare(store);folder=store.folder(job['id'])
    (folder/'workspace'/'new.py').write_text('VALUE=1')
    patch=artifacts(folder,job['manifest'])['patch']
    assert '+VALUE=1\n\\ No newline at end of file\n' in patch
