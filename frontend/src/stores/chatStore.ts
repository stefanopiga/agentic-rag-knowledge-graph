import { create } from "zustand";
import { type ChatState, type ChatActions } from "../types/chat";
import { type ChatMessage } from "../types/api";
import { chatService } from "../services/chat";
import { startChatStream } from "@/services/stream";
import { useAuthStore } from "./authStore";

interface ChatStore extends ChatState, ChatActions {}

const generateId = () => crypto.randomUUID();

export const useChatStore = create<ChatStore>((set, get) => ({
  // State
  messages: [],
  currentSession: null,
  isLoading: false,
  error: null,
  isConnected: true,
  isStreaming: false,
  streamError: null,

  // Actions
  sendMessage: async (content: string, useStream: boolean = true) => {
    const { tenant } = useAuthStore.getState();
    if (!tenant) {
      throw new Error("No tenant selected");
    }

    set({ isLoading: true, error: null });

    try {
      // Add user message immediately
      const userMessage: ChatMessage = {
        id: generateId(),
        content,
        role: "user",
        timestamp: new Date(),
      };

      set((state) => ({
        messages: [...state.messages, userMessage],
      }));

      // Stream or non-stream
      if (useStream) {
        set({ isStreaming: true, isLoading: true });

        const abortController = new AbortController();
        set({ streamError: null });

        let gotAnyChunk = false; // set true on session to avoid early fallback
        const fallbackTimer = setTimeout(async () => {
          if (get().isStreaming && !gotAnyChunk) {
            abortController.abort();
            try {
              const response = await chatService.sendMessage({
                message: content,
                sessionId: get().currentSession || undefined,
                tenantId: tenant.id,
              });
              const assistantMessage: ChatMessage = {
                id: generateId(),
                content: response.message,
                role: "assistant",
                timestamp: new Date(),
                sources: response.sources,
                toolCalls: response.toolCalls,
              };
              set((state) => ({
                messages: [...state.messages, assistantMessage],
                currentSession: response.sessionId,
                isStreaming: false,
                isLoading: false,
              }));
            } catch (e) {
              set({
                streamError: e instanceof Error ? e.message : "Stream fallback error",
                isStreaming: false,
                isLoading: false,
              });
            }
          }
        }, 7000);

        await startChatStream(
          {
            message: content,
            session_id: get().currentSession || undefined,
            tenant_id: tenant.id,
          },
          {
            onSession: (sid) => { gotAnyChunk = true; set({ currentSession: sid }); },
            onText: (chunk) => {
              gotAnyChunk = true;
              get().appendMessageChunk(chunk);
            },
            onTools: (tools) => get().completeMessage({ toolCalls: tools }),
            onEnd: () => {
              clearTimeout(fallbackTimer);
              set({ isStreaming: false, isLoading: false });
            },
            onError: (err) => {
              clearTimeout(fallbackTimer);
              set({ streamError: err, isStreaming: false, isLoading: false });
            },
          },
          abortController
        );

        return;
      }

      // Send to API
      const response = await chatService.sendMessage({
        message: content,
        sessionId: get().currentSession || undefined,
        tenantId: tenant.id,
      });

      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: generateId(),
        content: response.message,
        role: "assistant",
        timestamp: new Date(),
        sources: response.sources,
        toolCalls: response.toolCalls,
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        currentSession: response.sessionId,
        isLoading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : "Unknown error",
        isLoading: false,
      });
      throw error;
    }
  },

  loadSession: async (sessionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const messages = await chatService.getSessionHistory(sessionId);
      set({
        messages,
        currentSession: sessionId,
        isLoading: false,
      });
    } catch (error) {
      set({
        error:
          error instanceof Error ? error.message : "Failed to load session",
        isLoading: false,
      });
      throw error;
    }
  },

  clearMessages: () => {
    set({
      messages: [],
      currentSession: null,
      error: null,
    });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  appendMessageChunk: (chunk: string) => {
    set((state) => {
      const messages = [...state.messages];
      const lastMessage = messages[messages.length - 1];

      if (lastMessage && lastMessage.role === "assistant") {
        // Append to existing assistant message
        lastMessage.content += chunk;
      } else {
        // Create new assistant message
        const newMessage: ChatMessage = {
          id: generateId(),
          content: chunk,
          role: "assistant",
          timestamp: new Date(),
        };
        messages.push(newMessage);
      }

      return { messages };
    });
  },

  completeMessage: (data: any) => {
    set((state) => {
      const messages = [...state.messages];
      const lastMessage = messages[messages.length - 1];

      if (lastMessage && lastMessage.role === "assistant") {
        lastMessage.sources = data.sources;
        lastMessage.toolCalls = data.toolCalls;
      }

      return {
        messages,
        isLoading: false,
      };
    });
  },
}));
