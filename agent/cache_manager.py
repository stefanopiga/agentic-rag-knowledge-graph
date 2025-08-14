"""
Redis cache manager for query results and embeddings.
"""

import os
import json
import hashlib
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import timedelta
import logging

# Optional redis import for test environments without Redis client
try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis
except Exception:  # pragma: no cover
    aioredis = None  # type: ignore
    Redis = None  # type: ignore
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis caching for query results and embeddings."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis: Optional[Redis] = None
        self.default_ttl = timedelta(hours=1)  # 1 hour default TTL
        
        # Cache key prefixes for different data types
        self.VECTOR_SEARCH_PREFIX = "vs:"
        self.GRAPH_SEARCH_PREFIX = "gs:"
        self.HYBRID_SEARCH_PREFIX = "hs:"
        self.EMBEDDING_PREFIX = "emb:"
        self.DOCUMENT_PREFIX = "doc:"
    
    async def initialize(self):
        """Initialize Redis connection."""
        if not self.redis:
            if aioredis is None:
                # In ambienti test senza redis lib, lascia non inizializzato
                logger.warning("redis.asyncio non disponibile; cache disattivata in questo ambiente")
                self.redis = None
                return
            try:
                self.redis = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    retry_on_timeout=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                # Test connection
                await self.redis.ping()
                logger.info("Redis cache manager initialized")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis = None
                # In test/dev non alzare: consenti fallback senza cache
                app_env = os.getenv("APP_ENV", "development").lower()
                if app_env in ("production", "prod"):
                    raise
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Redis connection closed")
    
    def _generate_cache_key(self, prefix: str, tenant_id: str, data: Union[str, Dict, List]) -> str:
        """Generate cache key with tenant isolation."""
        # Create deterministic hash of the data
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        hash_object = hashlib.md5(data_str.encode())
        data_hash = hash_object.hexdigest()
        
        return f"{prefix}{tenant_id}:{data_hash}"
    
    async def set_cache(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[timedelta] = None
    ) -> bool:
        """Set cache value with TTL."""
        if not self.redis:
            return False
        
        try:
            ttl_seconds = int((ttl or self.default_ttl).total_seconds())
            serialized_value = json.dumps(value, default=str)
            
            await self.redis.setex(key, ttl_seconds, serialized_value)
            logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
            return True
        except Exception as e:
            logger.warning(f"Failed to set cache {key}: {e}")
            return False
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value."""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache miss: {key}")
                return None
        except Exception as e:
            logger.warning(f"Failed to get cache {key}: {e}")
            return None
    
    async def delete_cache(self, key: str) -> bool:
        """Delete cache entry."""
        if not self.redis:
            return False
        
        try:
            result = await self.redis.delete(key)
            logger.debug(f"Cache deleted: {key}")
            return result > 0
        except Exception as e:
            logger.warning(f"Failed to delete cache {key}: {e}")
            return False
    
    async def clear_tenant_cache(self, tenant_id: str) -> int:
        """Clear all cache entries for a tenant."""
        if not self.redis:
            return 0
        
        try:
            pattern = f"*{tenant_id}:*"
            keys = await self.redis.keys(pattern)
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"Cleared {deleted} cache entries for tenant {tenant_id}")
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Failed to clear tenant cache {tenant_id}: {e}")
            return 0
    
    # Vector Search Caching
    async def cache_vector_search(
        self, 
        tenant_id: str, 
        embedding: List[float], 
        limit: int, 
        results: List[Dict]
    ) -> bool:
        """Cache vector search results."""
        cache_data = {"embedding": embedding, "limit": limit}
        key = self._generate_cache_key(self.VECTOR_SEARCH_PREFIX, tenant_id, cache_data)
        return await self.set_cache(key, results, ttl=timedelta(minutes=30))
    
    async def get_vector_search_cache(
        self, 
        tenant_id: str, 
        embedding: List[float], 
        limit: int
    ) -> Optional[List[Dict]]:
        """Get cached vector search results."""
        cache_data = {"embedding": embedding, "limit": limit}
        key = self._generate_cache_key(self.VECTOR_SEARCH_PREFIX, tenant_id, cache_data)
        return await self.get_cache(key)
    
    # Graph Search Caching
    async def cache_graph_search(
        self, 
        tenant_id: str, 
        query: str, 
        results: List[Dict]
    ) -> bool:
        """Cache graph search results."""
        key = self._generate_cache_key(self.GRAPH_SEARCH_PREFIX, tenant_id, query)
        return await self.set_cache(key, results, ttl=timedelta(hours=2))
    
    async def get_graph_search_cache(
        self, 
        tenant_id: str, 
        query: str
    ) -> Optional[List[Dict]]:
        """Get cached graph search results."""
        key = self._generate_cache_key(self.GRAPH_SEARCH_PREFIX, tenant_id, query)
        return await self.get_cache(key)
    
    # Hybrid Search Caching
    async def cache_hybrid_search(
        self, 
        tenant_id: str, 
        embedding: List[float], 
        query_text: str,
        limit: int,
        text_weight: float,
        results: List[Dict]
    ) -> bool:
        """Cache hybrid search results."""
        cache_data = {
            "embedding": embedding, 
            "query_text": query_text,
            "limit": limit,
            "text_weight": text_weight
        }
        key = self._generate_cache_key(self.HYBRID_SEARCH_PREFIX, tenant_id, cache_data)
        return await self.set_cache(key, results, ttl=timedelta(minutes=45))
    
    async def get_hybrid_search_cache(
        self, 
        tenant_id: str, 
        embedding: List[float], 
        query_text: str,
        limit: int,
        text_weight: float
    ) -> Optional[List[Dict]]:
        """Get cached hybrid search results."""
        cache_data = {
            "embedding": embedding, 
            "query_text": query_text,
            "limit": limit,
            "text_weight": text_weight
        }
        key = self._generate_cache_key(self.HYBRID_SEARCH_PREFIX, tenant_id, cache_data)
        return await self.get_cache(key)
    
    # Embedding Caching
    async def cache_embedding(
        self, 
        tenant_id: str, 
        text: str, 
        embedding: List[float]
    ) -> bool:
        """Cache text embedding."""
        key = self._generate_cache_key(self.EMBEDDING_PREFIX, tenant_id, text)
        return await self.set_cache(key, embedding, ttl=timedelta(days=1))
    
    async def get_embedding_cache(
        self, 
        tenant_id: str, 
        text: str
    ) -> Optional[List[float]]:
        """Get cached embedding."""
        key = self._generate_cache_key(self.EMBEDDING_PREFIX, tenant_id, text)
        return await self.get_cache(key)
    
    # Document Caching
    async def cache_document(
        self, 
        tenant_id: str, 
        document_id: str, 
        document_data: Dict
    ) -> bool:
        """Cache document data."""
        key = self._generate_cache_key(self.DOCUMENT_PREFIX, tenant_id, document_id)
        return await self.set_cache(key, document_data, ttl=timedelta(hours=6))
    
    async def get_document_cache(
        self, 
        tenant_id: str, 
        document_id: str
    ) -> Optional[Dict]:
        """Get cached document data."""
        key = self._generate_cache_key(self.DOCUMENT_PREFIX, tenant_id, document_id)
        return await self.get_cache(key)
    
    async def invalidate_document_cache(self, tenant_id: str, document_id: str) -> bool:
        """Invalidate document cache when document is updated."""
        key = self._generate_cache_key(self.DOCUMENT_PREFIX, tenant_id, document_id)
        return await self.delete_cache(key)
    
    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """Redis health check."""
        if not self.redis:
            return {"status": "disconnected", "error": "Not initialized"}
        
        try:
            # Test basic operations
            test_key = "health_check_test"
            await self.redis.set(test_key, "test", ex=5)
            value = await self.redis.get(test_key)
            await self.redis.delete(test_key)
            
            # Get Redis info
            info = await self.redis.info()
            
            return {
                "status": "healthy",
                "connected": True,
                "test_passed": value == "test",
                "memory_used": info.get("used_memory_human", "unknown"),
                "uptime": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global cache manager instance
cache_manager = CacheManager()


async def initialize_cache():
    """Initialize cache manager."""
    await cache_manager.initialize()


async def close_cache():
    """Close cache manager."""
    await cache_manager.close()
