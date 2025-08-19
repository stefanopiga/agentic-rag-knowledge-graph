"""
Integration tests for RAG tenant isolation in API layer.

Tests to verify that all RAG calls from agent/api.py properly pass tenant_id
and enforce tenant isolation across vector search, hybrid search, and graph operations.
"""

import pytest
import uuid
import json
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient

from agent.models import ChatRequest, SearchRequest


class TestRAGTenantIsolationIntegration:
    """Integration tests for RAG API endpoints with tenant isolation."""
    
    @pytest.fixture
    def test_tenant_id(self):
        """Generate a test tenant ID."""
        return uuid.uuid4()
    
    @pytest.fixture  
    def other_tenant_id(self):
        """Generate a different tenant ID for isolation tests."""
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_vector_search_endpoint_tenant_isolation(self, monkeypatch, test_tenant_id):
        """Test /search/vector endpoint properly passes tenant_id to tools."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        monkeypatch.setenv("DISABLE_DB_PERSISTENCE", "true")
        
        from agent.api import app
        from agent.tools import vector_search_tool
        
        # Mock vector_search_tool to capture calls
        original_tool = vector_search_tool
        call_log = []
        
        async def mock_vector_search_tool(input_data, tenant_id):
            call_log.append({
                'input_data': input_data,
                'tenant_id': tenant_id,
                'tenant_id_type': type(tenant_id)
            })
            return []
        
        with patch('agent.api.vector_search_tool', side_effect=mock_vector_search_tool):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/search/vector", json={
                    "query": "test query",
                    "tenant_id": str(test_tenant_id),
                    "limit": 5
                })
                
                assert response.status_code == 200
                assert len(call_log) == 1
                assert call_log[0]['tenant_id'] == test_tenant_id
                assert call_log[0]['input_data'].query == "test query"
                assert call_log[0]['input_data'].limit == 5

    @pytest.mark.asyncio
    async def test_hybrid_search_endpoint_tenant_isolation(self, monkeypatch, test_tenant_id):
        """Test /search/hybrid endpoint properly passes tenant_id to tools."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        monkeypatch.setenv("DISABLE_DB_PERSISTENCE", "true")
        
        from agent.api import app
        from agent.tools import hybrid_search_tool
        
        call_log = []
        
        async def mock_hybrid_search_tool(input_data, tenant_id):
            call_log.append({
                'input_data': input_data,
                'tenant_id': tenant_id,
                'tenant_id_type': type(tenant_id)
            })
            return []
        
        with patch('agent.api.hybrid_search_tool', side_effect=mock_hybrid_search_tool):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/search/hybrid", json={
                    "query": "test query",
                    "tenant_id": str(test_tenant_id),
                    "limit": 10
                })
                
                assert response.status_code == 200
                assert len(call_log) == 1
                assert call_log[0]['tenant_id'] == test_tenant_id
                assert call_log[0]['input_data'].query == "test query"
                assert call_log[0]['input_data'].limit == 10

    @pytest.mark.asyncio
    async def test_graph_search_endpoint_tenant_isolation(self, monkeypatch, test_tenant_id):
        """Test /search/graph endpoint properly passes tenant_id to tools."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        monkeypatch.setenv("DISABLE_DB_PERSISTENCE", "true")
        
        from agent.api import app
        from agent.tools import graph_search_tool
        
        call_log = []
        
        async def mock_graph_search_tool(input_data, tenant_id):
            call_log.append({
                'input_data': input_data,
                'tenant_id': tenant_id,
                'tenant_id_type': type(tenant_id)
            })
            return []
        
        with patch('agent.api.graph_search_tool', side_effect=mock_graph_search_tool):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/search/graph", json={
                    "query": "test query",
                    "tenant_id": str(test_tenant_id)
                })
                
                assert response.status_code == 200
                assert len(call_log) == 1
                assert call_log[0]['tenant_id'] == test_tenant_id
                assert call_log[0]['input_data'].query == "test query"

    @pytest.mark.asyncio
    async def test_chat_endpoint_tenant_propagation(self, monkeypatch, test_tenant_id):
        """Test /chat endpoint propagates tenant_id through agent execution."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        monkeypatch.setenv("DISABLE_DB_PERSISTENCE", "true")
        
        from agent.api import app
        from agent.agent import rag_agent
        
        call_log = []
        
        # Mock the agent to capture tenant_id from dependencies
        async def mock_agent_run(prompt, deps):
            call_log.append({
                'prompt': prompt,
                'tenant_id': deps.tenant_id,
                'session_id': deps.session_id,
                'user_id': deps.user_id
            })
            # Return mock result
            mock_result = MagicMock()
            mock_result.data = "Mock response"
            mock_result.all_messages.return_value = []
            return mock_result
        
        with patch.object(rag_agent, 'run', side_effect=mock_agent_run):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/chat", json={
                    "message": "test message",
                    "tenant_id": str(test_tenant_id),
                    "user_id": "test-user"
                })
                
                assert response.status_code == 200
                assert len(call_log) == 1
                assert call_log[0]['tenant_id'] == str(test_tenant_id)
                assert call_log[0]['user_id'] == "test-user"

    @pytest.mark.asyncio
    async def test_chat_stream_endpoint_tenant_propagation(self, monkeypatch, test_tenant_id):
        """Test /chat/stream endpoint propagates tenant_id through agent execution."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        monkeypatch.setenv("DISABLE_DB_PERSISTENCE", "true")
        
        from agent.api import app
        from agent.agent import rag_agent
        
        call_log = []
        
        # Mock the streaming agent context manager
        class MockIterContext:
            def __init__(self, prompt, deps):
                call_log.append({
                    'prompt': prompt,
                    'tenant_id': deps.tenant_id,
                    'session_id': deps.session_id,
                    'user_id': deps.user_id
                })
                # Mock result
                self.result = MagicMock()
                self.result.data = "Mock streaming response"
                self.result.all_messages.return_value = []
                
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
            async def __aiter__(self):
                return self
                
            async def __anext__(self):
                raise StopAsyncIteration
        
        def mock_agent_iter(prompt, deps):
            return MockIterContext(prompt, deps)
        
        with patch.object(rag_agent, 'iter', side_effect=mock_agent_iter):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/chat/stream", json={
                    "message": "test streaming message", 
                    "tenant_id": str(test_tenant_id),
                    "user_id": "test-user"
                })
                
                assert response.status_code == 200
                assert len(call_log) == 1
                assert call_log[0]['tenant_id'] == str(test_tenant_id)
                assert call_log[0]['user_id'] == "test-user"

    @pytest.mark.asyncio
    async def test_tenant_isolation_different_tenants(self, monkeypatch, test_tenant_id, other_tenant_id):
        """Test that different tenants get different data and isolation is enforced."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        monkeypatch.setenv("DISABLE_DB_PERSISTENCE", "true")
        
        from agent.api import app
        
        call_log = []
        
        async def mock_vector_search_tool(input_data, tenant_id):
            call_log.append({
                'query': input_data.query,
                'tenant_id': tenant_id
            })
            # Return different results based on tenant as ChunkResult objects
            from agent.models import ChunkResult
            if tenant_id == test_tenant_id:
                return [ChunkResult(
                    content=f"Result for tenant {tenant_id}", 
                    score=0.9, 
                    chunk_id="test-1", 
                    document_id="doc-1",
                    document_title="Test Document 1",
                    document_source="test-source-1"
                )]
            else:
                return [ChunkResult(
                    content=f"Different result for tenant {tenant_id}", 
                    score=0.8, 
                    chunk_id="test-2", 
                    document_id="doc-2",
                    document_title="Test Document 2", 
                    document_source="test-source-2"
                )]
        
        with patch('agent.api.vector_search_tool', side_effect=mock_vector_search_tool):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Search for first tenant
                response1 = await client.post("/search/vector", json={
                    "query": "same query",
                    "tenant_id": str(test_tenant_id),
                    "limit": 5
                })
                
                # Search for second tenant
                response2 = await client.post("/search/vector", json={
                    "query": "same query",
                    "tenant_id": str(other_tenant_id),
                    "limit": 5
                })
                
                assert response1.status_code == 200
                assert response2.status_code == 200
                
                # Verify both tenants called with correct tenant_id
                assert len(call_log) == 2
                assert call_log[0]['tenant_id'] == test_tenant_id
                assert call_log[1]['tenant_id'] == other_tenant_id
                
                # Verify both got same query but different tenant_id
                assert call_log[0]['query'] == "same query"
                assert call_log[1]['query'] == "same query"

    @pytest.mark.asyncio
    async def test_invalid_tenant_id_handling(self, monkeypatch):
        """Test API handles invalid tenant_id formats gracefully."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        monkeypatch.setenv("DISABLE_DB_PERSISTENCE", "true")
        
        from agent.api import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test various invalid tenant_id formats
            invalid_tenant_ids = [
                "not-a-uuid",
                "",
                "12345",
                "invalid-uuid-format"
            ]
            
            for invalid_id in invalid_tenant_ids:
                response = await client.post("/search/vector", json={
                    "query": "test query",
                    "tenant_id": invalid_id,
                    "limit": 5
                })
                
                # Should return validation error
                assert response.status_code == 422, f"Invalid tenant_id {invalid_id} should return 422"

    @pytest.mark.asyncio
    async def test_missing_tenant_id_handling(self, monkeypatch):
        """Test API handles missing tenant_id properly."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        monkeypatch.setenv("DISABLE_DB_PERSISTENCE", "true")
        
        from agent.api import app
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test missing tenant_id in search endpoints (these require tenant_id)
            search_endpoints_and_payloads = [
                ("/search/vector", {"query": "test", "limit": 5}),
                ("/search/hybrid", {"query": "test", "limit": 5}),
                ("/search/graph", {"query": "test"}),
            ]
            
            for endpoint, payload in search_endpoints_and_payloads:
                response = await client.post(endpoint, json=payload)
                # Should return validation error for missing tenant_id
                assert response.status_code == 422, f"Endpoint {endpoint} should require tenant_id"
            
            # Test chat endpoints (these have default tenant_id, so should work)
            chat_endpoints_and_payloads = [
                ("/chat", {"message": "test", "user_id": "test-user"}),
                ("/chat/stream", {"message": "test", "user_id": "test-user"})
            ]
            
            for endpoint, payload in chat_endpoints_and_payloads:
                response = await client.post(endpoint, json=payload)
                # Should work with default tenant_id
                assert response.status_code == 200, f"Endpoint {endpoint} should work with default tenant_id"

    @pytest.mark.asyncio  
    async def test_db_utils_integration_with_stored_procedures(self, monkeypatch, test_tenant_id):
        """Test that db_utils functions are called with correct tenant_id for stored procedures."""
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        
        call_log = []
        
        # Mock the underlying stored procedure calls in tools.py directly
        async def mock_match_chunks(tenant_id, embedding, limit):
            call_log.append({
                'function': 'match_chunks',
                'tenant_id': tenant_id,
                'tenant_id_type': type(tenant_id),
                'embedding_length': len(embedding),
                'limit': limit
            })
            return []
        
        async def mock_hybrid_search(tenant_id, embedding, query_text, limit, text_weight):
            call_log.append({
                'function': 'hybrid_search', 
                'tenant_id': tenant_id,
                'tenant_id_type': type(tenant_id),
                'embedding_length': len(embedding),
                'query_text': query_text,
                'limit': limit,
                'text_weight': text_weight
            })
            return []
        
        # Mock embedding generation to avoid actual API calls
        async def mock_generate_embedding(text, tenant_id=None):
            return [0.1] * 1536
        
        with patch('agent.tools.match_chunks', side_effect=mock_match_chunks), \
             patch('agent.tools.hybrid_search', side_effect=mock_hybrid_search), \
             patch('agent.tools.generate_embedding', side_effect=mock_generate_embedding):
            
            from agent.tools import match_chunks_tool, hybrid_search_tool, VectorSearchInput, HybridSearchInput
            
            # Test match_chunks_tool
            input_data = VectorSearchInput(query="test query", limit=5)
            await match_chunks_tool(input_data, test_tenant_id)
            
            # Test hybrid_search_tool
            hybrid_input = HybridSearchInput(query="test query", limit=10, text_weight=0.3)
            await hybrid_search_tool(hybrid_input, test_tenant_id)
            
            # Verify calls
            assert len(call_log) == 2
            
            # Check match_chunks call
            match_call = call_log[0]
            assert match_call['function'] == 'match_chunks'
            assert match_call['tenant_id'] == test_tenant_id
            assert match_call['tenant_id_type'] == uuid.UUID
            assert match_call['limit'] == 5
            
            # Check hybrid_search call
            hybrid_call = call_log[1]
            assert hybrid_call['function'] == 'hybrid_search'
            assert hybrid_call['tenant_id'] == test_tenant_id
            assert hybrid_call['tenant_id_type'] == uuid.UUID
            assert hybrid_call['query_text'] == "test query"
            assert hybrid_call['limit'] == 10
            assert hybrid_call['text_weight'] == 0.3