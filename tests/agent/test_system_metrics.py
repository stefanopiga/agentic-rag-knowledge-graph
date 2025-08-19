"""
Tests for system metrics collection and calculation functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import time

from agent.monitoring import get_system_metrics


class TestSystemMetrics:
    """Test system metrics collection for health endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_success(self):
        """Test that get_system_metrics returns correct metrics structure."""
        
        # Mock database connection for active sessions
        mock_conn = AsyncMock()
        mock_sessions_result = [{'count': 15}]
        mock_conn.fetchrow = AsyncMock(return_value=mock_sessions_result[0])
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        # Mock psutil for system resources
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 163840000  # 156.25 MB in bytes
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.cpu_percent.return_value = 12.5
        
        # Mock Prometheus metrics
        mock_queries_metric = Mock()
        mock_queries_metric._value._value = 1247
        
        mock_response_time_metric = Mock()
        mock_response_time_metric._sum._value = 61.25  # Total time
        mock_response_time_metric._count._value = 250   # Total requests
        
        mock_cache_hits_metric = Mock()
        mock_cache_hits_metric._value._value = 870
        
        mock_cache_total_metric = Mock()
        mock_cache_total_metric._value._value = 1000
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('psutil.Process', return_value=mock_process), \
             patch('agent.monitoring.rag_queries_total', mock_queries_metric), \
             patch('agent.monitoring.rag_query_duration', mock_response_time_metric), \
             patch('agent.monitoring.cache_operations_total') as mock_cache_ops:
            
            mock_pool.acquire.return_value = mock_ctx
            
            # Setup cache metrics
            mock_cache_ops.labels.side_effect = lambda operation, result: {
                ('get', 'hit'): mock_cache_hits_metric,
                ('get', 'miss'): Mock(_value=Mock(_value=130))
            }.get((operation, result), Mock(_value=Mock(_value=0)))
            
            result = await get_system_metrics()
            
            # Verify result structure
            assert isinstance(result, dict)
            assert 'active_sessions' in result
            assert 'total_queries_today' in result
            assert 'avg_response_time' in result
            assert 'cache_hit_rate' in result
            assert 'memory_usage_mb' in result
            assert 'cpu_usage_percent' in result
            
            # Verify values
            assert result['active_sessions'] == 15
            assert result['total_queries_today'] == 1247
            assert result['avg_response_time'] == 0.245  # 61.25 / 250 = 0.245
            assert result['cache_hit_rate'] == 0.87      # 870 / 1000 = 0.87
            assert result['memory_usage_mb'] == 156.25    # 163840000 / 1024 / 1024
            assert result['cpu_usage_percent'] == 12.5
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_database_error(self):
        """Test get_system_metrics handles database errors gracefully."""
        
        # Mock database connection that fails
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(side_effect=Exception("Database connection failed"))
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        # Mock psutil for system resources
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 163840000
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.cpu_percent.return_value = 12.5
        
        # Mock Prometheus metrics with defaults
        mock_queries_metric = Mock()
        mock_queries_metric._value._value = 0
        
        mock_response_time_metric = Mock()
        mock_response_time_metric._sum._value = 0
        mock_response_time_metric._count._value = 0
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('psutil.Process', return_value=mock_process), \
             patch('agent.monitoring.rag_queries_total', mock_queries_metric), \
             patch('agent.monitoring.rag_query_duration', mock_response_time_metric), \
             patch('agent.monitoring.cache_operations_total') as mock_cache_ops, \
             patch('agent.monitoring.logger') as mock_logger:
            
            mock_pool.acquire.return_value = mock_ctx
            
            # Setup cache metrics
            mock_cache_ops.labels.return_value = Mock(_value=Mock(_value=0))
            
            result = await get_system_metrics()
            
            # Should return default values when database fails
            assert result['active_sessions'] == 0
            assert result['total_queries_today'] == 0
            assert result['avg_response_time'] == 0.0
            assert result['cache_hit_rate'] == 0.0
            assert result['memory_usage_mb'] == 156.25  # psutil still works
            assert result['cpu_usage_percent'] == 12.5
            
            # Should log the error
            mock_logger.warning.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_psutil_error(self):
        """Test get_system_metrics handles psutil errors gracefully."""
        
        # Mock database connection for active sessions
        mock_conn = AsyncMock()
        mock_sessions_result = [{'count': 10}]
        mock_conn.fetchrow = AsyncMock(return_value=mock_sessions_result[0])
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        # Mock psutil that raises exception
        mock_process = Mock()
        mock_process.memory_info.side_effect = Exception("psutil error")
        mock_process.cpu_percent.side_effect = Exception("psutil error")
        
        # Mock Prometheus metrics
        mock_queries_metric = Mock()
        mock_queries_metric._value._value = 500
        
        mock_response_time_metric = Mock()
        mock_response_time_metric._sum._value = 50.0
        mock_response_time_metric._count._value = 100
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('psutil.Process', return_value=mock_process), \
             patch('agent.monitoring.rag_queries_total', mock_queries_metric), \
             patch('agent.monitoring.rag_query_duration', mock_response_time_metric), \
             patch('agent.monitoring.cache_operations_total') as mock_cache_ops, \
             patch('agent.monitoring.logger') as mock_logger:
            
            mock_pool.acquire.return_value = mock_ctx
            
            # Setup cache metrics
            mock_cache_ops.labels.return_value = Mock(_value=Mock(_value=0))
            
            result = await get_system_metrics()
            
            # Should return default values when psutil fails
            assert result['active_sessions'] == 10      # database still works
            assert result['total_queries_today'] == 500
            assert result['avg_response_time'] == 0.5   # 50.0 / 100 = 0.5
            assert result['cache_hit_rate'] == 0.0
            assert result['memory_usage_mb'] == 0.0     # psutil failed
            assert result['cpu_usage_percent'] == 0.0   # psutil failed
            
            # Should log the error
            mock_logger.warning.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_prometheus_edge_cases(self):
        """Test get_system_metrics handles Prometheus metrics edge cases."""
        
        # Mock database connection
        mock_conn = AsyncMock()
        mock_sessions_result = [{'count': 5}]
        mock_conn.fetchrow = AsyncMock(return_value=mock_sessions_result[0])
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        # Mock psutil
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 104857600  # 100 MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.cpu_percent.return_value = 5.0
        
        # Mock Prometheus metrics with edge cases
        mock_queries_metric = Mock()
        mock_queries_metric._value._value = 100
        
        # Test division by zero for response time
        mock_response_time_metric = Mock()
        mock_response_time_metric._sum._value = 10.0
        mock_response_time_metric._count._value = 0  # Zero requests
        
        mock_cache_hits_metric = Mock()
        mock_cache_hits_metric._value._value = 0
        
        mock_cache_miss_metric = Mock()
        mock_cache_miss_metric._value._value = 0
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('psutil.Process', return_value=mock_process), \
             patch('agent.monitoring.rag_queries_total', mock_queries_metric), \
             patch('agent.monitoring.rag_query_duration', mock_response_time_metric), \
             patch('agent.monitoring.cache_operations_total') as mock_cache_ops:
            
            mock_pool.acquire.return_value = mock_ctx
            
            # Setup cache metrics - both hits and misses are 0
            mock_cache_ops.labels.side_effect = lambda operation, result: {
                ('get', 'hit'): mock_cache_hits_metric,
                ('get', 'miss'): mock_cache_miss_metric
            }.get((operation, result), Mock(_value=Mock(_value=0)))
            
            result = await get_system_metrics()
            
            # Should handle edge cases gracefully
            assert result['active_sessions'] == 5
            assert result['total_queries_today'] == 100
            assert result['avg_response_time'] == 0.0    # Should handle division by zero
            assert result['cache_hit_rate'] == 0.0       # Should handle 0/0 case
            assert result['memory_usage_mb'] == 100.0
            assert result['cpu_usage_percent'] == 5.0
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_cache_rate_calculation(self):
        """Test get_system_metrics calculates cache hit rate correctly."""
        
        # Mock database connection
        mock_conn = AsyncMock()
        mock_sessions_result = [{'count': 25}]
        mock_conn.fetchrow = AsyncMock(return_value=mock_sessions_result[0])
        
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_ctx.__aexit__.return_value = None
        
        # Mock psutil
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 209715200  # 200 MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.cpu_percent.return_value = 25.0
        
        # Mock Prometheus metrics
        mock_queries_metric = Mock()
        mock_queries_metric._value._value = 2000
        
        mock_response_time_metric = Mock()
        mock_response_time_metric._sum._value = 150.0
        mock_response_time_metric._count._value = 500
        
        # Test specific cache hit/miss scenario: 750 hits, 250 misses = 75% hit rate
        mock_cache_hits_metric = Mock()
        mock_cache_hits_metric._value._value = 750
        
        mock_cache_miss_metric = Mock()
        mock_cache_miss_metric._value._value = 250
        
        with patch('agent.db_utils.db_pool') as mock_pool, \
             patch('psutil.Process', return_value=mock_process), \
             patch('agent.monitoring.rag_queries_total', mock_queries_metric), \
             patch('agent.monitoring.rag_query_duration', mock_response_time_metric), \
             patch('agent.monitoring.cache_operations_total') as mock_cache_ops:
            
            mock_pool.acquire.return_value = mock_ctx
            
            # Setup cache metrics
            mock_cache_ops.labels.side_effect = lambda operation, result: {
                ('get', 'hit'): mock_cache_hits_metric,
                ('get', 'miss'): mock_cache_miss_metric
            }.get((operation, result), Mock(_value=Mock(_value=0)))
            
            result = await get_system_metrics()
            
            # Verify cache hit rate calculation: 750 / (750 + 250) = 0.75
            assert result['cache_hit_rate'] == 0.75
            assert result['active_sessions'] == 25
            assert result['total_queries_today'] == 2000
            assert result['avg_response_time'] == 0.3    # 150.0 / 500 = 0.3
            assert result['memory_usage_mb'] == 200.0
            assert result['cpu_usage_percent'] == 25.0
