import { useEffect,useRef,useCallback,useState } from 'react';
import { tarsApi,streamChat,cancelChatTurn,type ChatMessage,type ChatStyle } from '@/services/tarsApi';
import { useTarsStore } from '@/store/tarsStore';

export function useTarsChat(onEvent?:(event:ChatMessage)=>void){
 const [settingsReady,setSettingsReady]=useState(false);const [error,setError]=useState('');
 const callback=useRef(onEvent);callback.current=onEvent;
 const active=useRef<{id:string;conversation:string;messageId:string;text:string;controller:AbortController}>();
 const savedSettings=useRef('');
 const {humor,honesty,discretion,status}=useTarsStore();
 const cancelTurn=useCallback(async()=>{
  const turn=active.current;if(!turn)return;
  active.current=undefined;turn.controller.abort();
  const state=useTarsStore.getState();
  if(state.currentSessionId===turn.conversation){state.updateMessage(turn.messageId,turn.text || 'Stopped.',false);state.setStatus('idle');}
  try{await cancelChatTurn(turn.id);}catch(e){setError(e instanceof Error?e.message:'Cancellation failed.');}
 },[]);
 useEffect(()=>{
  let mounted=true;
  tarsApi.getSettings().then(settings=>{
   if(!mounted)return;
   savedSettings.current=JSON.stringify({humor:settings.humor,honesty:settings.honesty,discretion:settings.discretion});
   useTarsStore.setState({humor:settings.humor,honesty:settings.honesty,discretion:settings.discretion,isConnected:true});setSettingsReady(true);
   tarsApi.getConversations().then(({conversations})=>{
    if(!mounted)return;const state=useTarsStore.getState();
    const merged=conversations.filter(c=>c.message_count>0).map(c=>state.sessions.find(session=>session.id===c.id) || {id:c.id,name:c.legacy_id || 'Conversation',messages:[],createdAt:new Date(c.created_at),updatedAt:new Date(c.created_at)});
    useTarsStore.setState({sessions:[...merged,...state.sessions.filter(session=>!merged.some(item=>item.id===session.id))]});
    if(state.currentSessionId && state.status==='idle')useTarsStore.getState().loadSession(state.currentSessionId);
   }).catch(()=>undefined);
  }).catch(()=>{if(mounted)setError('Backend unavailable. Pair this device or check the local server.');});
  const unsubscribe=useTarsStore.subscribe((state,previous)=>{if(state.currentSessionId!==previous.currentSessionId && active.current){void cancelTurn();state.setStatus('idle');}});
  return()=>{mounted=false;unsubscribe();const turn=active.current;active.current=undefined;if(turn){turn.controller.abort();void cancelChatTurn(turn.id).catch(()=>undefined);}};
 },[cancelTurn]);
 useEffect(()=>{
  const value=JSON.stringify({humor,honesty,discretion});
  if(!settingsReady || status!=='idle' || value===savedSettings.current)return;
  const timer=setTimeout(()=>{tarsApi.updateSettings({humor,honesty,discretion}).then(()=>{savedSettings.current=value;}).catch(()=>setError('Personality changes were not saved. Wait for processing to finish and adjust again.'));},500);
  return()=>clearTimeout(timer);
 },[humor,honesty,discretion,settingsReady,status]);
 const sendMessage=useCallback((content:string,style:ChatStyle={audience:'owner',playful:false})=>{
  const state=useTarsStore.getState();if(!settingsReady || !content.trim() || active.current || state.status!=='idle')return false;
  const conversation=state.ensureCurrentSession();const id=crypto.randomUUID();const controller=new AbortController();setError('');
  state.addMessage({role:'user',content:content.trim()});state.addMessage({role:'tars',content:'',isStreaming:true});
  const messageId=useTarsStore.getState().messages[useTarsStore.getState().messages.length-1].id;
  const turn={id,conversation,messageId,text:'',controller};active.current=turn;state.setStatus('thinking');
  void streamChat(content.trim(),conversation,id,style,controller.signal,event=>{
   if(active.current!==turn || useTarsStore.getState().currentSessionId!==conversation)return;
   const current=useTarsStore.getState();
   if(event.type==='chunk'){turn.text+=event.content || '';current.updateMessage(messageId,turn.text,true);current.setStatus('speaking');}
   if(event.type==='end' || event.type==='cancelled' || event.type==='error'){
    current.updateMessage(messageId,event.type==='end'?(event.full_response || turn.text):(turn.text || event.content || 'Stopped.'),false);
    if(event.type==='error')setError(event.content || 'Generation failed.');
    active.current=undefined;current.setStatus('idle');
   }
   callback.current?.(event);
  }).catch(e=>{
   if(active.current!==turn)return;active.current=undefined;
   const current=useTarsStore.getState();current.updateMessage(messageId,turn.text || 'Response interrupted. You can retry.',false);current.setStatus('idle');
   setError(e instanceof Error?e.message:'Connection failed.');callback.current?.({type:'error'});
  });
  return true;
 },[settingsReady]);
 const clearChat=useCallback(async()=>{await cancelTurn();const state=useTarsStore.getState();await tarsApi.clearHistory(state.currentSessionId || undefined);state.clearMessages();},[cancelTurn]);
 return {sendMessage,cancelTurn,clearChat,error,settingsReady,isConnected:useTarsStore(state=>state.isConnected)};
}
