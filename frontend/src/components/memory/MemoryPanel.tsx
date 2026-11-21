import { useCallback, useState } from 'react';
import { Database, Search, Download, RefreshCw, Pencil, Trash2 } from 'lucide-react';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { memoryApi, type ClaimInput, type MemoryClaim, type MemoryGraph, type MemoryStatus } from '@/services/memoryApi';

const empty: ClaimInput = {subject:'', predicate:'', value:'', audiences:['owner'], sensitivity:'private', cloud_allowed:false, valid_to:null};
const button = 'border border-border rounded px-3 py-2 hover:bg-secondary disabled:opacity-50';
const input = 'w-full bg-background border border-border rounded px-3 py-2';

export function MemoryPanel() {
  const [open,setOpen] = useState(false);
  const [claims,setClaims] = useState<MemoryClaim[]>([]);
  const [graph,setGraph] = useState<MemoryGraph>({nodes:[],edges:[]});
  const [status,setStatus] = useState<MemoryStatus>();
  const [form,setForm] = useState<ClaimInput>(empty);
  const [editing,setEditing] = useState<string>();
  const [query,setQuery] = useState('');
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  const [notice,setNotice] = useState('');
  const [detail,setDetail] = useState<MemoryClaim>();
  const [pendingForget,setPendingForget] = useState<string>();
  const [tab,setTab] = useState<'facts'|'graph'>('facts');
  const refresh = useCallback(async () => {
    const [result,relationships] = await Promise.all([memoryApi.list(),memoryApi.graph()]);
    setClaims(result.claims); setStatus(result.status); setGraph(relationships);
  },[]);
  const run = async (action: () => Promise<void>) => {
    setBusy(true); setError('');
    try { await action(); } catch(e) { setError(e instanceof Error ? e.message : 'Memory operation failed'); }
    finally { setBusy(false); }
  };
  return <>
    <button className={`${button} w-full flex gap-2 items-center`} onClick={() => {setOpen(true); void run(refresh);}}><Database size={16}/> Personal memory</button>
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogTitle>Personal memory</DialogTitle>
        <DialogDescription>Owner-authored facts and relationships shared across your models. Facts are assertions with sources, not independently verified truths.</DialogDescription>
        <p className="text-xs text-muted-foreground">{status ? `${status.backend} · ${status.embedding_model} · ${status.pending_events} pending projection events` : 'Loading memory status…'}</p>
        <div className="flex flex-wrap gap-2">
          <button className={button} aria-pressed={tab==='facts'} onClick={() => setTab('facts')}>Facts</button>
          <button className={button} aria-pressed={tab==='graph'} onClick={() => setTab('graph')}>Relationships ({graph.nodes.length} nodes)</button>
          <button className={button} disabled={busy} onClick={() => void run(async () => {await memoryApi.rebuild(); await refresh();})}><RefreshCw size={16}/> Rebuild indexes</button>
          <button className={button} disabled={busy} onClick={() => void run(async () => {
            const data = await memoryApi.export(); const url = URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
            const anchor = document.createElement('a'); anchor.href=url; anchor.download='tars-personal-memory.json'; anchor.click(); URL.revokeObjectURL(url);
          })}><Download size={16}/> Export</button>
        </div>
        <p role="alert" className="text-destructive">{error}</p>
        <p role="status" className="text-sm text-muted-foreground">{notice}</p>
        {tab==='graph' ? <div className="overflow-auto"><table className="w-full text-left text-sm"><caption className="text-left py-2">Directed relationships from active, authorized facts</caption><thead><tr><th>Subject</th><th>Relationship →</th><th>Object</th></tr></thead><tbody>{graph.edges.map(edge => <tr key={edge.claim_id} className="border-t border-border"><td className="p-2">{edge.source}</td><td>{edge.relationship}</td><td>{edge.target}</td></tr>)}</tbody></table>{!graph.edges.length && <p>No relationships stored.</p>}</div> : <>
          <form className="flex gap-2" onSubmit={event => {event.preventDefault(); void run(async () => { if (query.trim()) setClaims((await memoryApi.search(query)).claims); else await refresh(); });}}>
            <input className={input} aria-label="Search personal memory" placeholder="Search your memories" value={query} onChange={e=>setQuery(e.target.value)}/><button className={button} disabled={busy}><Search size={16}/><span className="sr-only">Search</span></button>
          </form>
          <form className="grid gap-3 border border-border rounded p-4" onSubmit={event => {event.preventDefault(); void run(async () => {
            if (editing) await memoryApi.correct(editing,form); else await memoryApi.add(form);
            setForm(empty); setEditing(undefined); setDetail(undefined); setNotice('Memory saved.'); await refresh();
          });}}>
            <h3>{editing ? 'Correct memory (preserves supersession history)' : 'Remember a fact or relationship'}</h3>
            <div className="grid sm:grid-cols-3 gap-2">{(['subject','predicate','value'] as const).map(field=><label key={field} className="capitalize text-sm">{field}<input required maxLength={2000} className={input} value={form[field]} onChange={e=>setForm({...form,[field]:e.target.value})} placeholder={{subject:'Me',predicate:'works_on',value:'TARS'}[field]}/></label>)}</div>
            <label className="text-sm flex items-center gap-2"><input type="checkbox" checked={form.cloud_allowed} onChange={e=>setForm({...form,cloud_allowed:e.target.checked})}/> Allow this fact in cloud-model context when cloud routing is enabled</label>
            <p className="text-xs text-muted-foreground">New memories are private to you. Conversational history and backups have separate retention. When cloud routing is enabled, facts without cloud permission are omitted even from local turns that might fall back to cloud.</p>
            <div className="flex gap-2"><button className={button} disabled={busy}>{editing ? 'Save correction' : 'Remember'}</button>{editing && <button type="button" className={button} onClick={()=>{setEditing(undefined);setForm(empty);}}>Cancel edit</button>}</div>
          </form>
          <div className="space-y-2">{claims.map(claim => <article key={claim.id} className="border border-border rounded p-3 space-y-2">
            <p className="break-words"><strong>{claim.subject}</strong> <span className="text-primary">{claim.predicate} →</span> {claim.value}</p>
            <p className="text-xs text-muted-foreground">{claim.verification} · {claim.cloud_allowed ? 'Cloud permitted' : 'Local only'} · source {claim.source_id}</p>
            <div className="flex flex-wrap gap-2"><button className={button} disabled={busy} onClick={()=>void run(async ()=>setDetail(await memoryApi.detail(claim.id)))}>View source</button><button className={button} disabled={busy} aria-label={`Correct ${claim.subject} ${claim.predicate}`} onClick={()=>{setEditing(claim.id);setForm({subject:claim.subject,predicate:claim.predicate,value:claim.value,audiences:claim.audiences,sensitivity:claim.sensitivity,cloud_allowed:claim.cloud_allowed,valid_to:claim.valid_to});}}><Pencil size={16}/></button><button className={button} disabled={busy} aria-label={`Forget ${claim.subject} ${claim.predicate}`} onClick={()=>setPendingForget(claim.id)}><Trash2 size={16}/></button></div>
            {pendingForget===claim.id && <div className="space-y-2"><p>Forget this fact and its correction history? Existing conversation transcripts and previous backups remain until separately removed.</p><button className={button} disabled={busy} onClick={()=>void run(async ()=>{const result=await memoryApi.forget(claim.id);setNotice(result.retention_note);setPendingForget(undefined);setDetail(undefined);await refresh();})}>Forget this memory</button><button className={button} onClick={()=>setPendingForget(undefined)}>Keep memory</button></div>}
          </article>)}{!claims.length && <p className="text-muted-foreground">No matching memories. Add an explicit fact to get started.</p>}</div>
        </>}
        {detail && <section className="border border-border rounded p-3 text-sm break-all"><h3>Memory provenance</h3><p>Source: {detail.source_id} ({detail.source_kind})</p><p>Observed: {detail.created_at}</p><p>State: {detail.state}</p><pre className="whitespace-pre-wrap">{detail.source_content}</pre><button className={button} onClick={()=>setDetail(undefined)}>Close source</button></section>}
      </DialogContent>
    </Dialog>
  </>;
}
