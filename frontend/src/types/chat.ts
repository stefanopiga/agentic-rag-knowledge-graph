import type { ChatMessage, Source } from "./api";

export interface ChatState {
  messages: ChatMessage[];
  currentSession: string | null;
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;
  isStreaming?: boolean;
  streamError?: string | null;
}

export interface ChatActions {
  sendMessage: (content: string, useStream?: boolean) => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  clearMessages: () => void;
  setError: (error: string | null) => void;
  appendMessageChunk: (chunk: string) => void;
  completeMessage: (data: unknown) => void;
}

export interface MessageBubbleProps {
  message: ChatMessage;
  onSourceClick?: (source: Source) => void;
}

export interface SourceCitationProps {
  sources: Source[];
  onSourceClick?: (source: Source) => void;
}

export interface TypingIndicatorProps {
  isVisible: boolean;
}

export interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}
