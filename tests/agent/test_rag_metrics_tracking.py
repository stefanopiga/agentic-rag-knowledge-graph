"""
Tests for RAG operations metrics tracking and stored procedure fallback monitoring.
"""

import pytest
import asyncio
import asyncpg
from unittest.mock import Mock, AsyncMock, patch, MagicMock, PropertyMock
from uuid import uuid4

# Test imports  
from agent.db_utils import hybrid_search, get_document_chunks
from agent.monitoring import update_connection_metrics


class TestRAGMetricsTracking:
    """Test metrics tracking for RAG operations."""
    


    @pytest.mark.asyncio
    async def test_hybrid_search_success_metrics(self):
        """Test that successful hybrid_search operations are tracked."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        query_text = "test query"
        limit = 10
        text_weight = 0.3
        
        mock_conn = AsyncMock()
        mock_results = [
            {
                'id': 'hybrid1',
                'content': 'hybrid content',
                'similarity': 0.90,
                'rank': 1
            }
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_results)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        # Mock metrics functions
        mock_track_operation = Mock()
        mock_update_availability = Mock()
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.monitoring.track_stored_procedure_operation', mock_track_operation), \
             patch('agent.monitoring.update_stored_procedure_availability', mock_update_availability):
            mock_pool.acquire.return_value = mock_ctx
            
            results = await hybrid_search(
                tenant_id, embedding, query_text, limit, text_weight
            )
            
            assert len(results) == 1
            assert results[0]['id'] == 'hybrid1'
            
            # Verify success metrics were tracked
            mock_track_operation.assert_called_once_with(
                "hybrid_search", str(tenant_id), "success"
            )
            mock_update_availability.assert_called_once_with("hybrid_search", True)

    @pytest.mark.asyncio
    async def test_hybrid_search_fallback_metrics(self):
        """Test that hybrid_search fallback operations are tracked."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        query_text = "test query"
        limit = 10
        text_weight = 0.3
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(
            side_effect=asyncpg.PostgresError("function hybrid_search does not exist")
        )
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        # Mock metrics functions
        mock_track_operation = Mock()
        mock_update_availability = Mock()
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.monitoring.track_stored_procedure_operation', mock_track_operation), \
             patch('agent.monitoring.update_stored_procedure_availability', mock_update_availability):
            mock_pool.acquire.return_value = mock_ctx
            
            results = await hybrid_search(
                tenant_id, embedding, query_text, limit, text_weight
            )
            
            # Should return empty list
            assert results == []
            
            # Verify fallback metrics were tracked
            mock_track_operation.assert_called_once_with(
                "hybrid_search", str(tenant_id), "fallback"
            )
            mock_update_availability.assert_called_once_with("hybrid_search", False)

    @pytest.mark.asyncio
    async def test_get_document_chunks_success_metrics(self):
        """Test that successful get_document_chunks operations are tracked."""
        tenant_id = uuid4()
        document_id = str(uuid4())
        
        mock_conn = AsyncMock()
        mock_results = [
            {
                'chunk_id': 'chunk1',
                'content': 'document content',
                'chunk_index': 0,
                'metadata': '{}'
            }
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_results)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        # Mock metrics functions
        mock_track_operation = Mock()
        mock_update_availability = Mock()
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.monitoring.track_stored_procedure_operation', mock_track_operation), \
             patch('agent.monitoring.update_stored_procedure_availability', mock_update_availability):
            mock_pool.acquire.return_value = mock_ctx
            
            results = await get_document_chunks(document_id, tenant_id)
            
            assert len(results) == 1
            assert results[0]['chunk_id'] == 'chunk1'
            
            # Verify success metrics were tracked
            mock_track_operation.assert_called_once_with(
                "get_document_chunks", str(tenant_id), "success"
            )
            mock_update_availability.assert_called_once_with("get_document_chunks", True)

    @pytest.mark.asyncio
    async def test_get_document_chunks_fallback_metrics(self):
        """Test that get_document_chunks fallback operations are tracked."""
        tenant_id = uuid4()
        document_id = str(uuid4())
        
        mock_conn = AsyncMock()
        # Both stored procedure and fallback query fail
        mock_conn.fetch = AsyncMock(side_effect=[
            asyncpg.UndefinedFunctionError("function get_document_chunks does not exist"),
            asyncpg.PostgresError("connection failed")
        ])
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        # Mock metrics functions
        mock_track_operation = Mock()
        mock_update_availability = Mock()
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.monitoring.track_stored_procedure_operation', mock_track_operation), \
             patch('agent.monitoring.update_stored_procedure_availability', mock_update_availability):
            mock_pool.acquire.return_value = mock_ctx
            
            results = await get_document_chunks(document_id, tenant_id)
            
            # Should return empty list after fallback
            assert results == []
            
            # Verify fallback metrics were tracked
            mock_track_operation.assert_called_once_with(
                "get_document_chunks", str(tenant_id), "fallback"
            )
            mock_update_availability.assert_called_once_with("get_document_chunks", False)




class TestMetricsIntegration:
    """Test integration of metrics tracking with the monitoring system."""
    



class TestConnectionMetrics:
    """Test real database connection metrics tracking."""
    
    def test_update_connection_metrics_with_real_pools(self):
        """Test that update_connection_metrics accesses real connection pools and updates metrics."""
        
        # Mock PostgreSQL pool
        mock_pg_pool = Mock()
        mock_pg_pool.get_size.return_value = 10
        mock_pg_pool.get_idle_size.return_value = 3
        
        # Mock Neo4j Graphiti client
        mock_graphiti_client = Mock()
        mock_graphiti_client._initialized = True
        mock_graphiti_client.graphiti = Mock()
        mock_graphiti_client.graphiti.driver = Mock()
        mock_neo4j_pool = Mock()
        mock_neo4j_pool.in_use = 2
        mock_graphiti_client.graphiti.driver._pool = mock_neo4j_pool
        
        # Mock Redis cache manager
        mock_cache_manager = Mock()
        mock_cache_manager.redis = Mock()
        mock_redis_info = {
            'connected_clients': 5,
            'blocked_clients': 0
        }
        mock_cache_manager.redis.info = AsyncMock(return_value=mock_redis_info)
        
        # Mock Prometheus metrics
        mock_db_connections_active = Mock()
        mock_pg_gauge = Mock()
        mock_neo4j_gauge = Mock()
        mock_redis_gauge = Mock()
        mock_db_connections_active.labels.side_effect = lambda database_type: {
            "postgresql": mock_pg_gauge,
            "neo4j": mock_neo4j_gauge,
            "redis": mock_redis_gauge
        }[database_type]
        
        with patch('agent.db_utils.db_pool') as mock_db_pool, \
             patch('agent.graph_utils.graph_client', mock_graphiti_client), \
             patch('agent.cache_manager.cache_manager', mock_cache_manager), \
             patch('agent.monitoring.db_connections_active', mock_db_connections_active):
            
            mock_db_pool.pool = mock_pg_pool
            
            # Call the function
            update_connection_metrics()
            
            # Verify PostgreSQL metrics (active = total - idle)
            mock_db_connections_active.labels.assert_any_call(database_type="postgresql")
            mock_pg_gauge.set.assert_called_once_with(7)  # 10 - 3 = 7 active
            
            # Verify Neo4j metrics
            mock_db_connections_active.labels.assert_any_call(database_type="neo4j")
            mock_neo4j_gauge.set.assert_called_once_with(2)
            
            # Verify Redis metrics
            mock_db_connections_active.labels.assert_any_call(database_type="redis")
            mock_redis_gauge.set.assert_called_once_with(1)
    
    def test_update_connection_metrics_with_unavailable_pools(self):
        """Test update_connection_metrics handles unavailable connection pools gracefully."""
        
        # Mock unavailable pools
        mock_graphiti_client = Mock()
        mock_graphiti_client._initialized = False
        mock_graphiti_client.graphiti = None
        
        mock_cache_manager = Mock()
        mock_cache_manager.redis = None
        
        # Mock Prometheus metrics
        mock_db_connections_active = Mock()
        mock_pg_gauge = Mock()
        mock_neo4j_gauge = Mock()
        mock_redis_gauge = Mock()
        mock_db_connections_active.labels.side_effect = lambda database_type: {
            "postgresql": mock_pg_gauge,
            "neo4j": mock_neo4j_gauge,
            "redis": mock_redis_gauge
        }[database_type]
        
        with patch('agent.db_utils.db_pool') as mock_db_pool, \
             patch('agent.graph_utils.graph_client', mock_graphiti_client), \
             patch('agent.cache_manager.cache_manager', mock_cache_manager), \
             patch('agent.monitoring.db_connections_active', mock_db_connections_active), \
             patch('agent.monitoring.logger') as mock_logger:
            
            mock_db_pool.pool = None  # Uninitialized PostgreSQL pool
            
            # Call the function - should not raise exception
            update_connection_metrics()
            
            # Should set 0 for unavailable pools
            mock_pg_gauge.set.assert_called_once_with(0)
            mock_neo4j_gauge.set.assert_called_once_with(0)
            mock_redis_gauge.set.assert_called_once_with(0)
            
            # Should log warnings for unavailable pools
            assert mock_logger.warning.call_count >= 1
    
    def test_update_connection_metrics_with_pool_errors(self):
        """Test update_connection_metrics handles pool access errors gracefully."""
        
        # Mock PostgreSQL pool that raises exception
        mock_pg_pool = Mock()
        mock_pg_pool.get_size.side_effect = Exception("Connection pool error")
        
        # Mock Neo4j that raises exception
        mock_graphiti_client = Mock()
        mock_graphiti_client._initialized = True
        mock_graphiti_client.graphiti = Mock()
        mock_graphiti_client.graphiti.driver = Mock()
        mock_graphiti_client.graphiti.driver._pool = Mock()
        type(mock_graphiti_client.graphiti.driver._pool).in_use = PropertyMock(
            side_effect=Exception("Neo4j pool error")
        )
        
        # Mock Redis that raises exception
        mock_cache_manager = Mock()
        mock_cache_manager.redis = Mock()
        mock_cache_manager.redis.info = AsyncMock(side_effect=Exception("Redis error"))
        
        # Mock Prometheus metrics
        mock_db_connections_active = Mock()
        mock_gauge = Mock()
        mock_db_connections_active.labels.return_value = mock_gauge
        
        with patch('agent.db_utils.db_pool') as mock_db_pool, \
             patch('agent.graph_utils.graph_client', mock_graphiti_client), \
             patch('agent.cache_manager.cache_manager', mock_cache_manager), \
             patch('agent.monitoring.db_connections_active', mock_db_connections_active), \
             patch('agent.monitoring.logger') as mock_logger:
            
            mock_db_pool.pool = mock_pg_pool
            
            # Call the function - should not raise exception
            update_connection_metrics()
            
            # Should log warnings for pool errors and continue execution
            assert mock_logger.warning.call_count >= 2  # At least PostgreSQL and Neo4j warnings
            warning_calls = mock_logger.warning.call_args_list
            assert any("Failed to get PostgreSQL pool stats" in str(call) for call in warning_calls)
            assert any("Failed to get Neo4j pool stats" in str(call) for call in warning_calls)
    
    def test_update_connection_metrics_replaces_placeholder_values(self):
        """Test that update_connection_metrics replaces the original placeholder values."""
        
        # Mock real pools with different values than placeholders
        mock_pg_pool = Mock()
        mock_pg_pool.get_size.return_value = 15
        mock_pg_pool.get_idle_size.return_value = 8
        
        mock_graphiti_client = Mock()
        mock_graphiti_client._initialized = True
        mock_graphiti_client.graphiti = Mock()
        mock_graphiti_client.graphiti.driver = Mock()
        mock_neo4j_pool = Mock()
        mock_neo4j_pool.in_use = 4
        mock_graphiti_client.graphiti.driver._pool = mock_neo4j_pool
        
        mock_cache_manager = Mock()
        mock_cache_manager.redis = Mock()
        mock_redis_info = {'connected_clients': 8}
        mock_cache_manager.redis.info = AsyncMock(return_value=mock_redis_info)
        
        # Mock Prometheus metrics
        mock_db_connections_active = Mock()
        mock_pg_gauge = Mock()
        mock_neo4j_gauge = Mock()
        mock_redis_gauge = Mock()
        mock_db_connections_active.labels.side_effect = lambda database_type: {
            "postgresql": mock_pg_gauge,
            "neo4j": mock_neo4j_gauge,
            "redis": mock_redis_gauge
        }[database_type]
        
        with patch('agent.db_utils.db_pool') as mock_db_pool, \
             patch('agent.graph_utils.graph_client', mock_graphiti_client), \
             patch('agent.cache_manager.cache_manager', mock_cache_manager), \
             patch('agent.monitoring.db_connections_active', mock_db_connections_active):
            
            mock_db_pool.pool = mock_pg_pool
            
            # Call the function
            update_connection_metrics()
            
            # Verify that real values are used, not placeholders (5, 2, 1)
            mock_pg_gauge.set.assert_called_once_with(7)    # 15 - 8 = 7 (not 5)
            mock_neo4j_gauge.set.assert_called_once_with(4)  # 4 (not 2)
            mock_redis_gauge.set.assert_called_once_with(1)  # 1 (simplified for Redis)