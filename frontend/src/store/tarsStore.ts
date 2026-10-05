import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Message {
  id: string;
  role: 'user' | 'tars';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  confidence?: number;
  source?: string;
}

export interface ChatSession {
  id: string;
  name: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export type TarsStatus = 'idle' | 'listening' | 'thinking' | 'speaking';

interface TarsState {
  // Personality Settings (0-100)
  humor: number;
  honesty: number;
  discretion: number;
  
  // Extended Settings
  responseSpeed: number;  // 0 = slow/thoughtful, 100 = fast/snappy
  verbosity: number;      // 0 = terse, 100 = detailed
  cautionLevel: number;   // 0 = bold/risky, 100 = very careful
  trustLevel: number;     // 0 = skeptical, 100 = trusting
  
  // System State
  status: TarsStatus;
  isVoiceMode: boolean;
  isMuted: boolean;
  
  // Chat
  messages: Message[];
  isConnected: boolean;
  
  // Chat History
  sessions: ChatSession[];
  currentSessionId: string | null;
  isHistoryOpen: boolean;
  
  // Command Palette
  isCommandPaletteOpen: boolean;
  
  // System Stats
  totalMessages: number;
  totalSessions: number;
  uptime: Date;
  
  // Actions - Personality
  setHumor: (value: number) => void;
  setHonesty: (value: number) => void;
  setDiscretion: (value: number) => void;
  setResponseSpeed: (value: number) => void;
  setVerbosity: (value: number) => void;
  setCautionLevel: (value: number) => void;
  setTrustLevel: (value: number) => void;
  
  // Actions - System
  setStatus: (status: TarsStatus) => void;
  toggleVoiceMode: () => void;
  toggleMute: () => void;
  
  // Actions - Chat
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateLastMessage: (content: string, isStreaming?: boolean) => void;
  clearMessages: () => void;
  setConnected: (connected: boolean) => void;
  
  // Actions - Sessions
  createNewSession: (name?: string) => void;
  ensureCurrentSession: () => string;
  saveCurrentSession: () => void;
  loadSession: (sessionId: string) => void;
  deleteSession: (sessionId: string) => void;
  renameSession: (sessionId: string, name: string) => void;
  toggleHistory: () => void;
  setHistoryOpen: (open: boolean) => void;
  
  // Actions - Command Palette
  toggleCommandPalette: () => void;
  setCommandPaletteOpen: (open: boolean) => void;
  
  // Actions - Presets
  applyPreset: (preset: 'cooper' | 'brand' | 'comedy' | 'mission' | 'analyst' | 'creative') => void;
  
  // Actions - Export
  exportCurrentChat: () => string;
  exportAllSessions: () => string;
}

const generateSessionName = () => {
  const adjectives = ['Stellar', 'Quantum', 'Orbital', 'Deep Space', 'Mission', 'Endurance'];
  const nouns = ['Log', 'Report', 'Brief', 'Analysis', 'Session', 'Transmission'];
  return `${adjectives[Math.floor(Math.random() * adjectives.length)]} ${nouns[Math.floor(Math.random() * nouns.length)]}`;
};

export const useTarsStore = create<TarsState>()(
  persist(
    (set, get) => ({
      // Default personality settings
      humor: 75,
      honesty: 90,
      discretion: 50,
      
      // Default extended settings
      responseSpeed: 60,
      verbosity: 50,
      cautionLevel: 40,
      trustLevel: 70,
      
      // Initial system state
      status: 'idle',
      isVoiceMode: false,
      isMuted: false,
      
      // Empty chat
      messages: [],
      isConnected: true,
      
      // Sessions
      sessions: [],
      currentSessionId: null,
      isHistoryOpen: false,
      
      // Command Palette
      isCommandPaletteOpen: false,
      
      // Stats
      totalMessages: 0,
      totalSessions: 0,
      uptime: new Date(),
      
      // Personality actions
      setHumor: (value) => set({ humor: value }),
      setHonesty: (value) => set({ honesty: value }),
      setDiscretion: (value) => set({ discretion: value }),
      setResponseSpeed: (value) => set({ responseSpeed: value }),
      setVerbosity: (value) => set({ verbosity: value }),
      setCautionLevel: (value) => set({ cautionLevel: value }),
      setTrustLevel: (value) => set({ trustLevel: value }),
      
      // System actions
      setStatus: (status) => set({ status }),
      toggleVoiceMode: () => set((state) => ({ isVoiceMode: !state.isVoiceMode })),
      toggleMute: () => set((state) => ({ isMuted: !state.isMuted })),
      
      // Chat actions
      addMessage: (message) => set((state) => ({
        messages: [
          ...state.messages,
          {
            ...message,
            id: crypto.randomUUID(),
            timestamp: new Date(),
          },
        ],
        totalMessages: state.totalMessages + 1,
      })),
      
      updateLastMessage: (content, isStreaming = false) => set((state) => {
        const messages = [...state.messages];
        if (messages.length > 0) {
          messages[messages.length - 1] = {
            ...messages[messages.length - 1],
            content,
            isStreaming,
          };
        }
        return { messages };
      }),
      
      clearMessages: () => set({ messages: [] }),
      setConnected: (connected) => set({ isConnected: connected }),
      
      // Session actions
      createNewSession: (name) => {
        const state = get();
        // Save current session first if has messages
        if (state.messages.length > 0 && state.currentSessionId) {
          state.saveCurrentSession();
        }
        
        const newSession: ChatSession = {
          id: crypto.randomUUID(),
          name: name || generateSessionName(),
          messages: [],
          createdAt: new Date(),
          updatedAt: new Date(),
        };
        
        set({
          sessions: [newSession, ...state.sessions],
          currentSessionId: newSession.id,
          messages: [],
          totalSessions: state.totalSessions + 1,
        });
      },

      ensureCurrentSession: () => {
        const state = get();
        if (state.currentSessionId) return state.currentSessionId;
        const newSession: ChatSession = {
          id: crypto.randomUUID(),
          name: generateSessionName(),
          messages: [],
          createdAt: new Date(),
          updatedAt: new Date(),
        };
        set((current) => ({
          sessions: [newSession, ...current.sessions],
          currentSessionId: newSession.id,
          totalSessions: current.totalSessions + 1,
        }));
        return newSession.id;
      },
      
      saveCurrentSession: () => set((state) => {
        if (!state.currentSessionId || state.messages.length === 0) return state;
        
        const updatedSessions = state.sessions.map((session) =>
          session.id === state.currentSessionId
            ? { ...session, messages: state.messages, updatedAt: new Date() }
            : session
        );
        
        // If session doesn't exist, create it
        const sessionExists = state.sessions.some(s => s.id === state.currentSessionId);
        if (!sessionExists) {
          updatedSessions.unshift({
            id: state.currentSessionId,
            name: generateSessionName(),
            messages: state.messages,
            createdAt: new Date(),
            updatedAt: new Date(),
          });
        }
        
        return { sessions: updatedSessions };
      }),
      
      loadSession: (sessionId) => {
        const state = get();
        // Save current first
        if (state.messages.length > 0 && state.currentSessionId) {
          state.saveCurrentSession();
        }
        
        const session = state.sessions.find((s) => s.id === sessionId);
        if (session) {
          set({
            currentSessionId: sessionId,
            messages: session.messages.map(m => ({
              ...m,
              timestamp: new Date(m.timestamp)
            })),
            isHistoryOpen: false,
          });
        }
      },
      
      deleteSession: (sessionId) => set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== sessionId),
        ...(state.currentSessionId === sessionId ? { currentSessionId: null, messages: [] } : {}),
      })),
      
      renameSession: (sessionId, name) => set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === sessionId ? { ...s, name } : s
        ),
      })),
      
      toggleHistory: () => set((state) => ({ isHistoryOpen: !state.isHistoryOpen })),
      setHistoryOpen: (open) => set({ isHistoryOpen: open }),
      
      // Command Palette
      toggleCommandPalette: () => set((state) => ({ isCommandPaletteOpen: !state.isCommandPaletteOpen })),
      setCommandPaletteOpen: (open) => set({ isCommandPaletteOpen: open }),
      
      // Presets
      applyPreset: (preset) => {
        const presets = {
          cooper: { humor: 75, honesty: 90, discretion: 50, responseSpeed: 60, verbosity: 50, cautionLevel: 40, trustLevel: 70 },
          brand: { humor: 40, honesty: 95, discretion: 70, responseSpeed: 45, verbosity: 70, cautionLevel: 60, trustLevel: 50 },
          comedy: { humor: 100, honesty: 50, discretion: 30, responseSpeed: 80, verbosity: 60, cautionLevel: 20, trustLevel: 80 },
          mission: { humor: 20, honesty: 100, discretion: 80, responseSpeed: 70, verbosity: 40, cautionLevel: 90, trustLevel: 40 },
          analyst: { humor: 30, honesty: 95, discretion: 60, responseSpeed: 40, verbosity: 90, cautionLevel: 70, trustLevel: 60 },
          creative: { humor: 80, honesty: 70, discretion: 40, responseSpeed: 55, verbosity: 80, cautionLevel: 30, trustLevel: 85 },
        };
        set(presets[preset]);
      },
      
      // Export
      exportCurrentChat: () => {
        const state = get();
        const data = {
          exportedAt: new Date().toISOString(),
          messages: state.messages,
          settings: {
            humor: state.humor,
            honesty: state.honesty,
            discretion: state.discretion,
            responseSpeed: state.responseSpeed,
            verbosity: state.verbosity,
            cautionLevel: state.cautionLevel,
            trustLevel: state.trustLevel,
          },
        };
        return JSON.stringify(data, null, 2);
      },
      
      exportAllSessions: () => {
        const state = get();
        return JSON.stringify(state.sessions, null, 2);
      },
    }),
    {
      name: 'tars-storage',
      partialize: (state) => ({
        sessions: state.sessions,
        totalMessages: state.totalMessages,
        totalSessions: state.totalSessions,
        humor: state.humor,
        honesty: state.honesty,
        discretion: state.discretion,
        responseSpeed: state.responseSpeed,
        verbosity: state.verbosity,
        cautionLevel: state.cautionLevel,
        trustLevel: state.trustLevel,
      }),
    }
  )
);
