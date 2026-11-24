import {useEffect,useRef,useState,useCallback} from 'react';
import {localMedia,mediaJson} from '@/services/localMedia';

export function useOfflineVoice(session:string|null,muted:boolean,onTranscript:(text:string)=>void) {
  const [phase,setPhase]=useState<'idle'|'opening'|'recording'|'processing'|'playing'>('idle');
  const [error,setError]=useState('');
  const generation=useRef(0);
  const resources=useRef<{stream?:MediaStream;recorder?:MediaRecorder;controller?:AbortController;audio?:HTMLAudioElement;url?:string;timer?:ReturnType<typeof setTimeout>}>({});
  const stop=useCallback(()=>{
    generation.current++;
    const r=resources.current;
    clearTimeout(r.timer);
    r.controller?.abort();
    if(r.recorder && r.recorder.state!=='inactive'){r.recorder.onstop=null;r.recorder.stop();}
    r.stream?.getTracks().forEach(t=>t.stop());
    r.audio?.pause();
    if(r.url)URL.revokeObjectURL(r.url);
    resources.current={};
    setPhase('idle');
  },[]);
  useEffect(()=>{stop();return stop;},[session,muted,stop]);
  const record=async(language:string)=>{
    stop();setError('');setPhase('opening');
    const id=generation.current,r=resources.current;
    const fail=(e:unknown)=>{if(id===generation.current){stop();setError(e instanceof Error?e.message:'Recording failed.');}};
    try {
      const stream=await navigator.mediaDevices.getUserMedia({audio:true});
      if(id!==generation.current){stream.getTracks().forEach(t=>t.stop());return;}
      r.stream=stream;
      const recorder=new MediaRecorder(stream);
      const chunks:Blob[]=[];
      r.recorder=recorder;
      recorder.ondataavailable=e=>chunks.push(e.data);
      recorder.onerror=()=>fail(new Error('Local capture failed.'));
      recorder.onstop=async()=>{
        stream.getTracks().forEach(t=>t.stop());
        clearTimeout(r.timer);
        if(id!==generation.current)return;
        setPhase('processing');
        try {
          const bytes=await new Blob(chunks).arrayBuffer();
          const ctx=new OfflineAudioContext(1,1,16000);
          const decoded=await ctx.decodeAudioData(bytes);
          if(id!==generation.current)return;
          const samples=decoded.getChannelData(0).subarray(0,320000);
          const pcm=Int16Array.from(samples,x=>Math.max(-1,Math.min(1,x))*32767);
          r.controller=new AbortController();
          const res=await localMedia('transcribe?language='+ (language==='ta-IN'?'ta':'en'),{method:'POST',body:pcm.buffer,signal:r.controller.signal,headers:{'Content-Type':'application/octet-stream'}});
          const {text}=await res.json();
          if(id===generation.current){stop();if(text)onTranscript(text);else setError('No words recognized.');}
        }catch(e){fail(e);}
      };
      recorder.start();setPhase('recording');
      r.timer=setTimeout(()=>{if(recorder.state==='recording')recorder.stop();},19000);
    }catch(e){fail(e);}
  };
  const speak=async(text:string)=>{
    stop();setError('');if(muted||!text.trim())return;
    const id=generation.current,r=resources.current;
    r.controller=new AbortController();setPhase('processing');
    try {
      const response=await localMedia('speak',{...mediaJson({text:text.slice(0,600)}),signal:r.controller.signal});
      const blob=await response.blob();
      if(id!==generation.current)return;
      r.url=URL.createObjectURL(blob);
      r.audio=new Audio(r.url);
      r.audio.onended=()=>{if(id===generation.current)stop();};
      r.audio.onerror=()=>{if(id===generation.current){stop();setError('Audio playback failed.');}};
      setPhase('playing');await r.audio.play();
    }catch(e){if(id===generation.current){stop();setError(e instanceof Error?e.message:'Speech failed.');}}
  };
  const finish=()=>{const recorder=resources.current.recorder;if(recorder?.state==='recording')recorder.stop();};
  return {phase,error,record,finish,speak,stop};
}
