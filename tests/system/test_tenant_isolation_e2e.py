"""
End-to-End tests for tenant isolation in RAG system.

Tests the complete flow from API endpoints through tools to database functions
to verify tenant_id is properly propagated and tenant isolation is enforced.
"""

import pytest
import uuid
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from agent.db_utils import match_chunks, hybrid_search
from agent.tools import vector_search_tool, hybrid_search_tool, VectorSearchInput, HybridSearchInput
from agent.models import ChatRequest, SearchRequest


class TestTenantIsolationEndToEnd:
    """End-to-end tests for tenant isolation across the entire RAG pipeline."""
    
    @pytest.fixture
    def tenant_a_id(self):
        """Generate tenant A ID."""
        return uuid.uuid4()
    
    @pytest.fixture  
    def tenant_b_id(self):
        """Generate tenant B ID."""
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_api_to_database_tenant_propagation_vector_search(self, monkeypatch, tenant_a_id, tenant_b_id):
        """Test complete flow from /search/vector API to database with tenant isolation."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        monkeypatch.setenv("DISABLE_DB_PERSISTENCE", "true")
        
        # Track calls through the entire stack
        call_stack = []
        
        # Mock embedding generation
        async def mock_generate_embedding(text, tenant_id=None):
            call_stack.append({
                'layer': 'embedding',
                'tenant_id': tenant_id,
                'text': text
            })
            return [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        
        # Mock match_chunks at the database layer
        async def mock_match_chunks(tenant_id, embedding, limit):
            call_stack.append({
                'layer': 'database',
                'function': 'match_chunks',
                'tenant_id': tenant_id,
                'tenant_id_type': type(tenant_id),
                'limit': limit,
                'embedding_length': len(embedding)
            })
            
            # Return different results based on tenant
            if tenant_id == tenant_a_id:
                return [{"content": f"Tenant A result for {tenant_id}", "score": 0.9}]
            else:
                return [{"content": f"Tenant B result for {tenant_id}", "score": 0.8}]
        
        with patch('agent.tools.generate_embedding', side_effect=mock_generate_embedding), \
             patch('agent.db_utils.match_chunks', side_effect=mock_match_chunks):
            
            from agent.api import app
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Test Tenant A
                response_a = await client.post("/search/vector", json={
                    "query": "test query",
                    "tenant_id": str(tenant_a_id),
                    "limit": 5
                })
                
                # Test Tenant B
                response_b = await client.post("/search/vector", json={
                    "query": "test query",
                    "tenant_id": str(tenant_b_id),
                    "limit": 5
                })
                
                # Verify responses
                assert response_a.status_code == 200
                assert response_b.status_code == 200
                
                # Verify call stack
                assert len(call_stack) == 4  # 2 embedding calls + 2 database calls
                
                # Check embedding calls
                embedding_calls = [c for c in call_stack if c['layer'] == 'embedding']
                assert len(embedding_calls) == 2
                assert embedding_calls[0]['tenant_id'] == str(tenant_a_id)
                assert embedding_calls[1]['tenant_id'] == str(tenant_b_id)
                
                # Check database calls
                db_calls = [c for c in call_stack if c['layer'] == 'database']
                assert len(db_calls) == 2
                assert db_calls[0]['tenant_id'] == tenant_a_id
                assert db_calls[1]['tenant_id'] == tenant_b_id
                assert all(c['tenant_id_type'] == uuid.UUID for c in db_calls)

    @pytest.mark.asyncio
    async def test_api_to_database_tenant_propagation_hybrid_search(self, monkeypatch, tenant_a_id, tenant_b_id):
        """Test complete flow from /search/hybrid API to database with tenant isolation."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        monkeypatch.setenv("DISABLE_DB_PERSISTENCE", "true")
        
        call_stack = []
        
        # Mock embedding generation
        async def mock_generate_embedding(text, tenant_id=None):
            call_stack.append({
                'layer': 'embedding',
                'tenant_id': tenant_id,
                'text': text
            })
            return [0.1, 0.2, 0.3] * 512
        
        # Mock hybrid_search at the database layer
        async def mock_hybrid_search(tenant_id, embedding, query_text, limit, text_weight):
            call_stack.append({
                'layer': 'database',
                'function': 'hybrid_search',
                'tenant_id': tenant_id,
                'tenant_id_type': type(tenant_id),
                'query_text': query_text,
                'limit': limit,
                'text_weight': text_weight,
                'embedding_length': len(embedding)
            })
            
            # Return different results based on tenant
            if tenant_id == tenant_a_id:
                return [{"content": f"Tenant A hybrid result for {tenant_id}", "score": 0.95}]
            else:
                return [{"content": f"Tenant B hybrid result for {tenant_id}", "score": 0.85}]
        
        with patch('agent.tools.generate_embedding', side_effect=mock_generate_embedding), \
             patch('agent.db_utils.hybrid_search', side_effect=mock_hybrid_search):
            
            from agent.api import app
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Test Tenant A
                response_a = await client.post("/search/hybrid", json={
                    "query": "hybrid test query",
                    "tenant_id": str(tenant_a_id),
                    "limit": 8
                })
                
                # Test Tenant B  
                response_b = await client.post("/search/hybrid", json={
                    "query": "hybrid test query",
                    "tenant_id": str(tenant_b_id),
                    "limit": 8
                })
                
                # Verify responses
                assert response_a.status_code == 200
                assert response_b.status_code == 200
                
                # Verify call stack
                assert len(call_stack) == 4  # 2 embedding calls + 2 database calls
                
                # Check database calls
                db_calls = [c for c in call_stack if c['layer'] == 'database']
                assert len(db_calls) == 2
                
                # Verify tenant isolation
                assert db_calls[0]['tenant_id'] == tenant_a_id
                assert db_calls[1]['tenant_id'] == tenant_b_id
                assert db_calls[0]['query_text'] == "hybrid test query"
                assert db_calls[1]['query_text'] == "hybrid test query"
                assert all(c['limit'] == 8 for c in db_calls)
                assert all(c['tenant_id_type'] == uuid.UUID for c in db_calls)

    @pytest.mark.asyncio
    async def test_chat_endpoint_tenant_isolation_e2e(self, monkeypatch, tenant_a_id):
        """Test /chat endpoint maintains tenant isolation through agent execution."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        monkeypatch.setenv("DISABLE_DB_PERSISTENCE", "true")
        
        call_stack = []
        
        # Mock all RAG tools to track tenant_id propagation
        async def mock_vector_search_tool(input_data, tenant_id):
            call_stack.append({
                'tool': 'vector_search',
                'tenant_id': tenant_id,
                'query': input_data.query
            })
            return []
        
        async def mock_hybrid_search_tool(input_data, tenant_id):
            call_stack.append({
                'tool': 'hybrid_search',
                'tenant_id': tenant_id,
                'query': input_data.query
            })
            return []
        
        async def mock_graph_search_tool(input_data, tenant_id):
            call_stack.append({
                'tool': 'graph_search',
                'tenant_id': tenant_id,
                'query': input_data.query
            })
            return []
        
        # Mock the agent to trigger tool usage
        async def mock_agent_run(prompt, deps):
            # Simulate agent calling tools with dependencies
            from agent.tools import VectorSearchInput, HybridSearchInput, GraphSearchInput
            
            # Simulate tools being called with correct tenant_id
            await mock_vector_search_tool(
                VectorSearchInput(query="test query", limit=5),
                deps.tenant_id
            )
            await mock_hybrid_search_tool(
                HybridSearchInput(query="test query", limit=5, text_weight=0.3),
                deps.tenant_id
            )
            
            mock_result = MagicMock()
            mock_result.data = "Agent response with tenant isolation"
            mock_result.all_messages.return_value = []
            return mock_result
        
        with patch('agent.tools.vector_search_tool', side_effect=mock_vector_search_tool), \
             patch('agent.tools.hybrid_search_tool', side_effect=mock_hybrid_search_tool), \
             patch('agent.tools.graph_search_tool', side_effect=mock_graph_search_tool):
            
            from agent.api import app
            from agent.agent import rag_agent
            
            with patch.object(rag_agent, 'run', side_effect=mock_agent_run):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    response = await client.post("/chat", json={
                        "message": "Tell me about tenant isolation",
                        "tenant_id": str(tenant_a_id),
                        "user_id": "test-user"
                    })
                    
                    assert response.status_code == 200
                    
                    # Verify tools were called with correct tenant_id
                    assert len(call_stack) == 2  # vector + hybrid tools called
                    
                    vector_call = next(c for c in call_stack if c['tool'] == 'vector_search')
                    hybrid_call = next(c for c in call_stack if c['tool'] == 'hybrid_search')
                    
                    assert vector_call['tenant_id'] == str(tenant_a_id)
                    assert hybrid_call['tenant_id'] == str(tenant_a_id)

    @pytest.mark.asyncio
    async def test_tenant_data_leak_prevention(self, monkeypatch, tenant_a_id, tenant_b_id):
        """Test that tenants cannot access each other's data."""
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        
        # Simulate database with tenant-specific data
        tenant_data = {
            tenant_a_id: [{"content": "Sensitive Tenant A data", "score": 0.9}],
            tenant_b_id: [{"content": "Sensitive Tenant B data", "score": 0.9}]
        }
        
        async def mock_match_chunks(tenant_id, embedding, limit):
            # Return only data for the specific tenant
            return tenant_data.get(tenant_id, [])
        
        async def mock_hybrid_search(tenant_id, embedding, query_text, limit, text_weight):
            # Return only data for the specific tenant
            return tenant_data.get(tenant_id, [])
        
        with patch('agent.db_utils.match_chunks', side_effect=mock_match_chunks), \
             patch('agent.db_utils.hybrid_search', side_effect=mock_hybrid_search):
            
            # Test vector search tool
            vector_input = VectorSearchInput(query="sensitive data", limit=10)
            
            tenant_a_results = await vector_search_tool(vector_input, tenant_a_id)
            tenant_b_results = await vector_search_tool(vector_input, tenant_b_id)
            
            # Verify tenant isolation
            assert len(tenant_a_results) == 1
            assert len(tenant_b_results) == 1
            assert "Tenant A data" in str(tenant_a_results[0])
            assert "Tenant B data" in str(tenant_b_results[0])
            assert "Tenant A data" not in str(tenant_b_results[0])
            assert "Tenant B data" not in str(tenant_a_results[0])
            
            # Test hybrid search tool
            hybrid_input = HybridSearchInput(query="sensitive data", limit=10, text_weight=0.5)
            
            tenant_a_hybrid = await hybrid_search_tool(hybrid_input, tenant_a_id)
            tenant_b_hybrid = await hybrid_search_tool(hybrid_input, tenant_b_id)
            
            # Verify tenant isolation for hybrid search
            assert len(tenant_a_hybrid) == 1
            assert len(tenant_b_hybrid) == 1
            assert "Tenant A data" in str(tenant_a_hybrid[0])
            assert "Tenant B data" in str(tenant_b_hybrid[0])
            assert "Tenant A data" not in str(tenant_b_hybrid[0])
            assert "Tenant B data" not in str(tenant_a_hybrid[0])

    @pytest.mark.asyncio
    async def test_uuid_validation_throughout_stack(self, monkeypatch):
        """Test UUID validation is enforced at all levels of the stack."""
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        
        invalid_tenant_ids = [
            "not-a-uuid",
            12345,
            None,
            {},
            []
        ]
        
        for invalid_id in invalid_tenant_ids:
            # Test database layer validation
            with pytest.raises((ValueError, TypeError)):
                await match_chunks(invalid_id, [0.1] * 1536, 10)
            
            with pytest.raises((ValueError, TypeError)):
                await hybrid_search(invalid_id, [0.1] * 1536, "test", 10, 0.3)

    @pytest.mark.asyncio
    async def test_stored_procedure_parameter_order(self, monkeypatch, tenant_a_id):
        """Test that stored procedures are called with correct parameter order."""
        monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
        
        call_log = []
        
        # Mock database connection to capture SQL calls
        class MockConnection:
            async def fetchval(self, query):
                return True  # Stored procedures exist
            
            async def fetch(self, query, *args):
                call_log.append({
                    'query': query,
                    'args': args,
                    'arg_types': [type(arg) for arg in args]
                })
                return []
        
        mock_pool = MagicMock()
        mock_pool.acquire.return_value.__aenter__.return_value = MockConnection()
        
        with patch('agent.db_utils.get_database_pool', return_value=mock_pool):
            # Test match_chunks
            embedding = [0.1] * 1536
            await match_chunks(tenant_a_id, embedding, 10)
            
            # Test hybrid_search
            await hybrid_search(tenant_a_id, embedding, "test query", 10, 0.3)
            
            # Verify stored procedure calls
            assert len(call_log) == 2
            
            # Check match_chunks call
            match_call = call_log[0]
            assert "match_chunks($1, $2::vector, $3)" in match_call['query']
            assert match_call['args'][0] == tenant_a_id  # First param is tenant_id
            assert isinstance(match_call['args'][1], str)  # Embedding as vector string
            assert match_call['args'][2] == 10  # Limit
            
            # Check hybrid_search call
            hybrid_call = call_log[1]
            assert "hybrid_search($1::uuid, $2::vector, $3, $4, $5)" in hybrid_call['query']
            assert hybrid_call['args'][0] == tenant_a_id  # First param is tenant_id
            assert isinstance(hybrid_call['args'][1], str)  # Embedding as vector string
            assert hybrid_call['args'][2] == "test query"  # Query text
            assert hybrid_call['args'][3] == 10  # Limit
            assert hybrid_call['args'][4] == 0.3  # Text weight