"""
Semantic chunking implementation for intelligent document splitting.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

try:
    from agent.providers import get_embedding_client, get_ingestion_model
except (ImportError, ValueError):
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent.providers import get_embedding_client, get_ingestion_model

embedding_client = get_embedding_client()
ingestion_model = get_ingestion_model()


@dataclass
class ChunkingConfig:
    """Configuration for chunking."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    use_semantic_splitting: bool = True

@dataclass
class DocumentChunk:
    """Represents a document chunk."""
    content: str
    index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]
    token_count: Optional[int] = None

class SemanticChunker:
    """Semantic document chunker using LLM for intelligent splitting."""
    
    def __init__(self, config: ChunkingConfig):
        self.config = config

    async def chunk_document(self, content: str, title: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """Asynchronously chunks a document using semantic splitting."""
        if not content.strip():
            return []
        
        base_metadata = {"title": title, "source": source, **(metadata or {})}
        
        semantic_chunks = await self._semantic_chunk(content)
        return self._create_chunk_objects(semantic_chunks, content, base_metadata)

    async def _semantic_chunk(self, content: str) -> List[str]:
        # Simplified semantic chunking logic
        sections = re.split(r'\n\s*\n', content)
        return [section for section in sections if section.strip()]
    
    def _create_chunk_objects(self, chunks: List[str], original_content: str, base_metadata: Dict[str, Any]) -> List[DocumentChunk]:
        chunk_objects = []
        current_pos = 0
        for i, chunk_text in enumerate(chunks):
            start_pos = original_content.find(chunk_text, current_pos)
            if start_pos == -1:
                start_pos = current_pos
            
            end_pos = start_pos + len(chunk_text)
            chunk_metadata = {**base_metadata, "chunk_method": "semantic"}
            
            chunk_objects.append(DocumentChunk(
                content=chunk_text.strip(),
                index=i,
                start_char=start_pos,
                end_char=end_pos,
                metadata=chunk_metadata
            ))
            current_pos = end_pos
        return chunk_objects

class SimpleChunker:
    """Simple non-semantic chunker."""
    
    def __init__(self, config: ChunkingConfig):
        self.config = config
    
    async def chunk_document(self, content: str, title: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """Asynchronously chunks a document using a fixed-size window."""
        if not content.strip():
            return []
        
        base_metadata = {"title": title, "source": source, "chunk_method": "simple", **(metadata or {})}
        
        chunks_text = []
        start = 0
        while start < len(content):
            end = start + self.config.chunk_size
            chunks_text.append(content[start:end])
            start = end - self.config.chunk_overlap

        return self._create_chunk_objects(chunks_text, content, base_metadata)

    def _create_chunk_objects(self, chunks: List[str], original_content: str, base_metadata: Dict[str, Any]) -> List[DocumentChunk]:
        return [DocumentChunk(content=text, index=i, start_char=0, end_char=len(text), metadata=base_metadata) for i, text in enumerate(chunks)]

def create_chunker(config: ChunkingConfig):
    if config.use_semantic_splitting:
        return SemanticChunker(config)
    else:
        return SimpleChunker(config)
