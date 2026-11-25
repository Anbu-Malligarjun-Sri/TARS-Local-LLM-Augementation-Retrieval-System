import { useMemo, useRef, useState } from 'react';
import type { MemoryGraph } from '@/services/memoryApi';

export function MemoryNetwork({graph, inspect}: {graph:MemoryGraph; inspect:(id:string)=>void}) {
  const [focus,setFocus] = useState('');
  const drag=useRef<{x:number;y:number;left:number;top:number}>();
  const [zoom,setZoom] = useState(1);
  const [query,setQuery] = useState('');
  const {points,edges,center} = useMemo(() => {
    const neighbors = new Map(graph.nodes.map(name=>[name,new Set<string>()]));
    for (const e of graph.edges) {
      neighbors.get(e.source)?.add(e.target);
      neighbors.get(e.target)?.add(e.source);
    }
    const names = [...graph.nodes].sort((a,b)=>neighbors.get(b)!.size-neighbors.get(a)!.size);
    const center = neighbors.has(focus) ? focus : names[0];
    const ordered = [...new Set([center,...(neighbors.get(center) || []),...names])].slice(0,61);
    const points = new Map<string,{x:number;y:number}>();
    ordered.forEach((name,i)=>{
      const ring = Math.ceil(i/12);
      const angle = 2*Math.PI*((i-1)%12)/Math.min(12,ordered.length-1-(ring-1)*12);
      points.set(name,i===0 ? {x:0,y:0} : {x:Math.cos(angle)*ring*160,y:Math.sin(angle)*ring*115});
    });
    return {points,center,edges:graph.edges.filter(e=>points.has(e.source) && points.has(e.target))};
  },[graph,focus]);
  if (!graph.nodes.length) return <p>As you share facts, their connections will appear here.</p>;
  const size = Math.max(1,Math.ceil((points.size-1)/12));
  const width=size*330+170, height=size*240+75;
  return <section aria-label="Interactive memory graph" className="space-y-2">
    <div className="flex flex-wrap gap-2 items-center">
      <input aria-label="Find a memory node" className="bg-background border rounded px-2" placeholder="Find a node…" value={query} onChange={e=>setQuery(e.target.value)}/>
      <button onClick={()=>setZoom(z=>Math.min(4,z+.5))} aria-label="Zoom in">＋</button>
      <button onClick={()=>setZoom(z=>Math.max(1,z-.5))} aria-label="Zoom out">−</button>
      <span className="text-xs">{Math.round(zoom*100)}% · {points.size} of {graph.nodes.length} nodes</span>
    </div>
    {query && <div className="flex gap-2 flex-wrap">{graph.nodes.filter(n=>n.toLowerCase().includes(query.toLowerCase())).slice(0,20).map(n=><button key={n} className="underline" onClick={()=>{setFocus(n);setQuery('');}}>{n}</button>)}</div>}
    <div className="overflow-auto overscroll-contain border rounded bg-background" style={{height:310}}
      onPointerDown={e=>{
        if(e.button!==0 || e.pointerType!=='mouse' || (e.target as Element).closest('[role=button]'))return;
        const pane=e.currentTarget;
        drag.current={x:e.clientX,y:e.clientY,left:pane.scrollLeft,top:pane.scrollTop};
        pane.setPointerCapture(e.pointerId);
      }} onPointerMove={e=>{if(drag.current){
        e.currentTarget.scrollLeft=drag.current.left+drag.current.x-e.clientX;
        e.currentTarget.scrollTop=drag.current.top+drag.current.y-e.clientY;
      }}} onLostPointerCapture={()=>{drag.current=undefined;}}>
      <svg role="group" aria-label="Memory connections" viewBox={[-width/2,-height/2,width,height].join(' ')} style={{width:zoom*100+'%',height:zoom*100+'%'}}>
        {edges.map(e=><line key={e.claim_id} x1={points.get(e.source)!.x} y1={points.get(e.source)!.y} x2={points.get(e.target)!.x} y2={points.get(e.target)!.y} stroke="currentColor" opacity={e.source===center || e.target===center ? .65:.2}><title>{e.relationship}</title></line>)}
        {[...points].map(([name,p])=><g key={name} role="button" tabIndex={0} aria-label={'Focus '+name} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setFocus(name);}}} onClick={()=>setFocus(name)} transform={`translate(${p.x} ${p.y})`} className="cursor-pointer">
          <title>{name}</title><rect x={-42} y={-14} width={84} height={48} fill="transparent"/><circle r={name===center?12:8} fill={name===center?'#efa951':'#72afb7'}/>
          <text textAnchor="middle" y={28} fontSize={14} fill="currentColor">{name.length>20?name.slice(0,19)+'…':name}</text>
        </g>)}
      </svg>
    </div>
    <strong className="break-words">{center}</strong>
    <ul>{edges.filter(e=>e.source===center||e.target===center).map(e=><li key={e.claim_id}><button className="text-left underline break-words" onClick={()=>inspect(e.claim_id)}>{e.source} → {e.relationship} → {e.target}</button></li>)}</ul>
  </section>;
}
