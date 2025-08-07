import React from "react";
import type { TypingIndicatorProps } from "@/types/chat";

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  isVisible,
}) => {
  if (!isVisible) return null;

  return (
    <div className="flex justify-start mb-4">
      <div className="flex items-start space-x-3">
        {/* AI Avatar */}
        <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-white text-sm font-medium">
          AI
        </div>

        <div className="bg-surface border border-border rounded-2xl rounded-bl-sm px-4 py-3">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-text-secondary rounded-full animate-bounce"></div>
            <div
              className="w-2 h-2 bg-text-secondary rounded-full animate-bounce"
              style={{ animationDelay: "0.1s" }}
            ></div>
            <div
              className="w-2 h-2 bg-text-secondary rounded-full animate-bounce"
              style={{ animationDelay: "0.2s" }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
};
