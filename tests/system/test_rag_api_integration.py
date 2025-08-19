import pytest
import uuid
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport


class TestRAGAPIIntegration:
    """Integration tests for RAG API endpoints with tenant isolation."""

    @pytest.mark.asyncio
    async def test_vector_search_tool_offline_execution(self, monkeypatch):
        """Test vector_search_tool executes with offline embeddings and tenant_id."""
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        
        from agent.tools import vector_search_tool, VectorSearchInput
        
        tenant_id = uuid.uuid4()
        input_data = VectorSearchInput(query="test query", limit=5)
        results = await vector_search_tool(input_data, tenant_id)
        
        # Verify it executes without error and returns expected format
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_hybrid_search_tool_offline_execution(self, monkeypatch):
        """Test hybrid_search_tool executes with offline embeddings and tenant_id."""
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        
        from agent.tools import hybrid_search_tool, HybridSearchInput
        
        tenant_id = uuid.uuid4()
        input_data = HybridSearchInput(query="test query", limit=10, text_weight=0.3)
        results = await hybrid_search_tool(input_data, tenant_id)
        
        # Verify it executes without error and returns expected format
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_endpoints_tenant_validation(self, monkeypatch):
        """Test search endpoints handle invalid tenant_id properly."""
        # Setup environment
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("ENABLE_METRICS", "false")
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")

        from agent.api import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test vector search with invalid tenant_id
            resp = await client.post("/search/vector", json={
                "query": "test query",
                "tenant_id": "invalid-uuid",
                "limit": 5
            })
            assert resp.status_code == 422  # Validation error
            
            # Test hybrid search with invalid tenant_id
            resp = await client.post("/search/hybrid", json={
                "query": "test query", 
                "tenant_id": "invalid-uuid",
                "limit": 5
            })
            assert resp.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_rag_functions_parameter_signature_compliance(self, monkeypatch):
        """Test that RAG functions comply with tenant-first parameter signature."""
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        
        from agent.db_utils import match_chunks, hybrid_search
        import inspect
        
        # Verify match_chunks signature: tenant_id is first parameter
        match_chunks_sig = inspect.signature(match_chunks)
        params = list(match_chunks_sig.parameters.keys())
        assert params[0] == 'tenant_id', f"match_chunks first parameter should be tenant_id, got {params[0]}"
        
        # Verify hybrid_search signature: tenant_id is first parameter
        hybrid_search_sig = inspect.signature(hybrid_search)
        params = list(hybrid_search_sig.parameters.keys())
        assert params[0] == 'tenant_id', f"hybrid_search first parameter should be tenant_id, got {params[0]}"


