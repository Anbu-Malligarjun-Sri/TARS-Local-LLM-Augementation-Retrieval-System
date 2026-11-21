/**
 * TARS API Service
 * Handles all communication with the FastAPI backend
 */

// Use environment variable for API URL, fallback to localhost for development
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Device cookies are HttpOnly; the owner bootstrap token is never persisted.
async function apiFetch(url: string, options: RequestInit = {}) {
  return fetch(url, { ...options, credentials: 'include' });
}
export async function pairDevice(token: string) {
  const response = await apiFetch(`${API_BASE}/api/pair`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token }),
  });
  if (!response.ok) throw new Error('Pairing failed. Check the server token.');
}

export async function redeemLaunch(token: string) {
  const response = await apiFetch(`${API_BASE}/api/launch`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token }),
  });
  if (!response.ok) throw new Error('Launch link expired. Generate a new local launch link.');
}

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
  type: 'greeting' | 'response' | 'start' | 'chunk' | 'end' | 'error' | 'cancelled';
  content?: string;
  full_response?: string;
  conversation_id?: string;
  turn_id?: string;
  sequence?: number;
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

export interface ChatStyle {audience:'owner'|'parent'|'friend'|'professional'|'unknown';playful:boolean;language?:'en-IN'|'ta-IN'}
export async function cancelChatTurn(id:string){
  const response=await apiFetch(`${API_BASE}/api/turns/${id}/cancel`,{method:'POST'});
  if(!response.ok)throw new Error('Server cancellation was not acknowledged. Local playback and display have stopped.');
}
export async function streamChat(message:string,conversationId:string,turnId:string,style:ChatStyle,signal:AbortSignal,onEvent:(event:ChatMessage)=>void){
 const response=await apiFetch(`${API_BASE}/api/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,conversation_id:conversationId,turn_id:turnId,style,stream:true}),signal});
 if(!response.ok || !response.body)throw new Error(`Chat failed (${response.status}).`);
 const reader=response.body.getReader();const decoder=new TextDecoder();let pending='';let terminal=false;
 try{
  while(true){const {done,value}=await reader.read();if(done)break;pending+=decoder.decode(value,{stream:true});
   if(pending.length>1000000)throw new Error('Chat event exceeded the size limit.');
   let boundary:number;
   while((boundary=pending.indexOf('\n\n'))>=0){const frame=pending.slice(0,boundary);pending=pending.slice(boundary+2);
    const payload=frame.split('\n').filter(line=>line.startsWith('data: ')).map(line=>line.slice(6)).join('\n');if(!payload)continue;
    const event=JSON.parse(payload) as ChatMessage;
    if(event.turn_id!==turnId || event.conversation_id!==conversationId)continue;
    onEvent(event);if(['end','cancelled','error'].includes(event.type)){terminal=true;return;}
   }
  }
  if(!terminal && !signal.aborted)throw new Error('Response connection closed before completion.');
 }finally{await reader.cancel().catch(()=>undefined);reader.releaseLock();}
}

// REST API functions
export const tarsApi = {
  // Chat endpoints
  async chat(message: string, enhance = true, conversationId?: string): Promise<{ response: string; conversation_id?: string }> {
    const res = await apiFetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, enhance_response: enhance, stream: false, conversation_id: conversationId }),
    });
    if (!res.ok) throw new Error(`Chat failed: ${res.statusText}`);
    return res.json();
  },

  async getGreeting(): Promise<{ greeting: string }> {
    const res = await apiFetch(`${API_BASE}/api/chat/greeting`);
    if (!res.ok) throw new Error(`Failed to get greeting: ${res.statusText}`);
    return res.json();
  },

  // Settings endpoints
  async getSettings(): Promise<TarsSettings> {
    const res = await apiFetch(`${API_BASE}/api/settings`);
    if (!res.ok) throw new Error(`Failed to get settings: ${res.statusText}`);
    return res.json();
  },

  async updateSettings(settings: Partial<TarsSettings>): Promise<TarsSettings> {
    const res = await apiFetch(`${API_BASE}/api/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error(`Failed to update settings: ${res.statusText}`);
    return res.json();
  },

  async getConversations(): Promise<{conversations: {id: string; created_at: string; legacy_id?: string; message_count: number}[]}> {
    const response = await apiFetch(`${API_BASE}/api/conversations`);
    if (!response.ok) throw new Error('Unable to load server conversations');
    return response.json();
  },

  // History endpoints
  async getHistory(conversationId?: string): Promise<{ conversation_id: string; messages: unknown[]; count: number; audience?:ChatStyle['audience'] }> {
    const query = conversationId ? `?conversation_id=${encodeURIComponent(conversationId)}` : '';
    const res = await apiFetch(`${API_BASE}/api/history${query}`);
    if (!res.ok) throw new Error(`Failed to get history: ${res.statusText}`);
    return res.json();
  },

  async clearHistory(conversationId?: string): Promise<{ message: string; status: string }> {
    const query = conversationId ? `?conversation_id=${encodeURIComponent(conversationId)}` : '';
    const res = await apiFetch(`${API_BASE}/api/history${query}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`Failed to clear history: ${res.statusText}`);
    return res.json();
  },

  // RAG endpoints
  async getRagStats(): Promise<RagStats> {
    const res = await apiFetch(`${API_BASE}/api/rag/stats`);
    if (!res.ok) throw new Error(`Failed to get RAG stats: ${res.statusText}`);
    return res.json();
  },

  async searchRag(query: string, n_results = 5): Promise<{ query: string; results: unknown }> {
    const res = await apiFetch(`${API_BASE}/api/rag/search?query=${encodeURIComponent(query)}&n_results=${n_results}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`RAG search failed: ${res.statusText}`);
    return res.json();
  },

  // Health check
  async health(): Promise<{ status: string; llm_provider: string; rag_enabled: boolean; voice_enabled: boolean }> {
    const res = await apiFetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  },
};

// WebSocket connection manager
export class TarsWebSocket {
  private ws: WebSocket | null = null;
  private closed = false;
  private timer: ReturnType<typeof setTimeout> | undefined;
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
    if (this.closed) return;
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
    if (!this.closed && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      this.timer = setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
    }
  }

  send(message: string, stream = true, conversationId?: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ message, stream, conversation_id: conversationId }));
    } else {
      console.error('WebSocket not connected');
    }
  }

  disconnect(): void {
    this.closed = true;
    clearTimeout(this.timer);
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
