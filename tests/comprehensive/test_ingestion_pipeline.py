"""
Test suite completo per pipeline di ingestion.
"""

import pytest
import asyncio
import logging
import os
import tempfile
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from uuid import uuid4, UUID

from ingestion.ingest import DocumentIngestionPipeline
from ingestion.chunker import DocumentChunk, ChunkingConfig, create_chunker
from agent.models import IngestionConfig, IngestionResult
from agent.db_utils import db_pool
from agent.graph_utils import graph_client

logger = logging.getLogger(__name__)

@pytest.fixture(scope="function")
async def default_tenant_id() -> UUID:
    """Ensure a default tenant exists and return its ID."""
    async with db_pool.acquire() as conn:
        tenant = await conn.fetchrow("SELECT id FROM accounts_tenant WHERE slug = 'default'")
        if tenant:
            return tenant['id']
        return await conn.fetchval("INSERT INTO accounts_tenant (name, slug) VALUES ('Default Tenant', 'default') RETURNING id")

class TestDocumentProcessing:
    @pytest.fixture(autouse=True)
    async def setup_teardown(self):
        yield
        await self._cleanup_test_data()

    async def _cleanup_test_data(self):
        try:
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM chunks WHERE metadata->>'test_marker' = 'true'")
                await conn.execute("DELETE FROM documents WHERE title LIKE 'PIPELINE_TEST_%'")
        except Exception as e:
            logger.warning(f"Test cleanup failed: {e}")

    @pytest.fixture
    def temp_documents_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "test_markdown.md").write_text("# Test Document\n\nThis is a sufficiently long content section for testing purposes, ensuring that even with semantic chunking, it produces at least one valid output chunk.", encoding="utf-8")
            yield temp_dir

    @pytest.mark.asyncio
    async def test_markdown_document_processing(self, temp_documents_dir, default_tenant_id):
        config = IngestionConfig(chunk_size=100, chunk_overlap=20, skip_graph_building=True)
        pipeline = DocumentIngestionPipeline(config=config, documents_folder=temp_documents_dir)
        
        file_path = os.path.join(temp_documents_dir, "test_markdown.md")
        result = await pipeline._ingest_single_document(file_path, default_tenant_id)
        
        assert isinstance(result, IngestionResult)
        assert result.title == "test markdown"
        assert result.success
        assert result.chunks_created > 0

class TestChunkingStrategies:
    @pytest.fixture
    def sample_content(self):
        return "This is a much longer sample sentence for testing the chunking mechanism, ensuring it is long enough to be split into multiple parts based on a smaller chunk size."

    @pytest.mark.asyncio
    async def test_fixed_size_chunking(self, sample_content):
        config = ChunkingConfig(chunk_size=50, chunk_overlap=10, use_semantic_splitting=False)
        chunker = create_chunker(config)
        # Simple strategy: chunk_document sincrono
        chunks = chunker.chunk_document(content=sample_content, title="Test", source="test.md")
        assert len(chunks) > 1

class TestFullPipeline:
    @pytest.fixture
    def full_test_documents_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, "doc1.md").write_text("# AI Research\n\nArtificial intelligence is a branch of computer science that deals with the creation of intelligent agents, which are systems that can reason, learn, and act autonomously. This field is vast and includes many sub-fields.", encoding="utf-8")
            Path(temp_dir, "doc2.txt").write_text("Technology Companies\n\nMany large technology companies are investing heavily in AI. This includes research and development in areas like machine learning, natural language processing, and computer vision. These efforts are driving innovation across the industry.", encoding="utf-8")
            yield temp_dir

    @pytest.mark.asyncio
    async def test_complete_pipeline_run(self, full_test_documents_dir, default_tenant_id):
        config = IngestionConfig(chunk_size=150, chunk_overlap=30, skip_graph_building=True, use_semantic_chunking=False)
        pipeline = DocumentIngestionPipeline(config=config, documents_folder=full_test_documents_dir)
        
        results = await pipeline.ingest_documents(tenant_slug='default')
        
        logger.info(f"Ingestion results: {results}")
        
        assert len(results) == 2
        assert all(r.success and r.chunks_created > 0 for r in results), f"One or more documents failed ingestion or produced no chunks. Results: {results}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
