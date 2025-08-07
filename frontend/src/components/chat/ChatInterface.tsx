import React, { useEffect, useRef } from "react";
import { MessageBubble } from "./MessageBubble";
import { MessageInput } from "./MessageInput";
import { TypingIndicator } from "./TypingIndicator";
import { useChatStore } from "@/stores/chatStore";
import type { Source } from "@/types/api";
import { Button } from "@/components/ui";

export interface ChatInterfaceProps {
  onSourceClick?: (source: Source) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  onSourceClick,
}) => {
  const {
    messages,
    isLoading,
    isConnected,
    error,
    sendMessage,
    clearMessages,
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    try {
      await sendMessage(content);
    } catch (error) {
      console.error("Errore invio messaggio:", error);
    }
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="border-b border-border bg-surface px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-text-primary">
              Assistente FisioRAG
            </h1>
            <div className="flex items-center space-x-2 mt-1">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected ? "bg-success" : "bg-error"
                }`}
              ></div>
              <span className="text-sm text-text-secondary">
                {isConnected ? "Connesso" : "Disconnesso"}
              </span>
            </div>
          </div>

          <Button
            onClick={clearMessages}
            variant="outline"
            size="sm"
            disabled={messages.length === 0}
          >
            <svg
              className="w-4 h-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
            Cancella Chat
          </Button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-error/10 border-l-4 border-error p-4 m-4 rounded">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-error">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-text-primary mb-2">
              Benvenuto in FisioRAG
            </h3>
            <p className="text-text-secondary max-w-md">
              Inizia una conversazione facendo una domanda sui documenti medici.
              L'AI utilizzerà la knowledge graph per fornirti risposte accurate
              e fonti verificate.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onSourceClick={onSourceClick}
          />
        ))}

        <TypingIndicator isVisible={isLoading} />
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <MessageInput
        onSend={handleSendMessage}
        disabled={isLoading || !isConnected}
        placeholder={
          !isConnected
            ? "Connessione in corso..."
            : isLoading
            ? "Attendi risposta..."
            : "Fai una domanda sui documenti medici..."
        }
      />
    </div>
  );
};
