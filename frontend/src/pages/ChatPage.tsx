import React, { useState } from "react";
import { ChatInterface } from "@/components/chat";
import { Modal } from "@/components/ui";
import type { Source } from "@/types/api";

export const ChatPage: React.FC = () => {
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [isSourceModalOpen, setIsSourceModalOpen] = useState(false);

  const handleSourceClick = (source: Source) => {
    setSelectedSource(source);
    setIsSourceModalOpen(true);
  };

  const closeSourceModal = () => {
    setIsSourceModalOpen(false);
    setSelectedSource(null);
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <ChatInterface onSourceClick={handleSourceClick} />
      
      {/* Source Detail Modal */}
      <Modal
        isOpen={isSourceModalOpen}
        onClose={closeSourceModal}
        title="Dettagli Fonte"
        size="lg"
      >
        {selectedSource && (
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-text-primary mb-2">
                {selectedSource.title}
              </h4>
              {selectedSource.page && (
                <p className="text-sm text-text-secondary mb-3">
                  Pagina {selectedSource.page}
                </p>
              )}
            </div>
            
            <div>
              <h5 className="font-medium text-text-primary mb-2">Estratto:</h5>
              <div className="bg-background rounded-lg p-4 border border-border">
                <p className="text-text-secondary whitespace-pre-wrap">
                  {selectedSource.excerpt}
                </p>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm text-text-secondary">Rilevanza:</span>
                <div className="flex items-center space-x-2 mt-1">
                  <div className="w-full bg-border rounded-full h-2 max-w-xs">
                    <div 
                      className="bg-success h-2 rounded-full transition-all"
                      style={{ width: `${selectedSource.relevanceScore * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-text-primary">
                    {(selectedSource.relevanceScore * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
