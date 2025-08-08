"""
Database utilities for PostgreSQL connection and operations, aligned with the multi-tenant schema.
"""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from uuid import UUID
import logging

import asyncpg
from asyncpg.pool import Pool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DatabasePool:
    """Manages PostgreSQL connection pool with monitoring and optimization."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.pool: Optional[Pool] = None
        self._connection_metrics = {
            "total_connections": 0,
            "active_connections": 0,
            "failed_connections": 0,
            "query_count": 0,
            "avg_query_time": 0.0
        }
    
    async def initialize(self):
        if not self.pool:
            try:
                # Optimized pool settings for production workload
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=10,                          # Increased minimum connections
                    max_size=50,                          # Increased maximum connections
                    max_inactive_connection_lifetime=600, # 10 minutes (increased)
                    max_queries=50000,                    # Queries per connection before recycling
                    command_timeout=30,                   # Reduced timeout for faster failure detection
                    server_settings={
                        'search_path': 'public',
                        'application_name': 'agentic_rag_agent'
                    },
                    setup=self._setup_connection,          # Connection setup hook
                    init=self._init_connection             # Connection initialization
                )
                logger.info(f"Database connection pool initialized: {self.pool.get_size()} connections")
                self._connection_metrics["total_connections"] = self.pool.get_size()
            except Exception as e:
                logger.error(f"Failed to create database pool: {e}")
                self._connection_metrics["failed_connections"] += 1
                raise
    
    async def close(self):
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")
    
    async def _setup_connection(self, connection):
        """Setup individual connection with optimizations."""
        # Enable prepared statements for better performance
        await connection.execute("SET plan_cache_mode = force_generic_plan")
        # Optimize for read-heavy workload
        await connection.execute("SET effective_cache_size = '256MB'")
        await connection.execute("SET random_page_cost = 1.1")
        logger.debug("Connection optimizations applied")
    
    async def _init_connection(self, connection):
        """Initialize connection with custom settings."""
        # Set connection-specific settings
        await connection.execute("SET TIME ZONE 'UTC'")
        await connection.execute("SET client_encoding = 'UTF8'")
        logger.debug("Connection initialized")
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire connection with metrics tracking."""
        if not self.pool:
            await self.initialize()
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.pool.acquire() as connection:
                self._connection_metrics["active_connections"] += 1
                yield connection
                
        except Exception as e:
            self._connection_metrics["failed_connections"] += 1
            logger.error(f"Connection acquisition failed: {e}")
            raise
        finally:
            self._connection_metrics["active_connections"] = max(0, self._connection_metrics["active_connections"] - 1)
            query_time = asyncio.get_event_loop().time() - start_time
            self._update_query_metrics(query_time)
    
    def _update_query_metrics(self, query_time: float):
        """Update query performance metrics."""
        self._connection_metrics["query_count"] += 1
        # Rolling average for query time
        current_avg = self._connection_metrics["avg_query_time"]
        count = self._connection_metrics["query_count"]
        self._connection_metrics["avg_query_time"] = (current_avg * (count - 1) + query_time) / count
    
    async def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status and metrics."""
        if not self.pool:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "pool_size": self.pool.get_size(),
            "idle_connections": self.pool.get_idle_size(),
            "metrics": self._connection_metrics.copy(),
            "health": await self._health_check()
        }
    
    async def _health_check(self) -> Dict[str, Any]:
        """Perform pool health check."""
        try:
            async with self.acquire() as conn:
                # Test basic query
                result = await conn.fetchval("SELECT 1")
                # Test vector extension
                await conn.fetchval("SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'")
                
                return {
                    "basic_query": result == 1,
                    "vector_extension": True,
                    "response_time_ms": 0  # Will be updated by metrics
                }
        except Exception as e:
            return {
                "basic_query": False,
                "vector_extension": False,
                "error": str(e)
            }


# Global database pool instance
db_pool = DatabasePool()


async def initialize_database():
    """Initialize database connection pool."""
    await db_pool.initialize()


async def close_database():
    """Close database connection pool."""
    await db_pool.close()


# Session Management Functions (using rag_engine_chatsession)
async def create_session(
    tenant_id: UUID,
    user_id: Optional[int] = None,
    title: str = "New Chat",
    metadata: Optional[Dict[str, Any]] = None,
    expires_at: Optional[datetime] = None
) -> str:
    """
    Create a new chat session in rag_engine_chatsession.
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO rag_engine_chatsession (tenant_id, user_id, title, metadata, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id::text
            """,
            tenant_id,
            user_id,
            title,
            json.dumps(metadata or {}),
            expires_at
        )
        return result["id"]


async def get_session(session_id: str, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get session by ID from rag_engine_chatsession, ensuring tenant isolation.
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT 
                id::text, user_id, title, metadata, created_at, updated_at, expires_at
            FROM rag_engine_chatsession
            WHERE id = $1::uuid AND tenant_id = $2
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """,
            session_id,
            tenant_id
        )
        if result:
            return dict(result)
        return None


async def update_session(session_id: str, tenant_id: UUID, metadata: Dict[str, Any]) -> bool:
    """
    Update session metadata in rag_engine_chatsession.
    """
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE rag_engine_chatsession
            SET metadata = metadata || $3::jsonb, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1::uuid AND tenant_id = $2
            """,
            session_id,
            tenant_id,
            json.dumps(metadata)
        )
        return result.split()[-1] != "0"


# Message Management Functions (using rag_engine_chatmessage)
async def add_message(
    session_id: str,
    tenant_id: UUID,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Add a message to a session in rag_engine_chatmessage.
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO rag_engine_chatmessage (tenant_id, session_id, role, content, metadata)
            VALUES ($1, $2::uuid, $3, $4, $5)
            RETURNING id::text
            """,
            tenant_id,
            session_id,
            role,
            content,
            json.dumps(metadata or {})
        )
        return result["id"]


async def get_session_messages(
    session_id: str,
    tenant_id: UUID,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get messages for a session from rag_engine_chatmessage.
    """
    async with db_pool.acquire() as conn:
        query = """
            SELECT id::text, role, content, metadata, created_at
            FROM rag_engine_chatmessage
            WHERE session_id = $1::uuid AND tenant_id = $2
            ORDER BY created_at
        """
        params = [session_id, tenant_id]
        if limit:
            query += f" LIMIT ${len(params) + 1}"
            params.append(limit)
        
        results = await conn.fetch(query, *params)
        return [dict(row) for row in results]


# Document Management Functions
async def get_document(document_id: str, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get document by ID, ensuring tenant isolation.
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT * FROM documents WHERE id = $1::uuid AND tenant_id = $2",
            document_id,
            tenant_id
        )
        if result:
            return dict(result)
        return None


async def list_documents(
    tenant_id: UUID,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    List documents for a tenant.
    """
    async with db_pool.acquire() as conn:
        results = await conn.fetch(
            "SELECT * FROM document_summaries WHERE tenant_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
            tenant_id,
            limit,
            offset
        )
        return [dict(row) for row in results]


# Vector Search Functions
async def vector_search(
    tenant_id: UUID,
    embedding: List[float],
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search using the match_chunks function.
    """
    async with db_pool.acquire() as conn:
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        results = await conn.fetch(
            "SELECT * FROM match_chunks($1, $2::vector, $3)",
            tenant_id,
            embedding_str,
            limit
        )
        return [dict(row) for row in results]


async def hybrid_search(
    tenant_id: UUID,
    embedding: List[float],
    query_text: str,
    limit: int = 10,
    text_weight: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search using the hybrid_search function.
    """
    async with db_pool.acquire() as conn:
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        results = await conn.fetch(
            "SELECT * FROM hybrid_search($1, $2::vector, $3, $4, $5)",
            tenant_id,
            embedding_str,
            query_text,
            limit,
            text_weight
        )
        return [dict(row) for row in results]


# Chunk Management Functions
async def get_document_chunks(document_id: str, tenant_id: UUID) -> List[Dict[str, Any]]:
    """
    Get all chunks for a document, ensuring tenant isolation.
    """
    async with db_pool.acquire() as conn:
        results = await conn.fetch(
            "SELECT * FROM get_document_chunks($1, $2::uuid)",
            tenant_id,
            document_id
        )
        return [dict(row) for row in results]


# Utility Functions
async def execute_query(query: str, *params) -> List[Dict[str, Any]]:
    """Execute a custom query."""
    async with db_pool.acquire() as conn:
        results = await conn.fetch(query, *params)
        return [dict(row) for row in results]


async def test_connection() -> bool:
    """Test database connection."""
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


async def get_database_status() -> Dict[str, Any]:
    """Get comprehensive database status."""
    return await db_pool.get_pool_status()
