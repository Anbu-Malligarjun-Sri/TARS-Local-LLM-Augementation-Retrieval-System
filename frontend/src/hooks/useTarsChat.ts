/**
 * useTarsChat Hook
 * Manages WebSocket connection to TARS backend and handles chat interactions
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { TarsWebSocket, ChatMessage, tarsApi } from '@/services/tarsApi';
import { useTarsStore } from '@/store/tarsStore';

export function useTarsChat() {
  const wsRef = useRef<TarsWebSocket | null>(null);
  const activeTurn = useRef<string | undefined>();
  const [settingsReady, setSettingsReady] = useState(false);
  const streamingContentRef = useRef<string>('');
  
  const {
    addMessage,
    updateLastMessage,
    setStatus,
    setConnected,
    humor,
    honesty,
    discretion,
  } = useTarsStore();

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((msg: ChatMessage) => {
    if (msg.conversation_id && msg.conversation_id !== useTarsStore.getState().currentSessionId) return;
    if (msg.type === 'start') activeTurn.current = msg.turn_id;
    if (msg.turn_id && activeTurn.current && msg.turn_id !== activeTurn.current) return;
    switch (msg.type) {
      case 'greeting':
        addMessage({
          role: 'tars',
          content: msg.content || 'Connection established.',
        });
        setStatus('idle');
        break;

      case 'start':
        // Start streaming - add empty message
        streamingContentRef.current = '';
        addMessage({
          role: 'tars',
          content: '',
          isStreaming: true,
        });
        setStatus('speaking');
        break;

      case 'chunk':
        // Append chunk to streaming content
        streamingContentRef.current += msg.content || '';
        updateLastMessage(streamingContentRef.current, true);
        break;

      case 'end':
        // End streaming
        updateLastMessage(msg.full_response || streamingContentRef.current, false);
        streamingContentRef.current = '';
        setStatus('idle');
        break;

      case 'error':
      case 'cancelled':
        updateLastMessage(streamingContentRef.current || msg.content || 'Cancelled', false);
        setStatus('idle');
        break;
      case 'response':
        // Non-streaming response
        addMessage({
          role: 'tars',
          content: msg.content || '',
        });
        setStatus('idle');
        break;
    }
  }, [addMessage, updateLastMessage, setStatus]);

  // Initialize WebSocket connection
  useEffect(() => {
    wsRef.current = new TarsWebSocket(
      handleMessage,
      () => setConnected(true),
      () => { setConnected(false); setStatus('idle'); },
      (error) => console.error('WebSocket error:', error)
    );

    wsRef.current.connect();

    return () => {
      wsRef.current?.disconnect();
    };
  }, [handleMessage, setConnected, setStatus]);

  useEffect(() => {
    tarsApi.getSettings().then(settings => {
      useTarsStore.setState({ humor: settings.humor, honesty: settings.honesty, discretion: settings.discretion });
      tarsApi.getConversations().then(({conversations}) => {
        const state = useTarsStore.getState();
        const merged = conversations.filter(c => c.message_count > 0).map(c => {
          const cached = state.sessions.find(session => session.id === c.id);
          return cached || {id:c.id,name:c.legacy_id || 'Conversation',messages:[],createdAt:new Date(c.created_at),updatedAt:new Date(c.created_at)};
        });
        // Keep new browser sessions until their first server turn is persisted.
        useTarsStore.setState({sessions:[...merged,...state.sessions.filter(session=>!merged.some(item=>item.id===session.id))]});
        if (state.currentSessionId) useTarsStore.getState().loadSession(state.currentSessionId);
      }).catch(console.error);
      setSettingsReady(true);
    }).catch(console.error);
  }, []);

  // Sync settings with backend on change
  useEffect(() => {
    if (!settingsReady) return;
    const syncSettings = async () => {
      try {
        await tarsApi.updateSettings({ humor, honesty, discretion });
      } catch (error) {
        console.error('Failed to sync settings:', error);
      }
    };

    // Debounce the sync
    const timeout = setTimeout(syncSettings, 500);
    return () => clearTimeout(timeout);
  }, [humor, honesty, discretion, settingsReady]);

  // Send message function
  const sendMessage = useCallback((content: string) => {
    if (!settingsReady || !content.trim() || useTarsStore.getState().status !== 'idle') return;
    const conversationId = useTarsStore.getState().ensureCurrentSession();

    // Add user message to store
    addMessage({ role: 'user', content: content.trim() });
    setStatus('thinking');

    // Send via WebSocket with streaming
    if (wsRef.current?.isConnected()) {
      wsRef.current.send(content.trim(), true, conversationId);
    } else {
      // Fallback to REST API
      tarsApi.chat(content.trim(), true, conversationId)
        .then((response) => {
          if (useTarsStore.getState().currentSessionId !== conversationId) return;
          addMessage({
            role: 'tars',
            content: response.response,
              });
          setStatus('idle');
        })
        .catch((error) => {
          console.error('Chat error:', error);
          addMessage({
            role: 'tars',
            content: 'Communication error. Unable to process request.',
          });
          setStatus('idle');
        });
    }
  }, [addMessage, setStatus, settingsReady]);

  // Clear chat and backend history
  const clearChat = useCallback(async () => {
    try {
      const conversationId = useTarsStore.getState().currentSessionId;
      await tarsApi.clearHistory(conversationId || undefined);
      useTarsStore.getState().clearMessages();
    } catch (error) {
      console.error('Failed to clear history:', error);
    }
  }, []);

  return {
    sendMessage,
    clearChat,
    cancelTurn: async () => {
      if (activeTurn.current) await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/turns/${activeTurn.current}/cancel`, { method: 'POST', credentials: 'include' });
    },
    isConnected: wsRef.current?.isConnected() ?? false,
  };
}
