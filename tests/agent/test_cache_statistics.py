"""
Tests for cache statistics tracking functionality.

Tests cache hit/miss tracking, metrics collection, and integration with monitoring.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

# Handle optional Redis dependency
try:
    from agent.cache_manager import CacheManager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    CacheManager = None


@pytest.mark.skipif(not CACHE_AVAILABLE, reason="Redis cache manager not available")
class TestCacheStatisticsTracking:
    """Test cache hit/miss tracking and statistics collection."""

    @pytest.fixture
    def cache_manager(self):
        """Create cache manager instance for testing."""
        if not CACHE_AVAILABLE:
            pytest.skip("Cache manager not available")
        return CacheManager()

    @pytest.mark.asyncio
    async def test_cache_hit_tracking(self, cache_manager):
        """Test that cache hits are properly tracked."""
        # Mock Redis to simulate cache hit
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '{"test": "data"}'
        cache_manager.redis = mock_redis
        
        with patch('agent.cache_manager.cache_operations_total') as mock_counter:
            result = await cache_manager.get_cache("test_key")
            
            assert result == {"test": "data"}
            # Verify cache hit metric was recorded
            mock_counter.labels.assert_called_with(operation="get", result="hit")
            mock_counter.labels().inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_miss_tracking(self, cache_manager):
        """Test that cache misses are properly tracked."""
        # Mock Redis to simulate cache miss
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        cache_manager.redis = mock_redis
        
        with patch('agent.cache_manager.cache_operations_total') as mock_counter:
            result = await cache_manager.get_cache("test_key")
            
            assert result is None
            # Verify cache miss metric was recorded
            mock_counter.labels.assert_called_with(operation="get", result="miss")
            mock_counter.labels().inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_set_tracking(self, cache_manager):
        """Test that cache set operations are properly tracked."""
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.setex.return_value = True
        cache_manager.redis = mock_redis
        
        with patch('agent.cache_manager.cache_operations_total') as mock_counter:
            result = await cache_manager.set_cache("test_key", {"test": "data"})
            
            assert result is True
            # Verify cache set metric was recorded
            mock_counter.labels.assert_called_with(operation="set", result="success")
            mock_counter.labels().inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_delete_tracking(self, cache_manager):
        """Test that cache delete operations are properly tracked."""
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1
        cache_manager.redis = mock_redis
        
        with patch('agent.cache_manager.cache_operations_total') as mock_counter:
            result = await cache_manager.delete_cache("test_key")
            
            assert result is True
            # Verify cache delete metric was recorded
            mock_counter.labels.assert_called_with(operation="delete", result="success")
            mock_counter.labels().inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_error_tracking(self, cache_manager):
        """Test that cache errors are properly tracked."""
        # Mock Redis to raise exception
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = Exception("Redis error")
        cache_manager.redis = mock_redis
        
        with patch('agent.cache_manager.cache_operations_total') as mock_counter:
            result = await cache_manager.get_cache("test_key")
            
            assert result is None
            # Verify cache error metric was recorded
            mock_counter.labels.assert_called_with(operation="get", result="error")
            mock_counter.labels().inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_statistics_calculation(self):
        """Test cache hit rate calculation from metrics."""
        from agent.monitoring import calculate_cache_hit_rate
        
        # Mock Prometheus metrics
        with patch('agent.monitoring.cache_operations_total') as mock_counter:
            # Mock metric values
            mock_counter._value._value = {
                ("get", "hit"): MagicMock(_value=80),
                ("get", "miss"): MagicMock(_value=20),
                ("set", "success"): MagicMock(_value=50),
                ("delete", "success"): MagicMock(_value=10)
            }
            
            hit_rate = await calculate_cache_hit_rate()
            
            # Hit rate should be 80/(80+20) = 0.8
            assert hit_rate == 0.8

    @pytest.mark.asyncio
    async def test_cache_statistics_no_operations(self):
        """Test cache hit rate calculation when no operations have occurred."""
        from agent.monitoring import calculate_cache_hit_rate
        
        # Mock empty metrics
        with patch('agent.monitoring.cache_operations_total') as mock_counter:
            mock_counter._value._value = {}
            
            hit_rate = await calculate_cache_hit_rate()
            
            # Should return 0.0 when no operations
            assert hit_rate == 0.0

    @pytest.mark.asyncio
    async def test_cache_statistics_only_hits(self):
        """Test cache hit rate calculation when only hits occurred."""
        from agent.monitoring import calculate_cache_hit_rate
        
        with patch('agent.monitoring.cache_operations_total') as mock_counter:
            mock_counter._value._value = {
                ("get", "hit"): MagicMock(_value=100)
            }
            
            hit_rate = await calculate_cache_hit_rate()
            
            # Should return 1.0 when only hits
            assert hit_rate == 1.0

    @pytest.mark.asyncio
    async def test_cache_statistics_only_misses(self):
        """Test cache hit rate calculation when only misses occurred."""
        from agent.monitoring import calculate_cache_hit_rate
        
        with patch('agent.monitoring.cache_operations_total') as mock_counter:
            mock_counter._value._value = {
                ("get", "miss"): MagicMock(_value=50)
            }
            
            hit_rate = await calculate_cache_hit_rate()
            
            # Should return 0.0 when only misses
            assert hit_rate == 0.0

    @pytest.mark.asyncio
    async def test_cache_metrics_integration_in_health_endpoint(self):
        """Test that cache metrics are properly integrated in health endpoint."""
        from agent.monitoring import get_system_metrics
        
        with patch('agent.monitoring.calculate_cache_hit_rate') as mock_hit_rate:
            mock_hit_rate.return_value = 0.75
            
            metrics = await get_system_metrics()
            
            assert 'cache_hit_rate' in metrics
            assert metrics['cache_hit_rate'] == 0.75
            mock_hit_rate.assert_called_once()

    @pytest.mark.asyncio
    async def test_vector_search_cache_tracking(self):
        """Test that vector search cache operations are tracked."""
        from agent.tools import vector_search_tool
        from agent.tools import VectorSearchInput
        
        # Mock dependencies
        with patch('agent.tools.generate_embedding') as mock_embedding, \
             patch('agent.tools.cache_manager.get_vector_search_cache') as mock_get_cache, \
             patch('agent.tools.cache_manager.cache_vector_search') as mock_set_cache, \
             patch('agent.tools.vector_search') as mock_search:
            
            mock_embedding.return_value = [0.1] * 1536
            mock_get_cache.return_value = None  # Cache miss
            mock_set_cache.return_value = True
            mock_search.return_value = [{"chunk_id": "1", "content": "test", "score": 0.9, "document_id": "doc1", "document_title": "Test", "document_source": "test.pdf", "metadata": {}}]
            
            input_data = VectorSearchInput(query="test query", limit=5)
            tenant_id = uuid4()
            
            result = await vector_search_tool(input_data, tenant_id)
            
            # Verify cache operations were attempted
            mock_get_cache.assert_called_once()
            mock_set_cache.assert_called_once()
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_hybrid_search_cache_tracking(self):
        """Test that hybrid search cache operations are tracked."""
        from agent.tools import hybrid_search_tool
        from agent.tools import HybridSearchInput
        
        # Mock dependencies
        with patch('agent.tools.generate_embedding') as mock_embedding, \
             patch('agent.tools.cache_manager.get_hybrid_search_cache') as mock_get_cache, \
             patch('agent.tools.hybrid_search') as mock_search:
            
            mock_embedding.return_value = [0.1] * 1536
            mock_get_cache.return_value = [{"chunk_id": "1", "content": "test", "score": 0.9, "document_id": "doc1", "document_title": "Test", "document_source": "test.pdf", "metadata": {}}]  # Cache hit
            mock_search.return_value = []
            
            input_data = HybridSearchInput(query="test query", limit=10, text_weight=0.3)
            tenant_id = uuid4()
            
            result = await hybrid_search_tool(input_data, tenant_id)
            
            # Verify cache hit was used
            mock_get_cache.assert_called_once()
            # Search should not be called due to cache hit
            mock_search.assert_not_called()
            assert len(result) == 1
