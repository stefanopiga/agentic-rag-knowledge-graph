import { apiClient } from "./api";
import {
  type SendMessageRequest,
  type SendMessageResponse,
  type ChatMessage,
  type ChatSession,
} from "../types/api";
import { startChatStream } from "@/services/stream";

export interface StreamingHandlers {
  onSession?: (sessionId: string) => void;
  onText?: (chunk: string) => void;
  onTools?: (tools: any[]) => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
}

class ChatService {
  async sendMessage(request: SendMessageRequest): Promise<SendMessageResponse> {
    // Backend richiede snake_case e campi specifici
    const payload: any = {
      message: request.message,
      tenant_id: request.tenantId,
    };
    if (request.sessionId) payload.session_id = request.sessionId;

    const res = await apiClient.post<any>("/chat", payload);

    const mapped: SendMessageResponse = {
      message: res.message,
      sessionId: res.session_id ?? res.sessionId,
      sources: res.sources ?? [],
      toolCalls: res.tools_used ?? res.toolCalls ?? [],
    };

    return mapped;
  }

  async sendStreamingMessage(
    request: SendMessageRequest,
    handlers: StreamingHandlers,
    abortController?: AbortController
  ): Promise<void> {
    const payload: any = {
      message: request.message,
      tenant_id: request.tenantId,
    };
    if (request.sessionId) payload.session_id = request.sessionId;

    return startChatStream(payload, handlers, abortController);
  }

  async getSessionHistory(sessionId: string): Promise<ChatMessage[]> {
    return apiClient.get<ChatMessage[]>(`/chat/sessions/${sessionId}/history`);
  }

  async getSessions(tenantId: string): Promise<ChatSession[]> {
    return apiClient.get<ChatSession[]>("/chat/sessions", { tenantId });
  }

  async createSession(tenantId: string, title?: string): Promise<ChatSession> {
    return apiClient.post<ChatSession>("/chat/sessions", {
      tenantId,
      title,
    });
  }

  async deleteSession(sessionId: string): Promise<void> {
    return apiClient.delete<void>(`/chat/sessions/${sessionId}`);
  }

  async updateSessionTitle(
    sessionId: string,
    title: string
  ): Promise<ChatSession> {
    return apiClient.patch<ChatSession>(`/chat/sessions/${sessionId}`, {
      title,
    });
  }

  async exportSession(
    sessionId: string,
    format: "pdf" | "docx" | "txt"
  ): Promise<Blob> {
    const response = await apiClient.get<Blob>(
      `/chat/sessions/${sessionId}/export`,
      { format }
    );
    return response;
  }

  async searchSessions(
    tenantId: string,
    query: string,
    limit: number = 10
  ): Promise<ChatSession[]> {
    return apiClient.get<ChatSession[]>("/chat/sessions/search", {
      tenantId,
      query,
      limit,
    });
  }

  async getSessionAnalytics(
    tenantId: string,
    fromDate?: string,
    toDate?: string
  ): Promise<{
    totalSessions: number;
    totalMessages: number;
    avgSessionLength: number;
    popularTopics: string[];
  }> {
    return apiClient.get("/chat/analytics", {
      tenantId,
      fromDate,
      toDate,
    });
  }
}

export const chatService = new ChatService();
