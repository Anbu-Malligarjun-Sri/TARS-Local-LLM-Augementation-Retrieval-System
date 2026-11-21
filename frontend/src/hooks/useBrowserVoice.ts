import { useCallback,useEffect,useRef,useState } from 'react';
import { Microphone,SentenceSpeaker,VoiceMetrics,localVoices,recognitionConstructor } from '@/services/voice';
import type { ChatMessage } from '@/services/tarsApi';
import { useTarsStore } from '@/store/tarsStore';

export function useBrowserVoice(onFinal:(text:string)=>void){
 const [language,setLanguage]=useState('ta-IN');const [consent,setConsent]=useState(false);const [listening,setListening]=useState(false);const [speaking,setSpeaking]=useState(false);const [partial,setPartial]=useState('');const [error,setError]=useState('');const [voices,setVoices]=useState<SpeechSynthesisVoice[]>([]);const [voiceURI,setVoiceURI]=useState('');const [revision,setRevision]=useState(0);
 const metrics=useRef(new VoiceMetrics());const microphone=useRef<Microphone>();const speaker=useRef<SentenceSpeaker>();const finalRef=useRef(onFinal);finalRef.current=onFinal;const timing=useRef({request:0,firstText:false,firstSpeech:false});
 const currentSession=useTarsStore(state=>state.currentSessionId);const muted=useTarsStore(state=>state.isMuted);
 const record=useCallback((name:string,value:number)=>{metrics.current.add(name,value);setRevision(v=>v+1);},[]);
 const stop=useCallback((measure=true)=>{const start=performance.now();microphone.current?.stop();speaker.current?.stop();speaker.current=undefined;setPartial('');if(measure)record('local_stop_dispatch',performance.now()-start);},[record]);
 useEffect(()=>{
  microphone.current=new Microphone({state:setListening,partial:setPartial,final:text=>{setPartial('');finalRef.current(text);},error:setError,metric:record});
  return()=>{microphone.current?.stop();speaker.current?.stop();};
 },[record]);
 useEffect(()=>{const update=()=>setVoices(localVoices(language));update();window.speechSynthesis?.addEventListener('voiceschanged',update);return()=>window.speechSynthesis?.removeEventListener('voiceschanged',update);},[language]);
 useEffect(()=>{stop(false);},[currentSession,muted,language,consent,stop]);
 const beginReply=(requestAt=performance.now())=>{
  speaker.current?.stop();setError('');timing.current={request:requestAt,firstText:false,firstSpeech:false};
  if(useTarsStore.getState().isMuted)return;
  const voice=voices.find(v=>v.voiceURI===voiceURI) || voices.find(v=>v.lang===language) || voices[0];
  if(!voice){setError('No local speech voice for this language. The answer will appear as text.');return;}
  speaker.current=new SentenceSpeaker(voice,{state:setSpeaking,start:()=>{if(!timing.current.firstSpeech){timing.current.firstSpeech=true;record('request_to_first_speech',performance.now()-timing.current.request);}},error:setError});
 };
 const onEvent=(event:ChatMessage)=>{
  if(event.type==='chunk'){
   if(!timing.current.firstText){timing.current.firstText=true;record('request_to_first_text',performance.now()-timing.current.request);}
   if(!useTarsStore.getState().isMuted)speaker.current?.add(event.content || '');
  }else if(event.type==='end')speaker.current?.add('',true);
  else if(event.type==='cancelled' || event.type==='error')speaker.current?.stop();
 };
 const listen=()=>{setError('');speaker.current?.stop();setPartial('');try{microphone.current?.start(language,consent);}catch(e){setError(e instanceof Error?e.message:'Could not start microphone.');}};
 return {language,setLanguage,consent,setConsent,listening,speaking,partial,error,voices,voiceURI,setVoiceURI,listen,stop,beginReply,onEvent,supported:!!recognitionConstructor(),metrics:metrics.current.summary(),revision};
}
