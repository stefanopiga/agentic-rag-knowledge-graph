"""
Tests for stored procedure fallback scenarios in RAG functions.

This test module covers scenarios where stored procedures are not available
or fail, ensuring the system gracefully degrades with appropriate logging
and empty result sets instead of crashing.
"""

import pytest
import asyncio
import asyncpg
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from agent.db_utils import match_chunks, hybrid_search


class TestMatchChunksFallback:
    """Test match_chunks fallback scenarios when stored procedures fail."""
    
    @pytest.mark.asyncio
    async def test_match_chunks_postgres_error_fallback(self):
        """Test match_chunks handles PostgresError gracefully."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        limit = 10
        
        mock_conn = AsyncMock()
        # Simulate PostgresError for missing stored procedure
        mock_conn.fetch = AsyncMock(
            side_effect=asyncpg.PostgresError("function match_chunks does not exist")
        )
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            # Should return empty list without raising exception
            results = await match_chunks(tenant_id, embedding, limit)
            
            assert results == []
            
            # Verify logging
            mock_logger.error.assert_called_once()
            mock_logger.warning.assert_called_once_with(
                "Stored procedure match_chunks failed - returning safe fallback results"
            )
            
            # Verify stored procedure was attempted
            mock_conn.fetch.assert_called_once_with(
                "SELECT * FROM match_chunks($1, $2::vector, $3)",
                tenant_id,
                '[' + ','.join(map(str, embedding)) + ']',
                limit
            )

    @pytest.mark.asyncio
    async def test_match_chunks_undefined_function_error(self):
        """Test match_chunks handles UndefinedFunction error specifically."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        limit = 5
        
        mock_conn = AsyncMock()
        # Create a more specific PostgresError for undefined function
        error = asyncpg.UndefinedFunctionError("function match_chunks(uuid, vector, integer) does not exist")
        mock_conn.fetch = AsyncMock(side_effect=error)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await match_chunks(tenant_id, embedding, limit)
            
            assert results == []
            
            # Verify specific error logging
            mock_logger.error.assert_called_once()
            error_call_args = mock_logger.error.call_args[0][0]
            assert "PostgreSQL error in match_chunks" in error_call_args
            assert str(tenant_id) in error_call_args

    @pytest.mark.asyncio
    async def test_match_chunks_connection_error_fallback(self):
        """Test match_chunks handles connection errors gracefully."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        limit = 15
        
        mock_conn = AsyncMock()
        # Simulate connection timeout or network error
        mock_conn.fetch = AsyncMock(
            side_effect=asyncpg.ConnectionDoesNotExistError("connection was closed")
        )
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await match_chunks(tenant_id, embedding, limit)
            
            assert results == []
            
            # Verify general error handling
            mock_logger.error.assert_called_once()
            mock_logger.warning.assert_called_once_with(
                "Stored procedure match_chunks failed - returning safe fallback results"
            )

    @pytest.mark.asyncio
    async def test_match_chunks_generic_exception_fallback(self):
        """Test match_chunks handles generic exceptions gracefully."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        limit = 8
        
        mock_conn = AsyncMock()
        # Simulate unexpected exception
        mock_conn.fetch = AsyncMock(
            side_effect=RuntimeError("Unexpected database error")
        )
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await match_chunks(tenant_id, embedding, limit)
            
            assert results == []
            
            # Verify generic error handling
            mock_logger.error.assert_called_once()
            error_call_args = mock_logger.error.call_args[0][0]
            assert "Unexpected error in match_chunks" in error_call_args
            assert "Unexpected database error" in error_call_args
            
            mock_logger.warning.assert_called_once_with(
                "match_chunks operation failed - returning safe fallback results"
            )

    @pytest.mark.asyncio
    async def test_match_chunks_invalid_tenant_fallback(self):
        """Test match_chunks with None tenant_id returns empty results securely."""
        embedding = [0.1] * 1536
        limit = 5
        
        with patch('agent.db_utils.logger') as mock_logger:
            results = await match_chunks(None, embedding, limit)
            
            assert results == []
            
            # Verify security warning is logged
            mock_logger.warning.assert_called_once_with(
                "match_chunks called without tenant_id - returning empty results for security"
            )

    @pytest.mark.asyncio
    async def test_match_chunks_successful_operation_logging(self):
        """Test match_chunks logs successful operations appropriately."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        limit = 12
        
        mock_conn = AsyncMock()
        mock_results = [
            {'id': 'chunk1', 'content': 'test content', 'similarity': 0.95},
            {'id': 'chunk2', 'content': 'another content', 'similarity': 0.85}
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_results)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await match_chunks(tenant_id, embedding, limit)
            
            assert len(results) == 2
            assert results[0]['id'] == 'chunk1'
            assert results[1]['id'] == 'chunk2'
            
            # Verify info logging for successful operation
            mock_logger.info.assert_called_once()
            info_call_args = mock_logger.info.call_args[0][0]
            assert "Performing match_chunks search for tenant" in info_call_args
            assert str(tenant_id) in info_call_args
            assert f"limit {limit}" in info_call_args


class TestHybridSearchFallback:
    """Test hybrid_search fallback scenarios when stored procedures fail."""
    
    @pytest.mark.asyncio
    async def test_hybrid_search_postgres_error_fallback(self):
        """Test hybrid_search handles PostgresError gracefully."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        query_text = "test search query"
        limit = 10
        text_weight = 0.3
        
        mock_conn = AsyncMock()
        # Simulate PostgresError for missing stored procedure
        postgres_error = asyncpg.PostgresError("function hybrid_search does not exist")
        mock_conn.fetch = AsyncMock(side_effect=postgres_error)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            # Should return empty list without raising exception
            results = await hybrid_search(
                tenant_id, embedding, query_text, limit, text_weight
            )
            
            assert results == []
            
            # Verify warning logging  
            mock_logger.warning.assert_called_once()
            warning_call_args = mock_logger.warning.call_args[0][0]
            assert "Stored procedure hybrid_search failed - returning safe fallback results" in warning_call_args
            
            # Verify error logging includes tenant_id
            mock_logger.error.assert_called_once()
            error_call_args = mock_logger.error.call_args[0][0]
            assert str(tenant_id) in error_call_args
            
            # Verify stored procedure was attempted
            mock_conn.fetch.assert_called_once_with(
                "SELECT * FROM hybrid_search($1::uuid, $2::vector, $3, $4, $5)",
                tenant_id,
                '[' + ','.join(map(str, embedding)) + ']',
                query_text,
                limit,
                text_weight
            )

    @pytest.mark.asyncio
    async def test_hybrid_search_undefined_function_error(self):
        """Test hybrid_search handles UndefinedFunction error specifically."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        query_text = "medical procedure"
        limit = 15
        text_weight = 0.5
        
        mock_conn = AsyncMock()
        # Create a more specific PostgresError for undefined function
        error = asyncpg.UndefinedFunctionError(
            "function hybrid_search(uuid, vector, text, integer, numeric) does not exist"
        )
        mock_conn.fetch = AsyncMock(side_effect=error)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await hybrid_search(
                tenant_id, embedding, query_text, limit, text_weight
            )
            
            assert results == []
            
            # Verify specific PostgresError handling
            mock_logger.warning.assert_called_once()
            warning_message = mock_logger.warning.call_args[0][0]
            assert "Stored procedure hybrid_search failed - returning safe fallback results" in warning_message

    @pytest.mark.asyncio 
    async def test_hybrid_search_connection_timeout_fallback(self):
        """Test hybrid_search handles connection timeout gracefully."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        query_text = "connection test"
        limit = 8
        text_weight = 0.7
        
        mock_conn = AsyncMock()
        # Simulate connection timeout (PostgresError subclass)
        timeout_error = asyncpg.ConnectionFailureError("connection timeout")
        mock_conn.fetch = AsyncMock(side_effect=timeout_error)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await hybrid_search(
                tenant_id, embedding, query_text, limit, text_weight
            )
            
            assert results == []
            
            # Verify PostgresError handling for connection issues
            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_hybrid_search_non_postgres_exception_propagation(self):
        """Test hybrid_search propagates non-PostgresError exceptions."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        query_text = "exception test"
        limit = 5
        text_weight = 0.2
        
        mock_conn = AsyncMock()
        # Simulate non-PostgresError exception that should be propagated
        value_error = ValueError("Invalid embedding format")
        mock_conn.fetch = AsyncMock(side_effect=value_error)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            # Non-PostgresError should be raised, not handled gracefully
            with pytest.raises(ValueError, match="Invalid embedding format"):
                await hybrid_search(
                    tenant_id, embedding, query_text, limit, text_weight
                )
            
            # Verify error was logged before re-raising
            mock_logger.error.assert_called_once()
            error_message = mock_logger.error.call_args[0][0]
            assert "Hybrid search failed for tenant" in error_message
            assert str(tenant_id) in error_message

    @pytest.mark.asyncio
    async def test_hybrid_search_successful_operation_logging(self):
        """Test hybrid_search logs successful operations appropriately."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        query_text = "successful search test"
        limit = 20
        text_weight = 0.4
        
        mock_conn = AsyncMock()
        mock_results = [
            {
                'id': 'hybrid1',
                'content': 'hybrid content 1',
                'similarity': 0.92,
                'rank': 1
            },
            {
                'id': 'hybrid2', 
                'content': 'hybrid content 2',
                'similarity': 0.88,
                'rank': 2
            }
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_results)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await hybrid_search(
                tenant_id, embedding, query_text, limit, text_weight
            )
            
            assert len(results) == 2
            assert results[0]['id'] == 'hybrid1'
            assert results[1]['id'] == 'hybrid2'
            
            # Verify info logging for successful operation
            mock_logger.info.assert_called_once()
            info_call_args = mock_logger.info.call_args[0][0]
            assert "Performing hybrid_search for tenant" in info_call_args
            assert str(tenant_id) in info_call_args
            assert "successful search test" in info_call_args
            assert f"limit {limit}" in info_call_args

    @pytest.mark.asyncio
    async def test_hybrid_search_parameter_validation_with_fallback_context(self):
        """Test hybrid_search parameter validation still works in fallback scenarios."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        query_text = "validation test"
        limit = 10
        
        # Test text_weight validation fails before database operations
        with pytest.raises(ValueError, match="text_weight must be between 0.0 and 1.0"):
            await hybrid_search(
                tenant_id, embedding, query_text, limit, text_weight=1.5
            )
        
        with pytest.raises(ValueError, match="text_weight must be between 0.0 and 1.0"):
            await hybrid_search(
                tenant_id, embedding, query_text, limit, text_weight=-0.1
            )
        
        # Test tenant_id validation
        with pytest.raises(ValueError, match="Invalid tenant_id"):
            await hybrid_search(
                "invalid-uuid", embedding, query_text, limit, text_weight=0.3
            )


class TestStoredProcedureAvailabilityMonitoring:
    """Test monitoring and detection of stored procedure availability."""
    
    @pytest.mark.asyncio
    async def test_match_chunks_error_sqlstate_logging(self):
        """Test that PostgresError sqlstate is properly logged for monitoring."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        limit = 10
        
        mock_conn = AsyncMock()
        # Create PostgresError with specific sqlstate
        postgres_error = asyncpg.PostgresError("function does not exist")
        postgres_error.sqlstate = "42883"  # undefined_function sqlstate
        mock_conn.fetch = AsyncMock(side_effect=postgres_error)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await match_chunks(tenant_id, embedding, limit)
            
            assert results == []
            
            # Verify sqlstate is logged for monitoring
            mock_logger.error.assert_called_once()
            error_message = mock_logger.error.call_args[0][0]
            assert "42883" in error_message  # sqlstate should be in error message

    @pytest.mark.asyncio
    async def test_multiple_fallback_scenarios_in_sequence(self):
        """Test that multiple fallback scenarios work consistently."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        query_text = "sequence test"
        
        # First call - match_chunks fails
        mock_conn1 = AsyncMock()
        mock_conn1.fetch = AsyncMock(
            side_effect=asyncpg.PostgresError("match_chunks not found")
        )
        
        # Second call - hybrid_search fails  
        mock_conn2 = AsyncMock()
        mock_conn2.fetch = AsyncMock(
            side_effect=asyncpg.PostgresError("hybrid_search not found")
        )
        
        mock_ctx1 = AsyncMock()
        mock_ctx1.__aenter__.return_value = mock_conn1
        mock_ctx1.__aexit__.return_value = None
        
        mock_ctx2 = AsyncMock()
        mock_ctx2.__aenter__.return_value = mock_conn2  
        mock_ctx2.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool:
            # First call to match_chunks
            mock_pool.acquire.return_value = mock_ctx1
            result1 = await match_chunks(tenant_id, embedding, 10)
            
            # Second call to hybrid_search
            mock_pool.acquire.return_value = mock_ctx2
            result2 = await hybrid_search(tenant_id, embedding, query_text, 10, 0.3)
            
            # Both should return empty arrays gracefully
            assert result1 == []
            assert result2 == []