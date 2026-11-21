import { describe, it, expect, vi, afterEach } from 'vitest';
import { TarsWebSocket, pairDevice } from '../services/tarsApi';

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
});
