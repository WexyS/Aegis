import { create } from 'zustand';
import { StreamChunk } from '@/types/runtime';

const MAX_MESSAGES = 300;

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  isComplete: boolean;
  nextSequenceId: number;
  pendingChunks: Record<number, string>;
  tools?: any[];
}

export interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  abortController: AbortController | null;
  addMessage: (message: Partial<Message>) => string;
  handleStreamChunk: (chunk: StreamChunk) => void;
  finalizeMessage: (messageId: string) => void;
  abortStream: () => void;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isStreaming: false,
  abortController: null,

  addMessage: (msg) => {
    const id = msg.id || crypto.randomUUID();
    const newMessage: Message = {
      id,
      role: msg.role || 'assistant',
      content: msg.content || '',
      timestamp: msg.timestamp || new Date().toLocaleTimeString(),
      isComplete: msg.isComplete ?? true,
      nextSequenceId: 0,
      pendingChunks: {},
    };
    set((state) => {
      const messages = [...state.messages, newMessage];
      if (messages.length > MAX_MESSAGES) {
        messages.splice(0, messages.length - MAX_MESSAGES);
      }
      return { messages };
    });
    return id;
  },

  handleStreamChunk: (chunk) => {
    set((state) => {
      const messages = state.messages.map((m) => {
        if (m.id === chunk.messageId) {
          if (chunk.sequenceId < m.nextSequenceId || m.pendingChunks[chunk.sequenceId] !== undefined) {
            return m;
          }

          let content = m.content;
          let nextSequenceId = m.nextSequenceId;
          let pendingChunks = m.pendingChunks;

          if (chunk.sequenceId === nextSequenceId) {
            content += chunk.content;
            nextSequenceId += 1;

            while (pendingChunks[nextSequenceId] !== undefined) {
              content += pendingChunks[nextSequenceId];
              pendingChunks = { ...pendingChunks };
              delete pendingChunks[nextSequenceId];
              nextSequenceId += 1;
            }
          } else {
            pendingChunks = { ...pendingChunks, [chunk.sequenceId]: chunk.content };
          }

          return { ...m, content, nextSequenceId, pendingChunks };
        }
        return m;
      });
      return { messages, isStreaming: true };
    });
  },

  finalizeMessage: (id) => {
    set((state) => ({
      isStreaming: false,
      messages: state.messages.map(m => m.id === id ? { ...m, isComplete: true } : m)
    }));
  },

  abortStream: () => {
    const { abortController } = get();
    if (abortController) abortController.abort();
    set({ isStreaming: false, abortController: null });
  },

  clearChat: () => set({ messages: [] }),
}));
