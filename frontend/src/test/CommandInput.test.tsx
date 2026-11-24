import { afterEach,it,expect,vi } from 'vitest';
import { act,cleanup,fireEvent,render,screen,waitFor } from '@testing-library/react';
import { CommandInput } from '../components/chat/CommandInput';
import * as transport from '../services/tarsApi';
import { useTarsStore } from '../store/tarsStore';

afterEach(()=>{cleanup();vi.restoreAllMocks();vi.unstubAllGlobals();});
it('puts Stop in the send rectangle before the first token and ignores cancelled late text',async()=>{
 useTarsStore.setState({messages:[],sessions:[],currentSessionId:null,status:'idle',isVoiceMode:false});
 vi.spyOn(transport.tarsApi,'getSettings').mockResolvedValue({humor:60,honesty:90,discretion:50});
 vi.spyOn(transport.tarsApi,'getConversations').mockResolvedValue({conversations:[]});
 vi.spyOn(transport.tarsApi,'updateSettings').mockResolvedValue({humor:60,honesty:90,discretion:50});
 const cancel=vi.spyOn(transport,'cancelChatTurn').mockResolvedValue(undefined);
 let events:(event:transport.ChatMessage)=>void;let signal:AbortSignal;
 vi.spyOn(transport,'streamChat').mockImplementation(async(_text,_conversation,_turn,_style,abort,callback)=>{signal=abort;events=callback;await new Promise<void>(()=>undefined);});
 render(<CommandInput/>);
 fireEvent.change(screen.getByRole('textbox',{name:'Message'}),{target:{value:'Please explain this.'}});
 await waitFor(()=>expect(screen.getByRole('button',{name:'Send message'})).toBeEnabled());
 fireEvent.click(screen.getByRole('button',{name:'Send message'}));
 expect(useTarsStore.getState().status).toBe('thinking');
 expect(vi.mocked(transport.streamChat).mock.calls[0][3]).toEqual({audience:'owner',playful:false});
 const stop=screen.getByRole('button',{name:'Stop TARS'});expect(stop.closest('form')).toBeTruthy();
 fireEvent.click(stop);expect(signal.aborted).toBe(true);expect(cancel).toHaveBeenCalledOnce();
 act(()=>events({type:'chunk',content:'UNWANTED LATE OUTPUT'}));
 expect(useTarsStore.getState().messages.map(m=>m.content).join(' ')).not.toContain('UNWANTED');
 expect(useTarsStore.getState().status).toBe('idle');
});

it('shows Tamil/English and requires speech disclosure before microphone start',async()=>{
 vi.spyOn(transport.tarsApi,'getSettings').mockResolvedValue({humor:60,honesty:90,discretion:50});
 vi.spyOn(transport.tarsApi,'getConversations').mockResolvedValue({conversations:[]});
 vi.stubGlobal('SpeechRecognition',class {});
 useTarsStore.setState({messages:[],sessions:[],currentSessionId:null,status:'idle',isVoiceMode:false});
 await act(async()=>{render(<CommandInput/>);});fireEvent.click(screen.getByRole('button',{name:'Voice settings'}));
 expect(screen.getByRole('combobox',{name:'Speech language'})).toHaveValue('ta-IN');
 expect(screen.getByRole('button',{name:'Start microphone'})).toBeDisabled();
 expect(screen.getByText(/Recognition may send microphone audio/)).toBeInTheDocument();
});

it.each([
 ['வணக்கம் TARS','வணக்கம். ','ta-IN'],
 ['ஆங்கிலத்தில் சொல்லு','Here is the answer. ','en-IN'],
])('reviews Tamil dictation "%s" and speaks the reply in its own language',async(transcript,reply,locale)=>{
 useTarsStore.setState({messages:[],sessions:[],currentSessionId:null,status:'idle',isVoiceMode:false,isMuted:false});
 vi.spyOn(transport.tarsApi,'getSettings').mockResolvedValue({humor:60,honesty:90,discretion:50});
 vi.spyOn(transport.tarsApi,'getConversations').mockResolvedValue({conversations:[]});
 vi.spyOn(transport.tarsApi,'getHistory').mockResolvedValue({conversation_id:'new',messages:[],count:0});
 vi.spyOn(transport,'cancelChatTurn').mockResolvedValue(undefined);
 let final:(event:import('../services/voice').RecognitionEvent)=>void;
 class Recognition {onstart?:()=>void;onresult?:typeof final;start(){final=this.onresult;this.onstart?.();}abort=vi.fn();}
 vi.stubGlobal('SpeechRecognition',Recognition);
 const speak=vi.fn(),cancel=vi.fn();vi.stubGlobal('speechSynthesis',{getVoices:()=>[
  {voiceURI:'ta',name:'Tamil local',lang:'ta-IN',localService:true},
  {voiceURI:'en',name:'English local',lang:'en-IN',localService:true},
 ],addEventListener:vi.fn(),removeEventListener:vi.fn(),speak,cancel});
 vi.stubGlobal('SpeechSynthesisUtterance',class{constructor(public text:string){}});
 let events:(event:transport.ChatMessage)=>void;
 const stream=vi.spyOn(transport,'streamChat').mockImplementation(async(_text,_conversation,_turn,_style,_abort,callback)=>{events=callback;await new Promise<void>(()=>undefined);});
 await act(async()=>{render(<CommandInput/>);});
 fireEvent.click(screen.getByRole('button',{name:'Voice settings'}));
 fireEvent.click(screen.getByRole('checkbox',{name:/I consent/}));
 fireEvent.click(screen.getByRole('button',{name:'Start microphone'}));
 act(()=>final({resultIndex:0,results:{length:1,0:{isFinal:true,length:1,0:{transcript}}}}));
 expect(screen.getByRole('textbox',{name:'Message'})).toHaveValue(transcript);expect(stream).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button',{name:'Send message'}));
 await act(async()=>{events({type:'start'});events({type:'chunk',content:reply});});
 expect(speak).toHaveBeenCalledOnce();
 expect(speak.mock.calls[0][0].lang).toBe(locale);
 fireEvent.click(screen.getByRole('button',{name:'Stop TARS'}));
 expect(cancel).toHaveBeenCalled();
 act(()=>events({type:'chunk',content:'Late spoken text. '}));expect(speak).toHaveBeenCalledOnce();
});
