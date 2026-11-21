"""Separate durable worker: never run coding jobs in an HTTP request handler."""
import argparse,json,time,traceback
from pathlib import Path
from uuid import uuid4
from .workspace import verify_snapshot,artifacts,JobError
from .process import ProcessLimit
from .service import get_store
from src.agents.codex import configured_adapter


def execute_job(store,job,worker,adapter):
    folder=store.folder(job['id']);output={'checks':[],'source_unchanged':True};deadline=time.monotonic()+job['spec']['timeout_seconds'];last=[0,None]
    def alive():
        if time.monotonic()-last[0]>1:
            last[:]=[time.monotonic(),store.heartbeat(job['id'],worker)]
        return last[1]
    state='failed';error=None
    try:
        verify_snapshot(folder,job['manifest'])
        preflight=adapter.preflight(folder/'preflight',alive);output['sandbox']=preflight
        if not preflight['available']:raise JobError('Sandbox preflight failed; no source was sent to Codex. '+preflight['evidence'][-1000:])
        remaining=int(deadline-time.monotonic())
        if remaining<1:raise ProcessLimit('deadline_exceeded')
        execution_job={**job,'spec':{**job['spec'],'timeout_seconds':remaining}}
        reason=alive()
        if reason:raise ProcessLimit(reason)
        agent=adapter.run(execution_job,folder,alive);output['agent']=agent
        if agent['exit_code']!=0:raise JobError('Codex exited unsuccessfully; inspect agent evidence')
        store.verifying(job,worker)
        for profile in job['spec']['checks']:
            if alive():raise ProcessLimit(alive())
            remaining=int(deadline-time.monotonic())
            if remaining<1:raise ProcessLimit('deadline_exceeded')
            output['checks'].append(adapter.check(profile,folder/'workspace',min(60,remaining),alive))
        output['checks_passed']=all(c['exit_code']==0 for c in output['checks']) if output['checks'] else None
        if output['checks_passed'] is False:raise JobError('Acceptance checks failed')
        state='completed'
    except ProcessLimit as exc:
        error=str(exc);state='cancelled' if error=='cancelled' else 'interrupted' if error=='lease_lost' else 'failed'
        if getattr(exc,'output',None):
            target=folder/'artifacts';target.mkdir(exist_ok=True);(target/'partial-process.log').write_text(exc.output,encoding='utf-8')
    except Exception as exc:
        error=str(exc)[:2000]
    finally:
        try:output.update(artifacts(folder,job['manifest']))
        except Exception as exc:
            state='failed';error='Artifact validation failed: '+str(exc)[:1000]
        if job['spec']['checks'] and len(output['checks'])!=len(job['spec']['checks']):output['checks_passed']=None
        output['limitations']=['No changes were applied to the source repository.','Token accounting is observed usage, not a hard provider price cap.','Completion is not independent proof of objective correctness.']
        target=folder/'artifacts';target.mkdir(exist_ok=True)
        (target/'result.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
        store.finish(job,worker,state,output,error)
    return state


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
    store=get_store();worker=str(uuid4())
    while True:
        job=store.claim(worker)
        if job:
            try:adapter=configured_adapter()
            except Exception as error:store.finish(job,worker,'failed',error=str(error));continue
            execute_job(store,job,worker,adapter)
        if args.once:break
        time.sleep(.7)

if __name__=='__main__':main()
