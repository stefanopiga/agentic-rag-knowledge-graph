"""
Test offline per EmbeddingGenerator con EMBEDDINGS_OFFLINE=1.
"""

import os
import pytest
import asyncio

from ingestion.embedder import create_embedder
from ingestion.chunker import DocumentChunk

# Imposta modalità offline e modello/dimensione coerenti
os.environ.setdefault("EMBEDDINGS_OFFLINE", "1")
os.environ.setdefault("EMBEDDING_MODEL", "text-embedding-3-small")
os.environ.setdefault("VECTOR_DIMENSION", "1536")

# Compatibilità asincrona Windows se eseguito standalone
if os.name == "nt":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass


@pytest.mark.asyncio
async def test_embed_query_offline_dimension():
    embedder = create_embedder()
    vec = await embedder.embed_query("test query")
    assert isinstance(vec, list)
    assert len(vec) == embedder.get_embedding_dimension() == 1536


@pytest.mark.asyncio
async def test_embed_chunks_offline_dimension_and_count():
    embedder = create_embedder()

    chunks = [
        DocumentChunk(content="alpha", index=0, start_char=0, end_char=5, metadata={}, token_count=1),
        DocumentChunk(content="beta", index=1, start_char=0, end_char=4, metadata={}, token_count=1),
        DocumentChunk(content="gamma", index=2, start_char=0, end_char=5, metadata={}, token_count=1),
    ]

    embedded = await embedder.embed_chunks(chunks)

    assert len(embedded) == 3
    for c in embedded:
        assert hasattr(c, "embedding")
        assert isinstance(c.embedding, list)
        assert len(c.embedding) == 1536
