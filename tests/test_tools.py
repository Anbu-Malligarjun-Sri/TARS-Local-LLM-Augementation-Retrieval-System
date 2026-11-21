from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import pytest
from src.memory.repository import Repository
from src.tools.gateway import ToolGateway,ToolError
from src.tools.projects import Projects
from src.tools.calendar import LocalCalendar
from src.tools.web import PublicWeb,web_tools,WebResponse

@pytest.fixture
def gateway(tmp_path):
    repo=Repository(tmp_path/'tools.db')
    return ToolGateway(repo,Projects(repo).tools()+LocalCalendar(repo).tools()+web_tools(PublicWeb()))

def run(gateway,name,args=None,approve=False,key=None,owner='owner'):
    args=args or {};key=key or str(uuid4())
    approval=gateway.approve(owner,name,args)['approval_id'] if approve else None
    return gateway.execute(owner,name,args,key,approval)

def test_local_mutations_require_bound_approval_and_idempotent(gateway):
    args={'name':'TARS','notes':'Private project'}
    with pytest.raises(ToolError,match='approve'):run(gateway,'projects.create',args)
    approval=gateway.approve('owner','projects.create',args)['approval_id']
    with pytest.raises(ToolError,match='does not match'):
        gateway.execute('owner','projects.create',{'name':'Different'},str(uuid4()),approval)
    key=str(uuid4())
    first=gateway.execute('owner','projects.create',args,key,approval)
    again=gateway.execute('owner','projects.create',args,key,approval)
    assert again['result']==first['result']
    assert len(run(gateway,'projects.list')['result']['projects'])==1
    with pytest.raises(ToolError,match='different action'):
        gateway.execute('owner','projects.create',{'name':'Another'},key,approval)
    with pytest.raises(ToolError,match='consumed'):
        gateway.execute('owner','projects.create',args,str(uuid4()),approval)

def test_concurrent_duplicate_write_and_owner_scope(gateway):
    args={'name':'One project'};approval=gateway.approve('owner','projects.create',args)['approval_id'];key=str(uuid4())
    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes=list(pool.map(lambda _:gateway.execute('owner','projects.create',args,key,approval),range(4)))
    assert len({outcome['result']['id'] for outcome in outcomes})==1
    assert gateway.execute('other','projects.list',{},str(uuid4()),gateway.approve('other','projects.list',{})['approval_id'])['result']['projects']==[]

def test_grant_revocation_survives_gateway_restart(gateway):
    gateway.grant('owner','tasks.list',False)
    restarted=ToolGateway(gateway.repository,Projects(gateway.repository).tools())
    with pytest.raises(ToolError,match='approve'):run(restarted,'tasks.list')
    with pytest.raises(ToolError,match='private data'):
        gateway.execute('owner','projects.list',{},str(uuid4()),cloud=True)
    assert run(gateway,'tasks.list',approve=True)['state']=='completed'

def test_task_optimistic_updates_and_recoverable_completion(gateway):
    project=run(gateway,'projects.create',{'name':'TARS'},True)['result']
    task=run(gateway,'tasks.create',{'project_id':project['id'],'title':'Test tools'},True)['result']
    args={k:task[k] for k in ['id','project_id','title','notes','priority','due_at']}
    args.update(expected_version=1,status='done')
    changed=run(gateway,'tasks.update',args,True)['result']
    assert changed['status']=='done'
    assert run(gateway,'tasks.list')['result']['tasks']==[]
    with pytest.raises(ToolError,match='changed'):run(gateway,'tasks.update',args,True)
    args.update(expected_version=2,status='todo')
    run(gateway,'tasks.update',args,True)
    assert len(run(gateway,'tasks.list')['result']['tasks'])==1

def test_failure_has_no_mutation_and_audited(gateway):
    with pytest.raises(ToolError):run(gateway,'tasks.create',{'project_id':str(uuid4()),'title':'No parent'},True)
    with gateway.repository.transaction() as db:
        assert db.execute('SELECT COUNT(*) AS n FROM tasks').fetchone()['n']==0
        assert db.execute("SELECT COUNT(*) AS n FROM tool_audit WHERE action='failed'").fetchone()['n']>0

ICS='''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//TARS Test//EN
BEGIN:VEVENT
UID:daily
DTSTART;TZID=Asia/Kolkata:20261121T090000
DTEND;TZID=Asia/Kolkata:20261121T100000
RRULE:FREQ=DAILY;COUNT=3
EXDATE;TZID=Asia/Kolkata:20261122T090000
SUMMARY:Project review
END:VEVENT
BEGIN:VEVENT
UID:holiday
DTSTART;VALUE=DATE:20261122
DTEND;VALUE=DATE:20261123
SUMMARY:Day off
END:VEVENT
END:VCALENDAR'''

def test_calendar_recurrence_exceptions_all_day_and_freshness(gateway):
    assert not run(gateway,'calendar.read')['result']['configured']
    run(gateway,'calendar.import',{'content':ICS},True)
    result=run(gateway,'calendar.read',{'start':'2026-11-21','days':3})['result']
    assert len(result['events'])==3
    assert sum(e['all_day'] for e in result['events'])==1
    assert result['events'][0]['start'].endswith('+05:30')
    with gateway.repository.transaction() as db:
        db.execute("UPDATE calendar_snapshots SET imported_at='2000-01-01T00:00:00+00:00'")
    assert run(gateway,'calendar.read')['result']['stale']
    with pytest.raises(ToolError):run(gateway,'calendar.import',{'content':ICS.replace('FREQ=DAILY','FREQ=SECONDLY')},True)
    assert 'Project review' in run(gateway,'calendar.read',{'start':'2026-11-21','days':3})['result']['events'][0]['title']

def addresses(ip):return [(2,1,6,'',(ip,443))]
@pytest.mark.parametrize('url',['http://example.com','https://localhost/','https://127.0.0.1/','https://user:password@example.com','https://example.com:8443/','https://[::1]/'])
def test_ssrf_rejection(url):
    web=PublicWeb(resolver=lambda *a,**k:addresses('127.0.0.1'))
    with pytest.raises(ToolError):web.fetch(url)

def test_redirect_revalidation_and_dns_pinning():
    connected=[]
    class Response:
        status=302
        def getheader(self,name):return 'https://127.0.0.1/' if name=='Location' else None
    class Connection:
        def request(self,*a,**k):pass
        def getresponse(self):return Response()
        def close(self):pass
    def resolve(host,*a,**k):return addresses('127.0.0.1' if host=='127.0.0.1' else '93.184.216.34')
    def connect(host,ip,timeout):connected.append((host,ip));return Connection()
    web=PublicWeb(resolve,connect)
    with pytest.raises(ToolError):web.fetch('https://example.com')
    assert connected==[('example.com','93.184.216.34')]

def test_mixed_dns_is_rejected_and_html_script_stripped():
    web=PublicWeb(resolver=lambda *a,**k:addresses('93.184.216.34')+addresses('10.0.0.1'))
    with pytest.raises(ToolError):web.validate('https://example.com')
    web.fetch=lambda url:WebResponse(url,b'<title>Evidence</title><script>secret()</script><p>Useful fact</p>','text/html','2026-11-21T00:00:00Z')
    source=web.page('https://example.com')
    assert 'secret' not in source['evidence']
    assert 'Useful fact' in source['evidence']

def test_failed_local_run_is_visible_and_not_reexecuted(gateway):
    key=str(uuid4());args={'project_id':str(uuid4()),'title':'Invalid parent'}
    approval=gateway.approve('owner','tasks.create',args)['approval_id']
    with pytest.raises(ToolError):gateway.execute('owner','tasks.create',args,key,approval)
    outcome=gateway.execute('owner','tasks.create',args,key,approval)
    assert outcome['state']=='failed'
    assert outcome['error']=='project_missing'

def test_revocation_blocks_cached_read_and_restart_marks_interruption(gateway):
    key=str(uuid4());run(gateway,'projects.list',key=key)
    gateway.grant('owner','projects.list',False)
    with pytest.raises(ToolError):run(gateway,'projects.list',key=key)
    with gateway.repository.transaction() as db:
        db.execute("INSERT INTO tool_runs VALUES (?,?,?,?,?,'running',NULL,NULL,?,NULL)",(str(uuid4()),'owner','web.fetch',str(uuid4()),'hash','2026-11-21T00:00:00+00:00'))
    restarted=ToolGateway(gateway.repository,Projects(gateway.repository).tools())
    assert any(r['state']=='interrupted' for r in restarted.runs('owner'))

def test_calendar_dst_and_cancelled_override(gateway):
    content='''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//TARS Test//EN
BEGIN:VEVENT
UID:dst-series
DTSTART;TZID=America/New_York:20261031T090000
DTEND;TZID=America/New_York:20261031T100000
RRULE:FREQ=DAILY;COUNT=3
SUMMARY:Morning review
END:VEVENT
BEGIN:VEVENT
UID:dst-series
RECURRENCE-ID;TZID=America/New_York:20261102T090000
DTSTART;TZID=America/New_York:20261102T090000
DTEND;TZID=America/New_York:20261102T100000
STATUS:CANCELLED
SUMMARY:Cancelled review
END:VEVENT
END:VCALENDAR'''
    run(gateway,'calendar.import',{'content':content,'timezone':'America/New_York'},True)
    result=run(gateway,'calendar.read',{'start':'2026-10-31','days':3})['result']
    assert len(result['events'])==2
    assert result['events'][0]['start'].endswith('-04:00')
    assert result['events'][1]['start'].endswith('-05:00')

def test_fetch_budget_and_unsupported_content():
    class Response:
        status=200
        content_type='text/html'
        def getheader(self,name):return self.content_type if name=='Content-Type' else None
        def read1(self,size):return b'x'*size
    response=Response()
    class Connection:
        def request(self,*args,**kwargs):pass
        def getresponse(self):return response
        def close(self):pass
    web=PublicWeb(lambda *a,**k:addresses('93.184.216.34'),lambda *a:Connection())
    with pytest.raises(ToolError,match='too large'):web.fetch('https://example.com')
    response.content_type='application/octet-stream'
    with pytest.raises(ToolError,match='Only text'):web.fetch('https://example.com')
