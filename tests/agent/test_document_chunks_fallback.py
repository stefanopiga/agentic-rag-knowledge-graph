"""
Tests for get_document_chunks fallback scenarios and the safe fallback utility function.
"""

import pytest
import asyncio
import asyncpg
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from agent.db_utils import get_document_chunks, _handle_stored_procedure_fallback


class TestGetDocumentChunksFallback:
    """Test get_document_chunks fallback scenarios when stored procedures fail."""
    
    @pytest.mark.asyncio
    async def test_get_document_chunks_stored_procedure_success(self):
        """Test get_document_chunks uses stored procedure successfully when available."""
        tenant_id = uuid4()
        document_id = str(uuid4())
        
        mock_conn = AsyncMock()
        mock_results = [
            {
                'chunk_id': 'chunk1',
                'content': 'First chunk content',
                'chunk_index': 0,
                'metadata': '{}'
            },
            {
                'chunk_id': 'chunk2',
                'content': 'Second chunk content', 
                'chunk_index': 1,
                'metadata': '{}'
            }
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_results)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await get_document_chunks(document_id, tenant_id)
            
            assert len(results) == 2
            assert results[0]['chunk_id'] == 'chunk1'
            assert results[1]['chunk_id'] == 'chunk2'
            
            # Verify stored procedure was called
            mock_conn.fetch.assert_called_once_with(
                "SELECT * FROM get_document_chunks($1::uuid, $2::uuid)",
                tenant_id,
                document_id
            )

    @pytest.mark.asyncio
    async def test_get_document_chunks_stored_procedure_fallback(self):
        """Test get_document_chunks falls back to direct query when stored procedure fails."""
        tenant_id = uuid4()
        document_id = str(uuid4())
        
        mock_conn = AsyncMock()
        # First call (stored procedure) fails, second call (fallback) succeeds
        fallback_results = [
            {
                'chunk_id': 'fallback_chunk1',
                'content': 'Fallback content 1',
                'chunk_index': 0,
                'metadata': '{}'
            }
        ]
        
        mock_conn.fetch = AsyncMock(side_effect=[
            asyncpg.UndefinedFunctionError("function get_document_chunks does not exist"),
            fallback_results
        ])
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await get_document_chunks(document_id, tenant_id)
            
            assert len(results) == 1
            assert results[0]['chunk_id'] == 'fallback_chunk1'
            
            # Verify both calls were made
            assert mock_conn.fetch.call_count == 2
            
            # Verify stored procedure call
            first_call = mock_conn.fetch.call_args_list[0]
            assert "get_document_chunks($1::uuid, $2::uuid)" in first_call[0][0]
            
            # Verify fallback query with tenant filtering
            second_call = mock_conn.fetch.call_args_list[1]
            fallback_query = second_call[0][0]
            assert "JOIN documents d ON c.document_id = d.id" in fallback_query
            assert "d.tenant_id = $2::uuid" in fallback_query
            
            # Verify warning was logged
            mock_logger.warning.assert_called()
            mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_document_chunks_complete_fallback_failure(self):
        """Test get_document_chunks returns empty when both stored procedure and fallback fail."""
        tenant_id = uuid4()
        document_id = str(uuid4())
        
        mock_conn = AsyncMock()
        # Both calls fail
        mock_conn.fetch = AsyncMock(side_effect=[
            asyncpg.UndefinedFunctionError("function get_document_chunks does not exist"),
            asyncpg.ConnectionDoesNotExistError("connection was closed")
        ])
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await get_document_chunks(document_id, tenant_id)
            
            # Should return empty list
            assert results == []
            
            # Verify both calls were attempted
            assert mock_conn.fetch.call_count == 2
            
            # Verify error handling
            mock_logger.warning.assert_called()
            mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_get_document_chunks_dev_tenant_fallback(self):
        """Test get_document_chunks uses DEV_TENANT_UUID fallback when no tenant_id provided."""
        document_id = str(uuid4())
        
        mock_conn = AsyncMock()
        mock_results = [
            {
                'chunk_id': 'dev_chunk1',
                'content': 'Dev tenant content',
                'chunk_index': 0,
                'metadata': '{}'
            }
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_results)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await get_document_chunks(document_id)  # No tenant_id
            
            assert len(results) == 1
            assert results[0]['chunk_id'] == 'dev_chunk1'
            
            # Verify stored procedure was called with DEV_TENANT_UUID
            call_args = mock_conn.fetch.call_args
            query = call_args[0][0]
            assert "get_document_chunks($1::uuid, $2::uuid)" in query
            
            # Verify DEV_TENANT_UUID was used (00000000-0000-0000-0000-000000000000)
            from agent.db_utils import DEV_TENANT_UUID
            assert call_args[0][1] == DEV_TENANT_UUID

    @pytest.mark.asyncio
    async def test_get_document_chunks_dev_tenant_fallback_failure(self):
        """Test get_document_chunks handles failures with DEV_TENANT_UUID gracefully."""
        document_id = str(uuid4())
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(side_effect=[
            asyncpg.UndefinedFunctionError("function get_document_chunks does not exist"),
            asyncpg.PostgresError("connection failed")
        ])
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await get_document_chunks(document_id)
            
            # Should return empty list after both stored procedure and fallback fail
            assert results == []
            
            # Verify fallback was attempted (two fetch calls)
            assert mock_conn.fetch.call_count == 2
            
            # Verify error/warning was logged
            mock_logger.warning.assert_called()
            mock_logger.error.assert_called()


class TestStoredProcedureFallbackUtility:
    """Test the _handle_stored_procedure_fallback utility function."""
    
    def test_handle_postgres_error_fallback(self):
        """Test utility function handles PostgresError correctly."""
        tenant_id = uuid4()
        operation_name = "test_operation"
        error = asyncpg.PostgresError("function does not exist")
        error.sqlstate = "42883"
        
        with patch('agent.db_utils.logger') as mock_logger:
            result = _handle_stored_procedure_fallback(
                operation_name, tenant_id, error
            )
            
            assert result == []
            
            # Verify correct logging
            mock_logger.error.assert_called_once()
            error_message = mock_logger.error.call_args[0][0]
            assert "PostgreSQL error in test_operation" in error_message
            assert str(tenant_id) in error_message
            assert "42883" in error_message
            
            mock_logger.warning.assert_called_once()
            warning_message = mock_logger.warning.call_args[0][0]
            assert "Stored procedure test_operation failed" in warning_message

    def test_handle_generic_error_fallback(self):
        """Test utility function handles generic exceptions correctly."""
        tenant_id = uuid4()
        operation_name = "test_operation"
        error = RuntimeError("Unexpected error occurred")
        
        with patch('agent.db_utils.logger') as mock_logger:
            result = _handle_stored_procedure_fallback(
                operation_name, tenant_id, error
            )
            
            assert result == []
            
            # Verify generic error logging
            mock_logger.error.assert_called_once()
            error_message = mock_logger.error.call_args[0][0]
            assert "Unexpected error in test_operation" in error_message
            assert str(tenant_id) in error_message
            assert "Unexpected error occurred" in error_message
            
            mock_logger.warning.assert_called_once()
            warning_message = mock_logger.warning.call_args[0][0]
            assert "test_operation operation failed" in warning_message

    def test_handle_fallback_with_custom_result(self):
        """Test utility function respects custom fallback results."""
        tenant_id = uuid4()
        operation_name = "test_operation"
        error = ValueError("Test error")
        custom_fallback = [{"id": "fallback_item", "data": "fallback_data"}]
        
        with patch('agent.db_utils.logger') as mock_logger:
            result = _handle_stored_procedure_fallback(
                operation_name, tenant_id, error, custom_fallback
            )
            
            assert result == custom_fallback
            assert len(result) == 1
            assert result[0]["id"] == "fallback_item"

    def test_handle_fallback_parameter_validation(self):
        """Test utility function handles edge cases in parameters."""
        tenant_id = uuid4()
        operation_name = ""  # Edge case: empty operation name
        error = Exception("Test")
        
        with patch('agent.db_utils.logger') as mock_logger:
            result = _handle_stored_procedure_fallback(
                operation_name, tenant_id, error
            )
            
            assert result == []
            
            # Should still log even with empty operation name
            mock_logger.error.assert_called_once()
            mock_logger.warning.assert_called_once()


class TestIntegratedFallbackBehavior:
    """Test integrated behavior of fallback mechanisms across functions."""
    
    @pytest.mark.asyncio
    async def test_consistent_fallback_behavior_across_functions(self):
        """Test that all RAG functions have consistent fallback behavior."""
        tenant_id = uuid4()
        
        # Mock database that throws PostgresError for all stored procedures
        mock_conn = AsyncMock()
        postgres_error = asyncpg.UndefinedFunctionError("functions not available")
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            # Test match_chunks fallback
            from agent.db_utils import match_chunks
            mock_conn.fetch = AsyncMock(side_effect=postgres_error)
            result1 = await match_chunks(tenant_id, [0.1] * 1536, 10)
            assert result1 == []
            
            # Test hybrid_search fallback  
            from agent.db_utils import hybrid_search
            mock_conn.fetch = AsyncMock(side_effect=postgres_error)
            result2 = await hybrid_search(tenant_id, [0.1] * 1536, "test", 10, 0.3)
            assert result2 == []
            
            # All should return empty lists and log consistently
            assert mock_logger.error.call_count >= 2
            assert mock_logger.warning.call_count >= 2