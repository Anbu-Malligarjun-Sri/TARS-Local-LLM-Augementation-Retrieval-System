/**
 * TARS API Service
 * Handles all communication with the FastAPI backend
 */

// Use environment variable for API URL, fallback to localhost for development
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Build WebSocket URL based on API_BASE
function getWebSocketUrl(): string {
  let wsBase = API_BASE.replace(/\/$/, '');
  
  // If API_BASE is relative (like /api), build full URL from current location
  if (!wsBase.startsWith('http')) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    wsBase = `${protocol}//${window.location.host}${wsBase}`;
  }
  
  // Convert http/https to ws/wss
  wsBase = wsBase.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:');
  
  return `${wsBase}/api/ws/chat`;
}

// Types
export interface ChatMessage {
  type: 'greeting' | 'response' | 'start' | 'chunk' | 'end';
  content?: string;
  full_response?: string;
}

export interface TarsSettings {
  humor: number;
  honesty: number;
  discretion: number;
  responseSpeed?: number;
  verbosity?: number;
  cautionLevel?: number;
  trustLevel?: number;
}

export interface RagStats {
  total_documents: number;
  loaded_datasets: number;
  topics: string[];
  embedding_model: string;
  embedding_dimension: number;
}

// REST API functions
export const tarsApi = {
  // Chat endpoints
  async chat(message: string, enhance = true): Promise<{ response: string; conversation_id?: string }> {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, enhance_response: enhance, stream: false }),
    });
    if (!res.ok) throw new Error(`Chat failed: ${res.statusText}`);
    return res.json();
  },

  async getGreeting(): Promise<{ greeting: string }> {
    const res = await fetch(`${API_BASE}/api/chat/greeting`);
    if (!res.ok) throw new Error(`Failed to get greeting: ${res.statusText}`);
    return res.json();
  },

  // Settings endpoints
  async getSettings(): Promise<TarsSettings> {
    const res = await fetch(`${API_BASE}/api/settings`);
    if (!res.ok) throw new Error(`Failed to get settings: ${res.statusText}`);
    return res.json();
  },

  async updateSettings(settings: Partial<TarsSettings>): Promise<TarsSettings> {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error(`Failed to update settings: ${res.statusText}`);
    return res.json();
  },

  // History endpoints
  async getHistory(): Promise<{ conversation_id: string; messages: unknown[]; count: number }> {
    const res = await fetch(`${API_BASE}/api/history`);
    if (!res.ok) throw new Error(`Failed to get history: ${res.statusText}`);
    return res.json();
  },

  async clearHistory(): Promise<{ message: string; status: string }> {
    const res = await fetch(`${API_BASE}/api/history`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Failed to clear history: ${res.statusText}`);
    return res.json();
  },

  // RAG endpoints
  async getRagStats(): Promise<RagStats> {
    const res = await fetch(`${API_BASE}/api/rag/stats`);
    if (!res.ok) throw new Error(`Failed to get RAG stats: ${res.statusText}`);
    return res.json();
  },

  async searchRag(query: string, n_results = 5): Promise<{ query: string; results: unknown }> {
    const res = await fetch(`${API_BASE}/api/rag/search?query=${encodeURIComponent(query)}&n_results=${n_results}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`RAG search failed: ${res.statusText}`);
    return res.json();
  },

  // Health check
  async health(): Promise<{ status: string; llm_provider: string; rag_enabled: boolean; voice_enabled: boolean }> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  },
};

// WebSocket connection manager
export class TarsWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(
    private onMessage: (msg: ChatMessage) => void,
    private onConnect: () => void,
    private onDisconnect: () => void,
    private onError: (error: Event) => void
  ) {}

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    try {
      const wsUrl = getWebSocketUrl();
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.onConnect();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as ChatMessage;
          this.onMessage(data);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.ws.onclose = () => {
        this.onDisconnect();
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        this.onError(error);
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
    }
  }

  send(message: string, stream = true): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ message, stream }));
    } else {
      console.error('WebSocket not connected');
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
