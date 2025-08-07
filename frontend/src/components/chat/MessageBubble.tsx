import React from "react";
import type { MessageBubbleProps } from "@/types/chat";
import { SourceCitation } from "./SourceCitation";

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onSourceClick,
}) => {
  const isUser = message.role === "user";
  const timestamp = new Date(message.timestamp).toLocaleTimeString("it-IT", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div className={`max-w-[80%] ${isUser ? "order-2" : ""}`}>
        {/* Avatar */}
        <div
          className={`flex items-start space-x-3 ${
            isUser ? "flex-row-reverse space-x-reverse" : ""
          }`}
        >
          <div
            className={`
            w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium
            ${isUser ? "bg-primary" : "bg-secondary"}
          `}
          >
            {isUser ? "U" : "AI"}
          </div>

          <div className="flex-1">
            {/* Message bubble */}
            <div
              className={`
              rounded-2xl px-4 py-3 max-w-full break-words
              ${
                isUser
                  ? "bg-primary text-white rounded-br-sm"
                  : "bg-surface border border-border text-text-primary rounded-bl-sm"
              }
            `}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>
            </div>

            {/* Timestamp */}
            <div
              className={`text-xs text-text-secondary mt-1 ${
                isUser ? "text-right" : "text-left"
              }`}
            >
              {timestamp}
            </div>

            {/* Sources (only for assistant messages) */}
            {!isUser && message.sources && message.sources.length > 0 && (
              <div className="mt-3">
                <SourceCitation
                  sources={message.sources}
                  onSourceClick={onSourceClick}
                />
              </div>
            )}

            {/* Tool calls (only for assistant messages) */}
            {!isUser && message.toolCalls && message.toolCalls.length > 0 && (
              <div className="mt-3 space-y-2">
                {message.toolCalls.map((toolCall, index) => (
                  <div
                    key={index}
                    className="bg-background rounded-lg p-3 border border-border"
                  >
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-info rounded-full"></div>
                      <span className="text-sm font-medium text-text-primary">
                        {toolCall.tool_name}
                      </span>
                    </div>
                    {Object.keys(toolCall.args).length > 0 && (
                      <div className="mt-2 text-xs text-text-secondary">
                        <pre className="whitespace-pre-wrap">
                          {JSON.stringify(toolCall.args, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
