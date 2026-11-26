import { act, renderHook } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { useOfflineVoice } from '../hooks/useOfflineVoice';

it('releases a late microphone grant when the owner presses Stop', async () => {
  let grant!: (stream: MediaStream) => void;
  const permission = new Promise<MediaStream>(resolve => { grant = resolve; });
  const stopTrack = vi.fn();
  const transcript = vi.fn();
  const upload = vi.fn();
  vi.stubGlobal('fetch', upload);
  vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: () => permission } });
  const hook = renderHook(() => useOfflineVoice('test-session', false, transcript));
  try {
    let recording!: Promise<void>;
    act(() => { recording = hook.result.current.record('ta-IN'); });
    expect(hook.result.current.phase).toBe('opening');
    act(() => hook.result.current.stop());
    await act(async () => {
      grant({ getTracks: () => [{ stop: stopTrack }] } as unknown as MediaStream);
      await recording;
    });
    expect(stopTrack).toHaveBeenCalledOnce();
    expect(hook.result.current.phase).toBe('idle');
    expect(upload).not.toHaveBeenCalled();
    expect(transcript).not.toHaveBeenCalled();
  } finally {
    hook.unmount();
    vi.unstubAllGlobals();
  }
});
