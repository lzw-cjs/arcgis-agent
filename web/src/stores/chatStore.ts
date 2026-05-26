import { create } from 'zustand';
import type { Message, ToolCall, ChatState } from '../types';

function generateId(): string {
  return crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  sessionId: generateId(),
  loading: false,
  mapPanelOpen: false,
  error: null,

  addMessage: (msg) =>
    set((s) => ({
      messages: [...s.messages, msg],
      error: null,
    })),

  appendContent: (content) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = {
          ...last,
          content: last.content + content,
        };
      }
      return { messages: msgs };
    }),

  setLoading: (v) => set({ loading: v }),

  toggleMapPanel: () => set((s) => ({ mapPanelOpen: !s.mapPanelOpen })),

  setError: (err) => set({ error: err }),

  clearMessages: () =>
    set({
      messages: [],
      sessionId: generateId(),
      error: null,
    }),

  updateLastToolCall: (call) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last?.toolCalls?.length) {
        const updatedCalls = [...last.toolCalls];
        const lastCall = updatedCalls[updatedCalls.length - 1];
        updatedCalls[updatedCalls.length - 1] = { ...lastCall, ...call };
        msgs[msgs.length - 1] = { ...last, toolCalls: updatedCalls };
      }
      return { messages: msgs };
    }),

  addToolCallToLastMessage: (call) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = {
          ...last,
          toolCalls: [...(last.toolCalls || []), call],
        };
      }
      return { messages: msgs };
    }),

  setSuggestions: (suggestions) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === 'assistant') {
        msgs[msgs.length - 1] = { ...last, suggestions };
      }
      return { messages: msgs };
    }),
}));
