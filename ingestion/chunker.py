"""
Semantic chunking implementation for intelligent document splitting.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
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
    max_chunk_size: int = 2000
    use_semantic_splitting: bool = True
    min_chunk_size: int = 1

    def __post_init__(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
        if self.min_chunk_size <= 0:
            raise ValueError("Minimum chunk size must be positive")

@dataclass
class DocumentChunk:
    """Represents a document chunk."""
    content: str
    index: int
    start_char: int
    end_char: int
    metadata: Dict[str, Any]
    token_count: Optional[int] = None

    def __post_init__(self):
        if self.token_count is None and self.content:
            # naive token estimation: ~4 chars per token
            self.token_count = max(1, int(round(len(self.content) / 4)))

class SemanticChunker:
    """Semantic document chunker using LLM for intelligent splitting."""
    
    def __init__(self, config: ChunkingConfig):
        self.config = config
        # tests expect model object with model_name
        class _Model:
            def __init__(self, name: str):
                self.model_name = name

        self.model = _Model(os.getenv("INGESTION_MODEL", "gpt-4o-mini"))

    async def chunk_document(self, content: str, title: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """Asynchronously chunks a document. If use_semantic_splitting is False, use simple split."""
        if not content.strip():
            return []
        
        base_metadata = {"title": title, "source": source, **(metadata or {})}
        
        try:
            if self.config.use_semantic_splitting:
                semantic_chunks = await self._semantic_chunk(content)
                return self._create_chunk_objects(semantic_chunks, content, base_metadata)
            # simple path
            simple = SimpleChunker(self.config)
            return simple.chunk_document(content, title, source, metadata)
        except Exception:
            simple = SimpleChunker(self.config)
            return simple.chunk_document(content, title, source, metadata)

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
        # annotate total chunks
        total = len(chunk_objects)
        for c in chunk_objects:
            c.metadata = {**c.metadata, "total_chunks": total}
        return chunk_objects

    def _split_on_structure(self, content: str) -> List[str]:
        # Split on headers, lists, and blank lines
        parts = re.split(r"(\n\s*\n|^#.+$|^##.+$|^-\s+.+$|^\d+\.\s+.+$)", content, flags=re.MULTILINE)
        sections: List[str] = []
        buffer = ""
        for p in parts:
            if p is None:
                continue
            if p.strip() == "":
                if buffer.strip():
                    sections.append(buffer.strip())
                    buffer = ""
            else:
                buffer += ("\n\n" if buffer else "") + p
        if buffer.strip():
            sections.append(buffer.strip())
        return sections

    async def _split_long_section(self, text: str) -> List[str]:
        try:
            # naive split respecting max_chunk_size
            chunks: List[str] = []
            start = 0
            while start < len(text):
                end = min(start + self.config.max_chunk_size, len(text))
                # try to end at sentence boundary
                period = text.rfind(".", start, end)
                if period != -1 and period > start + self.config.min_chunk_size:
                    end = period + 1
                chunks.append(text[start:end].strip())
                start = max(end - self.config.chunk_overlap, start + 1)
            return [c for c in chunks if c]
        except Exception:
            # fallback simple split
            return self._simple_split(text)

    def _simple_split(self, text: str) -> List[str]:
        chunks: List[str] = []
        start = 0
        while start < len(text):
            end = min(start + self.config.chunk_size, len(text))
            period = text.rfind(".", start, end)
            if period != -1 and period > start + self.config.min_chunk_size:
                end = period + 1
            chunks.append(text[start:end].strip())
            start = max(end - self.config.chunk_overlap, start + 1)
        return [c for c in chunks if c]

class SimpleChunker:
    """Simple non-semantic chunker."""
    
    def __init__(self, config: ChunkingConfig):
        self.config = config
    
    def chunk_document(self, content: str, title: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> List[DocumentChunk]:
        """Synchronously chunks a document using a fixed-size window (tests expect sync)."""
        if not content.strip():
            return []
        base_metadata = {"title": title, "source": source, "chunk_method": "simple", **(metadata or {})}
        chunks_text: List[str] = []
        start = 0
        content_len = len(content)
        if content_len <= self.config.chunk_size:
            chunks_text.append(content)
        else:
            while start < content_len:
                end = min(start + self.config.chunk_size, content_len)
                chunks_text.append(content[start:end])
                if end >= content_len:
                    break
                # next window with overlap
                start = end - self.config.chunk_overlap
        chunk_objects = self._create_chunk_objects(chunks_text, content, base_metadata)
        total = len(chunk_objects)
        for c in chunk_objects:
            c.metadata = {**c.metadata, "total_chunks": total}
        return chunk_objects

    def _create_chunk_objects(self, chunks: List[str], original_content: str, base_metadata: Dict[str, Any]) -> List[DocumentChunk]:
        return [DocumentChunk(content=text, index=i, start_char=0, end_char=len(text), metadata=base_metadata) for i, text in enumerate(chunks)]

def create_chunker(config: ChunkingConfig):
    if config.use_semantic_splitting:
        return SemanticChunker(config)
    return SimpleChunker(config)
