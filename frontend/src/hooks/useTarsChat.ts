/**
 * useTarsChat Hook
 * Manages WebSocket connection to TARS backend and handles chat interactions
 */

import { useEffect, useRef, useCallback } from 'react';
import { TarsWebSocket, ChatMessage, tarsApi } from '@/services/tarsApi';
import { useTarsStore } from '@/store/tarsStore';

export function useTarsChat() {
  const wsRef = useRef<TarsWebSocket | null>(null);
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
    switch (msg.type) {
      case 'greeting':
        addMessage({
          role: 'tars',
          content: msg.content || 'Connection established.',
          confidence: 100,
          source: 'SYSTEM',
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

      case 'response':
        // Non-streaming response
        addMessage({
          role: 'tars',
          content: msg.content || '',
          confidence: 95,
          source: 'DATA ARCHIVES',
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
      () => setConnected(false),
      (error) => console.error('WebSocket error:', error)
    );

    wsRef.current.connect();

    return () => {
      wsRef.current?.disconnect();
    };
  }, [handleMessage, setConnected]);

  // Sync settings with backend on change
  useEffect(() => {
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
  }, [humor, honesty, discretion]);

  // Send message function
  const sendMessage = useCallback((content: string) => {
    if (!content.trim()) return;
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
          addMessage({
            role: 'tars',
            content: response.response,
            confidence: 95,
            source: 'DATA ARCHIVES',
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
  }, [addMessage, setStatus]);

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
    isConnected: wsRef.current?.isConnected() ?? false,
  };
}
