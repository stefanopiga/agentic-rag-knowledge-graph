import React from "react";
import type { SourceCitationProps } from "@/types/chat";

export const SourceCitation: React.FC<SourceCitationProps> = ({ 
  sources, 
  onSourceClick 
}) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="text-xs font-medium text-text-secondary uppercase tracking-wider">
        Fonti ({sources.length})
      </div>
      <div className="space-y-2">
        {sources.map((source, index) => (
          <div
            key={index}
            className={`
              bg-background border border-border rounded-lg p-3 text-sm
              ${onSourceClick ? "cursor-pointer hover:border-primary hover:bg-primary/5 transition-colors" : ""}
            `}
            onClick={() => onSourceClick?.(source)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="font-medium text-text-primary mb-1">
                  {source.title}
                  {source.page && (
                    <span className="text-text-secondary ml-1">
                      (Pagina {source.page})
                    </span>
                  )}
                </div>
                <div className="text-text-secondary text-xs mb-2 line-clamp-3">
                  {source.excerpt}
                </div>
              </div>
              <div className="ml-3 flex-shrink-0">
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-success rounded-full"></div>
                  <span className="text-xs text-text-secondary">
                    {(source.relevanceScore * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
            
            {onSourceClick && (
              <div className="mt-2 flex items-center text-xs text-primary">
                <svg 
                  className="w-3 h-3 mr-1" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Visualizza fonte
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
