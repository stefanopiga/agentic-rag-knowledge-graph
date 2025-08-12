import { apiClient } from "./api";
// import { useAuthStore } from "@/stores/authStore"; // non usato direttamente qui

interface ChatStreamRequest {
  message: string;
  session_id?: string;
  tenant_id: string;
  user_id?: string;
}

interface StreamHandlers {
  onSession?: (sessionId: string) => void;
  onText?: (chunk: string) => void;
  onTools?: (tools: any[]) => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
}

export const startChatStream = async (
  payload: ChatStreamRequest,
  handlers: StreamHandlers,
  abortController?: AbortController
): Promise<void> => {
  const baseUrl = apiClient.getBaseUrl();

  const controller = abortController || new AbortController();

  const response = await fetch(`${baseUrl}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      // Authorization header viene gestito da apiClient se necessario a livello globale
    },
    body: JSON.stringify(payload),
    signal: controller.signal,
  });

  if (!response.ok || !response.body) {
    handlers.onError?.(`HTTP ${response.status}`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const rawEvent = buffer.slice(0, boundary).trim();
      buffer = buffer.slice(boundary + 2);

      if (rawEvent.startsWith("data:")) {
        const dataStr = rawEvent.slice(5).trim();
        try {
          const evt = JSON.parse(dataStr);
          switch (evt.type) {
            case "session":
              handlers.onSession?.(evt.session_id);
              break;
            case "text":
              handlers.onText?.(evt.content ?? "");
              break;
            case "tools":
              handlers.onTools?.(evt.tools ?? []);
              break;
            case "end":
              handlers.onEnd?.();
              break;
            case "error":
              handlers.onError?.(evt.content ?? "stream error");
              break;
            default:
              break;
          }
        } catch (e) {
          handlers.onError?.("invalid JSON event");
        }
      }

      boundary = buffer.indexOf("\n\n");
    }
  }
};
