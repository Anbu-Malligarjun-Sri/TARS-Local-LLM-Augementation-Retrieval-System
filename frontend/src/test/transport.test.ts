import { describe, it, expect, vi, afterEach } from 'vitest';
import { TarsWebSocket, pairDevice,streamChat } from '../services/tarsApi';

afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });
describe('private transport lifecycle', () => {
  it('does not reconnect after deliberate teardown', () => {
    vi.useFakeTimers();
    let sockets = 0;
    class Socket {
      static OPEN = 1;
      readyState = 1;
      onclose?: () => void;
      constructor() { sockets++; }
      close() { this.onclose?.(); }
    }
    vi.stubGlobal('WebSocket', Socket);
    const transport = new TarsWebSocket(vi.fn(), vi.fn(), vi.fn(), vi.fn());
    transport.connect();
    transport.disconnect();
    vi.runAllTimers();
    expect(sockets).toBe(1);
    expect(transport.isConnected()).toBe(false);
  });
  it('pairs through a credentialed POST without storing the owner token', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal('fetch', fetchMock);
    await pairDevice('owner-test-token');
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/pair'), expect.objectContaining({
      credentials: 'include', method: 'POST', body: JSON.stringify({ token: 'owner-test-token' }),
    }));
  });
  it('decodes split Tamil SSE events, binds IDs and passes the abort signal',async()=>{
    const frame=(type:string,content:string,turn='turn-one')=>'data: '+JSON.stringify({type,content,turn_id:turn,conversation_id:'session-one'})+'\n\n';
    const bytes=new TextEncoder().encode(frame('chunk','wrong','other')+frame('chunk','வணக்கம்')+frame('end',''));
    let offset=0;const cancel=vi.fn().mockResolvedValue(undefined);const reader={read:vi.fn(async()=>{if(offset>=bytes.length)return {done:true};const value=bytes.slice(offset,offset+7);offset+=7;return {done:false,value};}),cancel,releaseLock:vi.fn()};
    const fetchMock=vi.fn().mockResolvedValue({ok:true,body:{getReader:()=>reader}});vi.stubGlobal('fetch',fetchMock);
    const controller=new AbortController();const events=vi.fn();
    await streamChat('Hello','session-one','turn-one',{audience:'owner',playful:false},controller.signal,events);
    expect(events.mock.calls.map(call=>call[0].type)).toEqual(['chunk','end']);
    expect(events.mock.calls[0][0].content).toBe('வணக்கம்');expect(cancel).toHaveBeenCalledOnce();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/chat'),expect.objectContaining({credentials:'include',signal:controller.signal}));
  });
});
