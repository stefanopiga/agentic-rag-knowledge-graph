"""
Tests for tenant isolation debugging and detailed logging functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from agent.db_utils import (
    _validate_tenant_id, 
    _get_effective_tenant_id,
    match_chunks,
    get_session_messages,
    add_message
)


class TestTenantIsolationLogging:
    """Test detailed logging for tenant isolation debugging."""
    
    def test_validate_tenant_id_logging(self):
        """Test that tenant ID validation produces appropriate debug logs."""
        with patch('agent.db_utils.logger') as mock_logger:
            # Test valid UUID
            tenant_id = uuid4()
            result = _validate_tenant_id(tenant_id)
            assert result == tenant_id
            mock_logger.debug.assert_called_with(f"✓ Valid UUID tenant_id: {tenant_id}")
            
            # Test string conversion
            tenant_str = str(uuid4())
            result = _validate_tenant_id(tenant_str)
            mock_logger.info.assert_called_with(f"✓ Converted string tenant_id '{tenant_str}' to UUID: {result}")
            
            # Test None value
            result = _validate_tenant_id(None)
            assert result is None
            mock_logger.debug.assert_called_with("No tenant_id provided - will use fallback logic")

    def test_validate_tenant_id_error_logging(self):
        """Test that tenant ID validation errors are logged appropriately."""
        with patch('agent.db_utils.logger') as mock_logger:
            # Test invalid string format
            with pytest.raises(ValueError):
                _validate_tenant_id("invalid-uuid")
            
            mock_logger.error.assert_called()
            error_call = mock_logger.error.call_args[0][0]
            assert "✗ Invalid tenant_id format" in error_call
            
            # Test invalid type
            with pytest.raises(ValueError):
                _validate_tenant_id(123)
            
            error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            assert any("✗ Invalid tenant_id type" in call for call in error_calls)

    def test_effective_tenant_id_logging(self):
        """Test that effective tenant ID determination is logged properly."""
        with patch('agent.db_utils.logger') as mock_logger:
            # Test with provided tenant_id
            tenant_id = uuid4()
            result = _get_effective_tenant_id(tenant_id)
            assert result == tenant_id
            mock_logger.debug.assert_called_with(f"✓ Using provided tenant_id: {tenant_id}")

    def test_effective_tenant_id_fallback_logging(self):
        """Test that DEV_TENANT_UUID fallback is logged with context."""
        with patch('agent.db_utils.logger') as mock_logger, \
             patch.dict('os.environ', {"APP_ENV": "development"}):
            
            result = _get_effective_tenant_id(None)
            
            # Should have debug and info logging calls
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            
            assert any("Tenant fallback analysis" in call for call in debug_calls)
            assert any("🔄 Tenant isolation fallback" in call for call in info_calls)

    @pytest.mark.asyncio
    async def test_match_chunks_operation_logging(self):
        """Test that match_chunks operations are logged with tenant context."""
        tenant_id = uuid4()
        embedding = [0.1] * 1536
        limit = 10
        
        mock_conn = AsyncMock()
        mock_results = [{'id': 'chunk1', 'content': 'test'}]
        mock_conn.fetch = AsyncMock(return_value=mock_results)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            results = await match_chunks(tenant_id, embedding, limit)
            
            assert len(results) == 1
            
            # Check that operation was logged
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            
            assert any("🔍 RAG Operation: match_chunks" in call for call in info_calls)
            assert any("Tenant isolation debug: match_chunks" in call for call in debug_calls)

    @pytest.mark.asyncio
    async def test_session_messages_tenant_isolation_logging(self):
        """Test that session message operations log tenant isolation details."""
        tenant_id = uuid4()
        session_id = str(uuid4())
        
        mock_conn = AsyncMock()
        mock_results = [
            {
                'id': 'msg1',
                'role': 'user',
                'content': 'test message',
                'metadata': '{}',
                'created_at': '2024-01-01T00:00:00'
            }
        ]
        mock_conn.fetch = AsyncMock(return_value=mock_results)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            # Test tenant-aware mode
            results = await get_session_messages(tenant_id=tenant_id, session_id=session_id)
            
            assert len(results) == 1
            
            # Check tenant isolation logging
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            
            assert any("💬 Session Operation: Getting messages" in call and "tenant isolation" in call for call in info_calls)
            assert any("Tenant isolation debug: get_session_messages" in call for call in debug_calls)

    @pytest.mark.asyncio
    async def test_session_messages_legacy_mode_logging(self):
        """Test that legacy mode is properly logged."""
        session_id = str(uuid4())
        
        mock_conn = AsyncMock()
        mock_results = []
        mock_conn.fetch = AsyncMock(return_value=mock_results)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            # Test legacy mode (no tenant_id)
            results = await get_session_messages(session_id=session_id)
            
            # Check legacy mode logging
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            
            assert any("legacy mode - no tenant isolation" in call for call in info_calls)
            assert any("legacy mode" in call for call in debug_calls)

    @pytest.mark.asyncio
    async def test_add_message_cross_tenant_violation_logging(self):
        """Test that cross-tenant access attempts are logged as violations."""
        tenant_id = uuid4()
        session_id = str(uuid4())
        
        mock_conn = AsyncMock()
        # Simulate session not found for tenant (cross-tenant access attempt)
        mock_conn.fetchval = AsyncMock(return_value=False)
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('agent.db_utils.logger') as mock_logger:
            mock_pool.acquire.return_value = mock_ctx
            
            with pytest.raises(ValueError, match="Session .* not found for tenant"):
                await add_message(
                    tenant_id=tenant_id,
                    session_id=session_id,
                    role="user",
                    content="test message"
                )
            
            # Check that violation was logged
            error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            
            assert any("✗ Tenant isolation violation" in call for call in error_calls)
            assert any("Cross-tenant access attempt detected" in call for call in debug_calls)


class TestTenantIsolationPerformanceLogging:
    """Test performance and timing logging for tenant operations."""
    
    @pytest.mark.asyncio
    async def test_operation_timing_context_manager(self):
        """Test that operation timing context manager logs appropriately."""
        from agent.db_utils import log_tenant_operation_timing
        
        tenant_id = uuid4()
        
        with patch('agent.db_utils.logger') as mock_logger:
            # Test fast operation
            async with log_tenant_operation_timing("test_operation", tenant_id, test_param="value"):
                await asyncio.sleep(0.01)  # Fast operation
            
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            
            # Should have start and completion logs
            assert any("⏱️ Starting test_operation" in call for call in debug_calls)
            assert any("⏱️ test_operation" in call and "completed in" in call for call in debug_calls)

    @pytest.mark.asyncio
    async def test_slow_operation_warning_logging(self):
        """Test that slow operations trigger warning logs."""
        from agent.db_utils import log_tenant_operation_timing
        
        tenant_id = uuid4()
        
        with patch('agent.db_utils.logger') as mock_logger, \
             patch('time.time', side_effect=[0, 3.0]):  # Simulate 3 second operation
            
            async with log_tenant_operation_timing("slow_operation", tenant_id):
                pass
            
            warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            
            # Should warn about slow operation
            assert any("🐌 Slow operation" in call for call in warning_calls)

    @pytest.mark.asyncio
    async def test_operation_error_timing_logging(self):
        """Test that failed operations log timing information."""
        from agent.db_utils import log_tenant_operation_timing
        
        tenant_id = uuid4()
        
        with patch('agent.db_utils.logger') as mock_logger, \
             patch('time.time', side_effect=[0, 1.5]):  # Simulate 1.5 second operation
            
            with pytest.raises(ValueError):
                async with log_tenant_operation_timing("failing_operation", tenant_id):
                    raise ValueError("Test error")
            
            error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            
            # Should log error with timing
            assert any("💥 failing_operation" in call and "failed after" in call for call in error_calls)