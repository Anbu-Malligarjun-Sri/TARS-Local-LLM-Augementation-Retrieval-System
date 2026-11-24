/** Browser speech adapters. No remote voice fallback or implicit microphone start. */
export interface RecognitionResult {isFinal:boolean;length:number;[index:number]:{transcript:string}}
export interface RecognitionEvent {resultIndex:number;results:{length:number;[index:number]:RecognitionResult}}
export interface Recognition {
 lang:string;continuous:boolean;interimResults:boolean;maxAlternatives:number;
 onstart:(()=>void)|null;onend:(()=>void)|null;onspeechend:(()=>void)|null;
 onresult:((event:RecognitionEvent)=>void)|null;onerror:((event:{error:string})=>void)|null;
 start():void;abort():void;
}
type SpeechWindow=Window & {SpeechRecognition?:new()=>Recognition;webkitSpeechRecognition?:new()=>Recognition};
export function recognitionConstructor(){const w=window as SpeechWindow;return w.SpeechRecognition || w.webkitSpeechRecognition;}
export function localVoices(language:string){return (window.speechSynthesis?.getVoices() || []).filter(v=>v.localService && v.lang.split('-')[0]===language.split('-')[0]);}

export function replyVoice(text:string, preferredURI:string, fallbackLanguage:string){
 const tamil=text.match(/[\u0B80-\u0BFF]+/g)?.length || 0;
 const english=text.match(/[a-z]+/gi)?.length || 0;
 const locale=tamil && tamil>=english?'ta-IN':english?'en-IN':fallbackLanguage;
 const candidates=localVoices(locale);
 return candidates.find(v=>v.voiceURI===preferredURI) || candidates.find(v=>v.lang===locale) || candidates[0];
}

export class VoiceMetrics {
 private samples:Record<string,number[]>={};
 add(name:string,value:number){if(Number.isFinite(value)&&value>=0)this.samples[name]=[...(this.samples[name] || []),Math.round(value)].slice(-50);}
 summary(){return Object.fromEntries(Object.entries(this.samples).map(([name,values])=>{const sorted=[...values].sort((a,b)=>a-b);return [name,{count:values.length,median_ms:sorted[Math.floor(sorted.length/2)],p95_ms:sorted[Math.min(sorted.length-1,Math.ceil(sorted.length*.95)-1)]}];}));}
}

export class Microphone {
 private recognition?:Recognition;private timer?:ReturnType<typeof setTimeout>;private generation=0;
 constructor(private callbacks:{state:(listening:boolean)=>void;partial:(text:string)=>void;final:(text:string)=>void;error:(message:string)=>void;metric:(name:string,ms:number)=>void}){}
 start(language:string,consent:boolean){
  this.stop();
  if(!consent)throw new Error('Approve the browser speech-service disclosure first.');
  const Constructor=recognitionConstructor();if(!Constructor)throw new Error('Speech recognition is unavailable in this browser. Use text input.');
  const recognition=new Constructor();this.recognition=recognition;const generation=++this.generation;let sent=false;let speechEnd:number|undefined;
  const current=()=>generation===this.generation;
  recognition.lang=language;recognition.continuous=false;recognition.interimResults=true;recognition.maxAlternatives=1;
  recognition.onstart=()=>{if(current())this.callbacks.state(true);};
  recognition.onspeechend=()=>{speechEnd=performance.now();};
  recognition.onresult=event=>{
   if(!current() || sent)return;
   let interim='',final='';
   for(let i=0;i<event.results.length;i++){const result=event.results[i];if(result.isFinal)final+=result[0].transcript;else interim+=result[0].transcript;}
   this.callbacks.partial((final+interim).slice(0,4000));
   if(final.trim()){
    sent=true;if(speechEnd!==undefined)this.callbacks.metric('speech_end_to_final',performance.now()-speechEnd);
    this.stop();this.callbacks.final(final.trim().slice(0,4000));
   }
  };
  recognition.onerror=event=>{if(current()){this.stop();this.callbacks.error(`Speech recognition: ${event.error}. Text input is still available.`);}};
  recognition.onend=()=>{if(current()){this.stop();if(!sent)this.callbacks.error('No final speech transcript received. Try again or type your message.');}};
  this.timer=setTimeout(()=>{if(current()){this.stop();this.callbacks.error('Microphone timed out after 20 seconds. Try again or use text.');}},20000);
  try{recognition.start();}catch(error){this.stop();throw error;}
 }
 stop(){this.generation++;clearTimeout(this.timer);if(this.recognition){const r=this.recognition;this.recognition=undefined;r.onstart=r.onresult=r.onerror=r.onend=r.onspeechend=null;r.abort();}this.callbacks.state(false);}
}

export function spokenText(text:string){return text.replace(/\[([^\]]+)\]\([^)]*\)/g,'$1').replace(/https?:\/\/\S+/g,'').replace(/`[^`]*`/g,'').replace(/<[^>]*>/g,'').replace(/[*_#>|]/g,'').trim();}

/** One utterance at a time; callbacks from cancelled generations are ignored. */
export class SentenceSpeaker {
 private pending='';private code=false;private queue:string[]=[];private active=false;private generation=0;private total=0;private halted=false;private watchdog?:ReturnType<typeof setTimeout>;
 constructor(private selectVoice:(text:string)=>SpeechSynthesisVoice|undefined,private callbacks:{state:(speaking:boolean)=>void;start:()=>void;error:(message:string)=>void}){}
 add(chunk:string,final=false){
  if(this.halted)return;
  this.pending+=chunk;
  while(this.pending){
   const fence=this.pending.indexOf('```');
   if(this.code){if(fence<0){this.pending=final?'':this.pending.slice(-2);break;}this.pending=this.pending.slice(fence+3);this.code=false;continue;}
   const match=/[.!?](?=\s)|\n/.exec(this.pending);const boundary=match?match.index+1:-1;
   if(fence>=0 && (boundary<0 || fence<boundary)){this.enqueue(this.pending.slice(0,fence));this.pending=this.pending.slice(fence+3);this.code=true;continue;}
   if(boundary>0){this.enqueue(this.pending.slice(0,boundary));this.pending=this.pending.slice(boundary);continue;}
   if(final){this.enqueue(this.pending);this.pending='';break;}
   if(this.pending.length>400){const split=this.pending.lastIndexOf(' ',350);if(split>0){this.enqueue(this.pending.slice(0,split));this.pending=this.pending.slice(split);continue;}}
   break;
  }
  this.pump();
 }
 private enqueue(raw:string){const text=spokenText(raw);if(!text)return;this.total+=text.length;if(this.total>12000 || this.queue.length>=32){this.stop();this.halted=true;this.callbacks.error('Voice playback limit reached; read the remaining text.');return;}this.queue.push(text);}
 private pump(){
  if(this.active || !this.queue.length)return;
  const text=this.queue.shift()!;
  const voice=this.selectVoice(text);
  if(!voice){
   this.stop();this.halted=true;
   this.callbacks.error('No local voice for the reply language. Read the text response.');
   return;
  }
  const generation=this.generation;const utterance=new SpeechSynthesisUtterance(text);utterance.voice=voice;utterance.lang=voice.lang;utterance.rate=1;
  this.active=true;
  utterance.onstart=()=>{if(generation===this.generation){this.callbacks.state(true);this.callbacks.start();}};
  const finish=()=>{if(generation!==this.generation)return;clearTimeout(this.watchdog);this.active=false;this.callbacks.state(false);this.pump();};
  utterance.onend=finish;utterance.onerror=()=>{if(generation===this.generation){this.stop();this.callbacks.error('Speech playback failed. Read the text response.');}};
  this.watchdog=setTimeout(()=>{if(generation===this.generation){this.stop();this.callbacks.error('Speech playback timed out. Read the text response.');}},30000);
  window.speechSynthesis.speak(utterance);
 }
 stop(){this.generation++;this.queue=[];this.pending='';this.code=false;this.total=0;this.active=false;clearTimeout(this.watchdog);window.speechSynthesis?.cancel();this.callbacks.state(false);}
}
