import {useEffect,useRef,useState} from 'react';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from '@/components/ui/dialog';
import {localMedia,mediaJson} from '@/services/localMedia';

type Profile={id:string;name:string};

function Capture() {
  const [profiles,setProfiles]=useState<Profile[]>([]);
  const [name,setName]=useState('');
  const [consent,setConsent]=useState(false);
  const [ready,setReady]=useState(false);
  const [busy,setBusy]=useState(false);
  const [notice,setNotice]=useState('');
  const [removing,setRemoving]=useState('');
  const video=useRef<HTMLVideoElement>(null);
  const stream=useRef<MediaStream>();
  const generation=useRef(0);
  const active=useRef(true);
  const cameraOff=()=>{
    generation.current++;
    stream.current?.getTracks().forEach(track=>track.stop());
    stream.current=undefined;
    if(video.current)video.current.srcObject=null;
    setReady(false);
  };
  const refresh=async()=>{const list=await (await localMedia('faces')).json();if(active.current)setProfiles(list);};
  const run=async(action:()=>Promise<void>)=>{
    setBusy(true);setNotice('');
    try {await action();} catch(e){if(active.current)setNotice(e instanceof Error?e.message:'Face operation failed.');}
    finally {if(active.current)setBusy(false);}
  };
  useEffect(()=>{
    active.current=true;
    void refresh().catch(()=>{if(active.current)setNotice('Could not read face profiles.');});
    return ()=>{active.current=false;generation.current++;stream.current?.getTracks().forEach(track=>track.stop());};
  },[]);
  const preview=async()=>{
    cameraOff();
    const id=generation.current;
    const media=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});
    if(id!==generation.current || !video.current){media.getTracks().forEach(track=>track.stop());return;}
    stream.current=media;video.current.srcObject=media;
    try {await video.current.play();if(id===generation.current)setReady(true);} catch(e){cameraOff();throw e;}
  };
  const capture=async(enroll:boolean)=>{
    const source=video.current;
    if(!source?.videoWidth || !ready || !consent)return;
    const canvas=document.createElement('canvas');canvas.width=canvas.height=192;
    const ctx=canvas.getContext('2d');
    if(!ctx)throw new Error('Canvas unavailable.');
    const side=Math.min(source.videoWidth,source.videoHeight);
    ctx.drawImage(source,(source.videoWidth-side)/2,(source.videoHeight-side)/2,side,side,0,0,192,192);
    cameraOff();setConsent(false);
    const pixels=ctx.getImageData(0,0,192,192).data;
    let binary='';
    for(let i=0;i<pixels.length;i+=4)binary+=String.fromCharCode(pixels[i],pixels[i+1],pixels[i+2]);
    const body={rgb:btoa(binary),consent:true,...(enroll?{name:name.trim()}:{})};
    const result=await (await localMedia('faces/'+(enroll?'enroll':'match'),mediaJson(body))).json();
    if(!active.current)return;
    setNotice(enroll?'Profile enrolled.':result.name?'Possible match: '+result.name:'No clear match.');
    if(enroll){setName('');await refresh();}
  };
  return <div className="space-y-3 text-sm">
    <video ref={video} playsInline muted className={ready?'w-48 aspect-square object-cover rounded':'w-0 h-0'} aria-label="Local camera preview"/>
    <label className="block"><input type="checkbox" checked={consent} onChange={e=>{setConsent(e.target.checked);if(!e.target.checked)cameraOff();}}/> The person in this frame agrees to this check and, if enrolling, storage of their face template.</label>
    <button disabled={!consent || ready || busy} onClick={()=>void run(preview)}>Open camera preview</button>
    {ready && <button className="ml-4" onClick={cameraOff}>Close camera</button>}
    <label className="block">Profile name <input maxLength={60} value={name} onChange={e=>setName(e.target.value)} className="border bg-background rounded px-2"/></label>
    <div className="flex gap-4"><button disabled={!consent || !ready || !name.trim() || busy} onClick={()=>void run(()=>capture(true))}>Enroll this person</button>
      <button disabled={!consent || !ready || !profiles.length || busy} onClick={()=>void run(()=>capture(false))}>Check for a match</button></div>
    <ul>{profiles.map(p=><li key={p.id} className="flex justify-between"><span>{p.name}</span>
      <button disabled={busy} onClick={()=>{if(removing!==p.id){setRemoving(p.id);return;}void run(async()=>{await localMedia('faces/'+p.id,{method:'DELETE'});setRemoving('');await refresh();});}}>{removing===p.id?'Confirm removal':'Remove'}</button></li>)}</ul>
    <p role="status">{notice}</p>
  </div>;
}

export function FaceProfiles() {
  const [open,setOpen]=useState(false);
  return <><button className="w-full border rounded px-3 py-2 text-left" onClick={()=>setOpen(true)}>Face profiles</button>
    <Dialog open={open} onOpenChange={setOpen}><DialogContent><DialogTitle>Face profiles</DialogTitle>
      <DialogDescription>Check one consenting person at a time. Each capture sends one frame to your paired server. It keeps a local face template for enrolled people. A match is a suggestion and grants no account access.</DialogDescription>
      {open && <Capture/>}
    </DialogContent></Dialog></>;
}
