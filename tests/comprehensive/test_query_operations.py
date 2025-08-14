"""
Test suite completo per queries vettoriali e graph.
"""

import pytest
import asyncio
import logging
import json
import os
from uuid import UUID
from ingestion.embedder import create_embedder
from agent.db_utils import db_pool, vector_search
from ingestion.chunker import DocumentChunk

# Skip modulo se ambiente cloud non configurato
if not (
    os.getenv("DATABASE_URL")
):
    pytest.skip("Ambiente cloud non configurato: DATABASE_URL mancante", allow_module_level=True)

logger = logging.getLogger(__name__)

@pytest.fixture(scope="function")
async def default_tenant_id() -> UUID:
    """Ensure a default tenant exists and return its ID."""
    await db_pool.initialize()
    async with db_pool.acquire() as conn:
        tenant = await conn.fetchrow("SELECT id FROM accounts_tenant WHERE slug = 'default'")
        if tenant:
            return tenant['id']
        return await conn.fetchval("INSERT INTO accounts_tenant (name, slug) VALUES ('Default Tenant', 'default') RETURNING id")

class TestVectorQueries:
    @pytest.fixture(autouse=True)
    async def setup_teardown(self, default_tenant_id):
        self.tenant_id = default_tenant_id
        await self._create_test_data()
        yield
        await self._cleanup_test_data()

    async def _create_test_data(self):
        """Crea dati test per queries vettoriali."""
        from ingestion.chunker import DocumentChunk
        embedder = create_embedder()
        docs_data = [{"title": "AI Research", "chunks": ["AI focuses on machine learning.", "Deep learning is a subset of AI."]}]
        
        async with db_pool.acquire() as conn:
            for doc_data in docs_data:
                doc_result = await conn.fetchrow("INSERT INTO documents (tenant_id, title, source, content) VALUES ($1, $2, 'test.md', $3) RETURNING id", self.tenant_id, doc_data['title'], "")
                doc_id = doc_result['id']
                
                temp_chunks = [DocumentChunk(content=c, index=i, start_char=0, end_char=len(c), metadata={'test': True}) for i, c in enumerate(doc_data['chunks'])]
                embedded_chunks = await embedder.embed_chunks(temp_chunks)
                
                for chunk in embedded_chunks:
                    embedding_str = '[' + ','.join(map(str, chunk.embedding)) + ']'
                    await conn.execute("INSERT INTO chunks (tenant_id, document_id, content, embedding, chunk_index, metadata) VALUES ($1, $2, $3, $4::vector, $5, $6)", self.tenant_id, doc_id, chunk.content, embedding_str, chunk.index, json.dumps(chunk.metadata))

    async def _cleanup_test_data(self):
        """Pulisce dati test."""
        async with db_pool.acquire() as conn:
            await conn.execute("DELETE FROM chunks WHERE metadata->>'test' = 'true'")
            await conn.execute("DELETE FROM documents WHERE title = 'AI Research'")

    @pytest.mark.asyncio
    async def test_basic_vector_search(self):
        """Test ricerca vettoriale base."""
        embedder = create_embedder()
        from ingestion.chunker import DocumentChunk
        query_chunk = DocumentChunk(content="artificial intelligence", index=0, start_char=0, end_char=23, metadata={})
        embedded_query = await embedder.embed_chunks([query_chunk])
        
        results = await vector_search(self.tenant_id, embedded_query[0].embedding, limit=5)
        
        assert len(results) > 0
        assert "similarity" in results[0]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
