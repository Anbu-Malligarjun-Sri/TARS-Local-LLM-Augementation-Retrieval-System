import { useState,useRef,useEffect } from 'react';
import { Send,Mic,Square } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTarsStore } from '@/store/tarsStore';
import { useTarsChat } from '@/hooks/useTarsChat';
import { useBrowserVoice } from '@/hooks/useBrowserVoice';
import { tarsApi,type ChatStyle,type ChatMessage } from '@/services/tarsApi';

export function CommandInput(){
 const [input,setInput]=useState('');const [autoSend,setAutoSend]=useState(false);
 const [style,setStyle]=useState<ChatStyle>({audience:'owner',playful:false});
 const styleBySession=useRef(new Map<string,ChatStyle>());const dictated=useRef(false);const voiceEvents=useRef<(event:ChatMessage)=>void>();
 const {status,currentSessionId,isVoiceMode:showVoice,toggleVoiceMode}=useTarsStore();
 const chat=useTarsChat(event=>voiceEvents.current?.(event));
 const submitRef=useRef<(text:string)=>void>();
 const voice=useBrowserVoice(text=>{dictated.current=true;setInput(text);if(autoSend)submitRef.current?.(text);});
 const audioTurn=useRef(false);const requestStart=useRef(0);
 voiceEvents.current=event=>{if(audioTurn.current){if(event.type==='start')voice.beginReply(requestStart.current);voice.onEvent(event);}};
 const busy=status==='thinking' || status==='speaking';
 const processing=busy || voice.listening || voice.speaking;
 const submit=(text:string)=>{
  if(!text.trim() || busy)return;
  if(voice.speaking)voice.stop();
  audioTurn.current=dictated.current;
  requestStart.current=performance.now();
  if(chat.sendMessage(text,{...style,language:voice.language as 'en-IN'|'ta-IN'})){setInput('');dictated.current=false;}else voice.stop();
 };
 submitRef.current=submit;
 const stop=()=>{voice.stop();audioTurn.current=false;void chat.cancelTurn();};
 const chooseAudience=(audience:ChatStyle['audience'])=>{
  stop();useTarsStore.getState().createNewSession(audience==='owner'?'Owner conversation':`${audience} style preview`);
  const next={audience,playful:false};styleBySession.current.set(useTarsStore.getState().currentSessionId!,next);setStyle(next);setInput('');
 };
 useEffect(()=>{
  let mounted=true;
  setStyle(styleBySession.current.get(currentSessionId || '') || {audience:'owner',playful:false});setInput('');dictated.current=false;
  if(currentSessionId && !styleBySession.current.has(currentSessionId)){
   tarsApi.getHistory(currentSessionId).then(history=>{if(mounted && history.audience){const restored={audience:history.audience,playful:false};styleBySession.current.set(currentSessionId,restored);setStyle(restored);}}).catch(()=>undefined);
  }
  return()=>{mounted=false;};
 },[currentSessionId]);
 return <div className="space-y-2">
  <div className="flex flex-wrap gap-3 items-center text-xs text-muted-foreground">
   <label>Audience style <select aria-label="Audience style" className="bg-background border border-border rounded p-1" value={style.audience} disabled={processing} onChange={e=>chooseAudience(e.target.value as ChatStyle['audience'])}>
    <option value="owner">Owner</option><option value="parent">Parent preview</option><option value="friend">Friend preview</option><option value="professional">Professional preview</option><option value="unknown">Unknown preview</option>
   </select></label>
   {style.audience==='friend' && <label><input type="checkbox" checked={style.playful} disabled={processing} onChange={e=>{const next={...style,playful:e.target.checked};setStyle(next);if(currentSessionId)styleBySession.current.set(currentSessionId,next);}}/>Allow playful sarcasm</label>}
   {style.audience!=='owner' && <span>Separate preview: no owner memories or tools.</span>}
  </div>
  <form onSubmit={e=>{e.preventDefault();submit(input);}}>
   <div className="flex items-center gap-2 p-3 bg-tars-dark border border-border rounded focus-within:border-tars-amber/50">
    <span className="font-terminal text-tars-amber">&gt;</span>
    <input aria-label="Message" maxLength={4000} value={input} onChange={e=>setInput(e.target.value)} placeholder={voice.listening?'Listening…':'Enter command…'} disabled={voice.listening} className="flex-1 min-w-0 bg-transparent outline-none font-terminal text-sm"/>
    <button type="button" aria-label="Voice settings" aria-expanded={showVoice} onClick={()=>{if(showVoice)stop();toggleVoiceMode();}} className="p-2 rounded hover:bg-secondary"><Mic className="w-4 h-4"/></button>
    {processing?<button type="button" aria-label="Stop TARS" title="Stop generation, microphone and speech" onClick={stop} className="flex items-center gap-2 px-3 py-2 rounded bg-tars-amber text-tars-black font-terminal text-xs"><Square className="w-4 h-4" fill="currentColor"/>STOP</button>:
    <button type="submit" aria-label="Send message" disabled={!input.trim() || !chat.settingsReady} className={cn('px-3 py-2 rounded',input.trim() && chat.settingsReady?'bg-tars-amber text-tars-black':'bg-secondary text-muted-foreground')}><Send className="w-4 h-4"/></button>}
   </div>
  </form>
  {(chat.error || voice.error) && <p role="alert" className="text-xs text-destructive">{chat.error || voice.error}</p>}
  {showVoice && <section aria-label="Browser voice" className="border border-border rounded p-3 space-y-3 text-xs">
   <p>Browser voice: Tamil / English. Recognition may send microphone audio to your browser’s speech provider, even when the LLM is local. TARS stores the sent transcript as chat, not raw audio. Playback uses local voices.</p>
   <label className="flex gap-2"><input type="checkbox" checked={voice.consent} onChange={e=>voice.setConsent(e.target.checked)}/>I consent to browser-provider speech recognition for this session.</label>
   <div className="flex flex-wrap gap-3">
    <label>Speech language <select aria-label="Speech language" value={voice.language} onChange={e=>voice.setLanguage(e.target.value)} className="bg-background border rounded p-1"><option value="ta-IN">Tamil (India)</option><option value="en-IN">English (India)</option></select></label>
    <label>Local voice <select aria-label="Local voice" value={voice.voiceURI} onChange={e=>voice.setVoiceURI(e.target.value)} className="bg-background border rounded p-1"><option value="">Automatic local voice</option>{voice.voices.map(v=><option key={v.voiceURI} value={v.voiceURI}>{v.name} ({v.lang})</option>)}</select></label>
   </div>
   <p>Choose the main language for each turn. Mixed Tamil/English accuracy depends on the speech service. Speak once, review the transcript, then Send. Recording stops before playback to avoid echo.</p>
   <label className="flex gap-2"><input type="checkbox" checked={autoSend} onChange={e=>setAutoSend(e.target.checked)}/>Send final transcript automatically</label>
   <button type="button" disabled={!voice.consent || !voice.supported || !chat.settingsReady} onClick={()=>{stop();voice.listen();}} className="border rounded px-3 py-2 disabled:opacity-50">{busy || voice.speaking?'Interrupt and listen':'Start microphone'}</button>
   <button type="button" onClick={stop} className="border rounded px-3 py-2 ml-2">Stop voice</button>
   <p role="status">{voice.listening?'Microphone listening (20-second limit)':voice.speaking?'Playing local speech':'Microphone off'}{!voice.supported?' · Recognition unsupported here; use text.':''}</p>
   {voice.partial && <p aria-live="polite">Partial transcript: {voice.partial}</p>}
   {!voice.voices.length && <p>No local voice for this language is currently available; replies remain text.</p>}
   <details><summary>Measured timings (this page only)</summary><p>Milliseconds; median / p95 across up to 50 samples. Stop timing measures local API dispatch, not acoustic silence or provider shutdown.</p><pre>{JSON.stringify(voice.metrics,null,2)}</pre></details>
  </section>}
 </div>;
}
