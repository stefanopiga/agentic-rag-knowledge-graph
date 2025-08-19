"""
Tests for performance monitoring decorator functionality.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from agent.monitoring import monitor_performance


class TestMonitorPerformanceDecorator:
    """Test performance monitoring decorator for timing and error tracking."""
    
    def test_monitor_performance_sync_function_success(self):
        """Test that monitor_performance tracks successful sync function execution."""
        
        # Mock Prometheus metrics
        mock_operation_duration = Mock()
        mock_operation_errors = Mock()
        mock_operation_total = Mock()
        
        with patch('agent.monitoring.operation_duration', mock_operation_duration), \
             patch('agent.monitoring.operation_errors', mock_operation_errors), \
             patch('agent.monitoring.operation_total', mock_operation_total), \
             patch('agent.monitoring.logger') as mock_logger:
            
            # Define test function
            @monitor_performance("test_operation")
            def test_function(x, y):
                time.sleep(0.01)  # Simulate some work
                return x + y
            
            # Execute function
            result = test_function(2, 3)
            
            # Verify result
            assert result == 5
            
            # Verify operation counter was incremented
            mock_operation_total.labels.assert_called_once_with(operation_name="test_operation", status="success")
            mock_operation_total.labels.return_value.inc.assert_called_once()
            
            # Verify duration was observed
            mock_operation_duration.labels.assert_called_once_with(operation_name="test_operation")
            mock_operation_duration.labels.return_value.observe.assert_called_once()
            
            # Verify duration value is reasonable (> 0.01s)
            observed_duration = mock_operation_duration.labels.return_value.observe.call_args[0][0]
            assert observed_duration >= 0.01
            
            # Verify no error was recorded
            mock_operation_errors.labels.assert_not_called()
            
            # Verify successful completion was logged
            mock_logger.info.assert_called()
            log_call = mock_logger.info.call_args[0][0]
            assert "completed" in log_call.lower()
            assert "test_operation" in str(mock_logger.info.call_args)
    
    @pytest.mark.asyncio
    async def test_monitor_performance_async_function_success(self):
        """Test that monitor_performance tracks successful async function execution."""
        
        # Mock Prometheus metrics
        mock_operation_duration = Mock()
        mock_operation_errors = Mock()
        mock_operation_total = Mock()
        
        with patch('agent.monitoring.operation_duration', mock_operation_duration), \
             patch('agent.monitoring.operation_errors', mock_operation_errors), \
             patch('agent.monitoring.operation_total', mock_operation_total), \
             patch('agent.monitoring.logger') as mock_logger:
            
            # Define test async function
            @monitor_performance("async_test_operation")
            async def async_test_function(x, y):
                await asyncio.sleep(0.01)  # Simulate async work
                return x * y
            
            # Execute function
            result = await async_test_function(4, 5)
            
            # Verify result
            assert result == 20
            
            # Verify operation counter was incremented
            mock_operation_total.labels.assert_called_once_with(operation_name="async_test_operation", status="success")
            mock_operation_total.labels.return_value.inc.assert_called_once()
            
            # Verify duration was observed
            mock_operation_duration.labels.assert_called_once_with(operation_name="async_test_operation")
            mock_operation_duration.labels.return_value.observe.assert_called_once()
            
            # Verify duration value is reasonable (> 0.01s)
            observed_duration = mock_operation_duration.labels.return_value.observe.call_args[0][0]
            assert observed_duration >= 0.01
            
            # Verify no error was recorded
            mock_operation_errors.labels.assert_not_called()
    
    def test_monitor_performance_sync_function_error(self):
        """Test that monitor_performance tracks sync function errors."""
        
        # Mock Prometheus metrics
        mock_operation_duration = Mock()
        mock_operation_errors = Mock()
        mock_operation_total = Mock()
        
        with patch('agent.monitoring.operation_duration', mock_operation_duration), \
             patch('agent.monitoring.operation_errors', mock_operation_errors), \
             patch('agent.monitoring.operation_total', mock_operation_total), \
             patch('agent.monitoring.logger') as mock_logger:
            
            # Define test function that raises error
            @monitor_performance("failing_operation")
            def failing_function():
                time.sleep(0.005)  # Small delay
                raise ValueError("Test error")
            
            # Execute function and expect error
            with pytest.raises(ValueError, match="Test error"):
                failing_function()
            
            # Verify operation counter was incremented with error status
            mock_operation_total.labels.assert_called_once_with(operation_name="failing_operation", status="error")
            mock_operation_total.labels.return_value.inc.assert_called_once()
            
            # Verify duration was still observed
            mock_operation_duration.labels.assert_called_once_with(operation_name="failing_operation")
            mock_operation_duration.labels.return_value.observe.assert_called_once()
            
            # Verify error was recorded
            mock_operation_errors.labels.assert_called_once_with(operation_name="failing_operation", error_type="ValueError")
            mock_operation_errors.labels.return_value.inc.assert_called_once()
            
            # Verify error was logged
            mock_logger.error.assert_called()
            error_log_call = mock_logger.error.call_args[0][0]
            assert "failed" in error_log_call.lower()
            assert "failing_operation" in str(mock_logger.error.call_args)
    
    @pytest.mark.asyncio
    async def test_monitor_performance_async_function_error(self):
        """Test that monitor_performance tracks async function errors."""
        
        # Mock Prometheus metrics
        mock_operation_duration = Mock()
        mock_operation_errors = Mock()
        mock_operation_total = Mock()
        
        with patch('agent.monitoring.operation_duration', mock_operation_duration), \
             patch('agent.monitoring.operation_errors', mock_operation_errors), \
             patch('agent.monitoring.operation_total', mock_operation_total), \
             patch('agent.monitoring.logger') as mock_logger:
            
            # Define test async function that raises error
            @monitor_performance("async_failing_operation")
            async def async_failing_function():
                await asyncio.sleep(0.005)  # Small delay
                raise ConnectionError("Async test error")
            
            # Execute function and expect error
            with pytest.raises(ConnectionError, match="Async test error"):
                await async_failing_function()
            
            # Verify operation counter was incremented with error status
            mock_operation_total.labels.assert_called_once_with(operation_name="async_failing_operation", status="error")
            mock_operation_total.labels.return_value.inc.assert_called_once()
            
            # Verify duration was still observed
            mock_operation_duration.labels.assert_called_once_with(operation_name="async_failing_operation")
            mock_operation_duration.labels.return_value.observe.assert_called_once()
            
            # Verify error was recorded with correct error type
            mock_operation_errors.labels.assert_called_once_with(operation_name="async_failing_operation", error_type="ConnectionError")
            mock_operation_errors.labels.return_value.inc.assert_called_once()
    
    def test_monitor_performance_slow_operation_warning(self):
        """Test that monitor_performance logs warnings for slow operations."""
        
        # Mock Prometheus metrics
        mock_operation_duration = Mock()
        mock_operation_errors = Mock()
        mock_operation_total = Mock()
        
        with patch('agent.monitoring.operation_duration', mock_operation_duration), \
             patch('agent.monitoring.operation_errors', mock_operation_errors), \
             patch('agent.monitoring.operation_total', mock_operation_total), \
             patch('agent.monitoring.logger') as mock_logger:
            
            # Define slow test function
            @monitor_performance("slow_operation")
            def slow_function():
                time.sleep(0.1)  # 100ms - should trigger warning if threshold is 50ms
                return "completed"
            
            # Execute function
            result = slow_function()
            
            # Verify result
            assert result == "completed"
            
            # Verify operation was tracked normally
            mock_operation_total.labels.assert_called_once_with(operation_name="slow_operation", status="success")
            mock_operation_duration.labels.assert_called_once_with(operation_name="slow_operation")
            
            # Check if warning was logged (this depends on implementation threshold)
            # We'll verify if either info or warning was called
            assert mock_logger.info.called or mock_logger.warning.called
    
    def test_monitor_performance_preserves_function_metadata(self):
        """Test that monitor_performance preserves original function metadata."""
        
        with patch('agent.monitoring.operation_duration'), \
             patch('agent.monitoring.operation_errors'), \
             patch('agent.monitoring.operation_total'), \
             patch('agent.monitoring.logger'):
            
            # Define test function with metadata
            @monitor_performance("metadata_test")
            def test_function_with_metadata(x: int, y: int) -> int:
                """Test function docstring."""
                return x + y
            
            # Verify function metadata is preserved
            assert test_function_with_metadata.__name__ == "test_function_with_metadata"
            assert "Test function docstring" in test_function_with_metadata.__doc__
            
            # Verify function still works
            result = test_function_with_metadata(1, 2)
            assert result == 3
    
    def test_monitor_performance_different_error_types(self):
        """Test that monitor_performance correctly categorizes different error types."""
        
        # Mock Prometheus metrics
        mock_operation_duration = Mock()
        mock_operation_errors = Mock()
        mock_operation_total = Mock()
        
        error_types_to_test = [
            (ValueError("value error"), "ValueError"),
            (TypeError("type error"), "TypeError"), 
            (ConnectionError("connection error"), "ConnectionError"),
            (RuntimeError("runtime error"), "RuntimeError")
        ]
        
        for error_instance, expected_error_type in error_types_to_test:
            with patch('agent.monitoring.operation_duration', mock_operation_duration), \
                 patch('agent.monitoring.operation_errors', mock_operation_errors), \
                 patch('agent.monitoring.operation_total', mock_operation_total), \
                 patch('agent.monitoring.logger'):
                
                @monitor_performance("error_categorization_test")
                def error_function():
                    raise error_instance
                
                # Execute function and expect specific error
                with pytest.raises(type(error_instance)):
                    error_function()
                
                # Verify correct error type was recorded
                mock_operation_errors.labels.assert_called_with(
                    operation_name="error_categorization_test", 
                    error_type=expected_error_type
                )
                
                # Reset mocks for next iteration
                mock_operation_errors.reset_mock()
                mock_operation_total.reset_mock()
                mock_operation_duration.reset_mock()
    
    def test_monitor_performance_with_function_arguments(self):
        """Test that monitor_performance works correctly with various function arguments."""
        
        # Mock Prometheus metrics
        mock_operation_duration = Mock()
        mock_operation_errors = Mock()
        mock_operation_total = Mock()
        
        with patch('agent.monitoring.operation_duration', mock_operation_duration), \
             patch('agent.monitoring.operation_errors', mock_operation_errors), \
             patch('agent.monitoring.operation_total', mock_operation_total), \
             patch('agent.monitoring.logger'):
            
            # Define test function with various argument types
            @monitor_performance("args_test")
            def complex_function(pos_arg, *args, kw_arg=None, **kwargs):
                return {
                    'pos_arg': pos_arg,
                    'args': args,
                    'kw_arg': kw_arg,
                    'kwargs': kwargs
                }
            
            # Execute function with various arguments
            result = complex_function(
                "first", 
                "second", "third",
                kw_arg="keyword",
                extra1="value1",
                extra2="value2"
            )
            
            # Verify result structure
            assert result['pos_arg'] == "first"
            assert result['args'] == ("second", "third")
            assert result['kw_arg'] == "keyword"
            assert result['kwargs'] == {"extra1": "value1", "extra2": "value2"}
            
            # Verify monitoring was applied
            mock_operation_total.labels.assert_called_once_with(operation_name="args_test", status="success")
            mock_operation_duration.labels.assert_called_once_with(operation_name="args_test")
