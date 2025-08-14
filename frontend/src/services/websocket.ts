import { io, Socket } from "socket.io-client";
import { useAuthStore } from "../stores/authStore";
import { useChatStore } from "../stores/chatStore";

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(tenantId: string): Socket {
    if (this.socket?.connected) {
      return this.socket;
    }

    const token = useAuthStore.getState().token;
    const baseUrl =
      (import.meta.env.VITE_WS_URL as string) ||
      (import.meta.env.VITE_API_BASE_URL as string) ||
      (import.meta.env.VITE_API_URL as string) ||
      "http://localhost:8000";

    this.socket = io(baseUrl, {
      auth: {
        token,
      },
      query: {
        tenantId,
      },
      transports: ["websocket", "polling"],
    });

    this.setupEventListeners();
    return this.socket;
  }

  private setupEventListeners() {
    if (!this.socket) return;

    this.socket.on("connect", () => {
      console.log("WebSocket connected");
      this.reconnectAttempts = 0;

      // Update chat store connection status
      useChatStore.setState({ isConnected: true });
    });

    this.socket.on("disconnect", (reason) => {
      console.log("WebSocket disconnected:", reason);
      useChatStore.setState({ isConnected: false });

      // Auto-reconnect on certain disconnect reasons
      if (reason === "io server disconnect") {
        // Server initiated disconnect, don't reconnect
        return;
      }

      this.handleReconnect();
    });

    this.socket.on("connect_error", (error) => {
      console.error("WebSocket connection error:", error);
      this.handleReconnect();
    });

    // Chat-specific events
    this.socket.on(
      "message_chunk",
      (data: { chunk: string; messageId: string }) => {
        useChatStore.getState().appendMessageChunk(data.chunk);
      }
    );

    this.socket.on(
      "message_complete",
      (data: { messageId: string; sources?: any[]; toolCalls?: any[] }) => {
        useChatStore.getState().completeMessage(data);
      }
    );

    this.socket.on("typing_start", () => {
      // Handle typing indicator
      console.log("Assistant started typing");
    });

    this.socket.on("typing_stop", () => {
      // Handle typing indicator
      console.log("Assistant stopped typing");
    });

    this.socket.on("error", (error: any) => {
      console.error("WebSocket error:", error);
      useChatStore.getState().setError("Connection error occurred");
    });

    // Tenant-specific events
    this.socket.on(
      "document_processing",
      (data: {
        documentId: string;
        status: "processing" | "completed" | "error";
        progress?: number;
      }) => {
        // Handle document processing updates
        console.log("Document processing update:", data);
      }
    );

    this.socket.on("metrics_update", (data: any) => {
      // Handle real-time metrics updates
      console.log("Metrics update:", data);
    });
  }

  private handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      useChatStore
        .getState()
        .setError("Connection lost. Please refresh the page.");
      return;
    }

    this.reconnectAttempts++;
    console.log(
      `Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`
    );

    setTimeout(() => {
      this.socket?.connect();
    }, Math.pow(2, this.reconnectAttempts) * 1000); // Exponential backoff
  }

  disconnect() {
    if (this.socket) {
      this.socket.removeAllListeners();
      this.socket.disconnect();
      this.socket = null;
    }
    useChatStore.setState({ isConnected: false });
  }

  // Send message through WebSocket for real-time chat
  sendMessage(message: string, sessionId?: string) {
    if (!this.socket?.connected) {
      throw new Error("WebSocket not connected");
    }

    const { tenant } = useAuthStore.getState();
    if (!tenant) {
      throw new Error("No tenant selected");
    }

    this.socket.emit("send_message", {
      message,
      sessionId,
      tenantId: tenant.id,
      timestamp: new Date().toISOString(),
    });
  }

  // Join a specific chat session room
  joinSession(sessionId: string) {
    if (this.socket?.connected) {
      this.socket.emit("join_session", { sessionId });
    }
  }

  // Leave a chat session room
  leaveSession(sessionId: string) {
    if (this.socket?.connected) {
      this.socket.emit("leave_session", { sessionId });
    }
  }

  // Get connection status
  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const wsService = new WebSocketService();
