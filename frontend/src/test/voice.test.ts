import { afterEach,describe,it,expect,vi } from 'vitest';
import { Microphone,SentenceSpeaker,VoiceMetrics,localVoices,type RecognitionEvent } from '../services/voice';

afterEach(()=>{vi.unstubAllGlobals();vi.useRealTimers();});
const local={name:'Local English',lang:'en-IN',localService:true,voiceURI:'local'} as SpeechSynthesisVoice;
class Utterance {voice?:SpeechSynthesisVoice;lang='';rate=1;onstart?:()=>void;onend?:()=>void;onerror?:()=>void;constructor(public text:string){}}
describe('speech privacy and lifecycle',()=>{
 it('selects only local voices matching the requested language',()=>{
  vi.stubGlobal('speechSynthesis',{getVoices:()=>[local,{...local,localService:false},{...local,lang:'ta-IN'}]});
  expect(localVoices('en-IN')).toEqual([local]);expect(localVoices('ta-IN')).toHaveLength(1);
 });
 it('streams sentences, suppresses split code fences and cancels late audio callbacks',()=>{
  vi.useFakeTimers();const utterances:Utterance[]=[];const cancel=vi.fn();
  vi.stubGlobal('SpeechSynthesisUtterance',Utterance);vi.stubGlobal('speechSynthesis',{speak:(u:Utterance)=>utterances.push(u),cancel});
  const callbacks={state:vi.fn(),start:vi.fn(),error:vi.fn()};const speaker=new SentenceSpeaker(local,callbacks);
  speaker.add('Hello. This is ');expect(utterances[0].text).toBe('Hello.');utterances[0].onstart?.();
  speaker.add('useful. ``');speaker.add('`python\nsecret = 123\n```\nRead [this](https://example.invalid). ',true);
  utterances[0].onend?.();expect(utterances[1].text).toBe('This is useful.');utterances[1].onend?.();
  expect(utterances.map(u=>u.text).join(' ')).not.toContain('secret');
  speaker.stop();const count=utterances.length;utterances[count-1].onend?.();utterances[count-1].onstart?.();
  expect(utterances).toHaveLength(count);expect(cancel).toHaveBeenCalledOnce();expect(callbacks.start).toHaveBeenCalledOnce();
 });
 it('requires consent, shows interim text, sends one final and never restarts recording',()=>{
  vi.useFakeTimers();const instances:FakeRecognition[]=[];
  class FakeRecognition {
   lang='';continuous=true;interimResults=false;maxAlternatives=1;
   onstart?:()=>void;onend?:()=>void;onspeechend?:()=>void;onresult?:(e:RecognitionEvent)=>void;onerror?:(e:{error:string})=>void;
   start=vi.fn(()=>this.onstart?.());abort=vi.fn();constructor(){instances.push(this);}
  }
  vi.stubGlobal('SpeechRecognition',FakeRecognition);
  const callbacks={state:vi.fn(),partial:vi.fn(),final:vi.fn(),error:vi.fn(),metric:vi.fn()};const mic=new Microphone(callbacks);
  expect(()=>mic.start('ta-IN',false)).toThrow(/disclosure/);mic.start('ta-IN',true);const instance=instances[0];
  expect(instance.lang).toBe('ta-IN');expect(instance.interimResults).toBe(true);
  instance.onresult?.({resultIndex:0,results:{length:1,0:{isFinal:false,length:1,0:{transcript:'வணக்கம்'}}}});
  expect(callbacks.partial).toHaveBeenCalledWith('வணக்கம்');expect(callbacks.final).not.toHaveBeenCalled();
  const stale=instance.onresult;instance.onspeechend?.();stale?.({resultIndex:0,results:{length:1,0:{isFinal:true,length:1,0:{transcript:'வணக்கம் TARS'}}}});
  stale?.({resultIndex:0,results:{length:1,0:{isFinal:true,length:1,0:{transcript:'duplicate'}}}});
  expect(callbacks.final).toHaveBeenCalledExactlyOnceWith('வணக்கம் TARS');expect(instance.abort).toHaveBeenCalledOnce();expect(instance.start).toHaveBeenCalledOnce();
 });
 it('bounds silence capture and handles microphone permission denial',()=>{
  vi.useFakeTimers();let errorHandler:(e:{error:string})=>void;
  class Recognition {start(){errorHandler=this.onerror;}abort=vi.fn();onerror?:(e:{error:string})=>void;}
  vi.stubGlobal('SpeechRecognition',Recognition);const callbacks={state:vi.fn(),partial:vi.fn(),final:vi.fn(),error:vi.fn(),metric:vi.fn()};const mic=new Microphone(callbacks);
  mic.start('en-IN',true);errorHandler({error:'not-allowed'});expect(callbacks.error).toHaveBeenCalledWith(expect.stringContaining('not-allowed'));
  mic.start('en-IN',true);vi.advanceTimersByTime(20000);expect(callbacks.error).toHaveBeenCalledWith(expect.stringContaining('timed out'));expect(callbacks.final).not.toHaveBeenCalled();
 });
 it('reports bounded observed median/p95 samples without invented data',()=>{
  const metrics=new VoiceMetrics();expect(metrics.summary()).toEqual({});for(let i=1;i<=60;i++)metrics.add('latency',i);
  expect(metrics.summary().latency).toEqual({count:50,median_ms:36,p95_ms:58});
 });
});
