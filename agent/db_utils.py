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
from .monitoring import monitor_performance

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DatabasePool:
    """Manages PostgreSQL connection pool with monitoring and optimization."""
    
    def __init__(self, database_url: Optional[str] = None):
        # Sanitize DATABASE_URL to avoid trailing spaces/quotes issues on Windows/.env
        raw_url = database_url or os.getenv("DATABASE_URL") or ""
        self.database_url = raw_url.strip().strip('"').strip("'")
        if not self.database_url:
            app_env = os.getenv("APP_ENV", "development").lower()
            if app_env in ("production", "prod"):
                raise ValueError("DATABASE_URL environment variable not set")
            # In ambienti non-prod, consenti import senza DB; l'inizializzazione fallirà ma sarà gestita a runtime
        
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
                # Settings aligned with unit tests expectations
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=5,
                    max_size=20,
                    max_inactive_connection_lifetime=300,
                    command_timeout=60
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

                # Test vector extension exists
                vector_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )

                # Test required SQL functions existence (by proname)
                match_chunks_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'match_chunks')"
                )
                hybrid_search_exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'hybrid_search')"
                )

                return {
                    "basic_query": result == 1,
                    "vector_extension": bool(vector_exists),
                    "sql_functions": {
                        "match_chunks": bool(match_chunks_exists),
                        "hybrid_search": bool(hybrid_search_exists),
                    },
                    "response_time_ms": 0,  # Will be updated by metrics
                }
        except Exception as e:
            return {
                "basic_query": False,
                "vector_extension": False,
                "sql_functions": {
                    "match_chunks": False,
                    "hybrid_search": False,
                },
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


# Session Management Functions (simple API expected by tests)
async def create_session(
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timeout_minutes: Optional[int] = None,
    title: str = "New Chat"
) -> str:
    """Create a new chat session (tests expect INSERT INTO sessions)."""
    expires_at: Optional[datetime] = None
    if timeout_minutes is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO sessions (user_id, metadata, expires_at, title)
            VALUES ($1, $2, $3, $4)
            RETURNING id::text
            """,
            user_id,
            json.dumps(metadata or {}),
            expires_at,
            title,
        )
        return result["id"]


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session by ID (tests expect no tenant arg)."""
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT id::text, user_id, title, metadata, created_at, updated_at, expires_at
            FROM sessions
            WHERE id = $1::uuid
            """,
            session_id,
        )
        if result:
            row = dict(result)
            # normalize metadata to dict if stored as JSON string in tests
            if isinstance(row.get("metadata"), str):
                try:
                    row["metadata"] = json.loads(row["metadata"])
                except Exception:
                    pass
            return row
        return None


async def update_session(session_id: str, metadata: Dict[str, Any]) -> bool:
    """Update session metadata."""
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE sessions
            SET metadata = COALESCE(metadata, '{}'::jsonb) || $2::jsonb, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1::uuid
            """,
            session_id,
            json.dumps(metadata)
        )
        return result.split()[-1] != "0"


# Message Management Functions (using rag_engine_chatmessage)
async def add_message(
    session_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Add a message to a session (tests expect INSERT INTO messages)."""
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO messages (session_id, role, content, metadata)
            VALUES ($1::uuid, $2, $3, $4)
            RETURNING id::text
            """,
            session_id,
            role,
            content,
            json.dumps(metadata or {})
        )
        return result["id"]


async def get_session_messages(
    session_id: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get messages for a session."""
    async with db_pool.acquire() as conn:
        query = """
            SELECT id::text, role, content, metadata, created_at
            FROM messages
            WHERE session_id = $1::uuid
            ORDER BY created_at
        """
        params = [session_id]
        if limit:
            query += f" LIMIT ${len(params) + 1}"
            params.append(limit)
        results = await conn.fetch(query, *params)
        return [dict(row) for row in results]


# Document Management Functions
async def get_document(document_id: str, tenant_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
    """
    Get document by ID, optionally enforcing tenant isolation when tenant_id is provided.
    """
    async with db_pool.acquire() as conn:
        if tenant_id is not None:
            result = await conn.fetchrow(
                """
                SELECT id::text, title, source, content, metadata, created_at, updated_at
                FROM documents
                WHERE id = $1::uuid AND tenant_id = $2::uuid
                """,
                document_id,
                tenant_id,
            )
        else:
            result = await conn.fetchrow(
                """
                SELECT id::text, title, source, content, metadata, created_at, updated_at
                FROM documents
                WHERE id = $1::uuid
                """,
                document_id,
            )
        if result:
            row = dict(result)
            if isinstance(row.get("metadata"), str):
                try:
                    row["metadata"] = json.loads(row["metadata"])
                except Exception:
                    pass
            return row
        return None


async def list_documents(
    tenant_id: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    List documents, optionally filtered by tenant.
    """
    async with db_pool.acquire() as conn:
        if tenant_id is not None:
            results = await conn.fetch(
                """
                SELECT * FROM document_summaries
                WHERE tenant_id = $1::uuid
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                tenant_id,
                limit,
                offset,
            )
        else:
            results = await conn.fetch(
                """
                SELECT * FROM document_summaries
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
        return [dict(row) for row in results]


# Vector Search Functions
@monitor_performance("db_vector_search", warning_threshold=0.5)
async def vector_search(*args, **kwargs) -> List[Dict[str, Any]]:
    """Vector similarity search supporting both legacy and tenant-aware signatures.

    Legacy signature (tests/agent): vector_search(embedding, limit=10)
    Tenant-aware signature: vector_search(tenant_id, embedding, limit=10)
    """
    # Parse arguments
    tenant_id: Optional[UUID] = None
    embedding: List[float]
    limit: int = kwargs.get("limit", 10)

    if len(args) >= 2 and not isinstance(args[0], list):
        # tenant-aware call
        tenant_id = args[0]
        embedding = args[1]
    else:
        # legacy call: first arg is embedding list
        embedding = args[0]

    async with db_pool.acquire() as conn:
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        if tenant_id is not None:
            rows = await conn.fetch(
                "SELECT * FROM match_chunks($1, $2::vector, $3)",
                tenant_id,
                embedding_str,
                limit,
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM match_chunks($1::vector, $2)",
                embedding_str,
                limit,
            )
        return [dict(row) for row in rows]


@monitor_performance("db_hybrid_search", warning_threshold=0.5)
async def hybrid_search(
    embedding: List[float],
    query_text: str,
    limit: int = 10,
    text_weight: float = 0.3,
    tenant_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search using the SQL function.

    If tenant_id is provided, uses the tenant-aware function signature:
      hybrid_search(p_tenant_id UUID, query_embedding vector(1536), query_text TEXT, match_count INT, text_weight FLOAT)

    Otherwise, attempts a legacy call without tenant argument (for backward compatibility).
    """
    async with db_pool.acquire() as conn:
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        if tenant_id is not None:
            results = await conn.fetch(
                "SELECT * FROM hybrid_search($1::uuid, $2::vector, $3, $4, $5)",
                tenant_id,
                embedding_str,
                query_text,
                limit,
                text_weight,
            )
        else:
            results = await conn.fetch(
                "SELECT * FROM hybrid_search($1::vector, $2, $3, $4)",
                embedding_str,
                query_text,
                limit,
                text_weight,
            )
        return [dict(row) for row in results]


# Chunk Management Functions
async def get_document_chunks(document_id: str, tenant_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
    """
    Get all chunks for a document. If tenant_id is provided, use tenant-aware function; otherwise, fallback to direct select.
    """
    async with db_pool.acquire() as conn:
        if tenant_id is not None:
            results = await conn.fetch(
                "SELECT * FROM get_document_chunks($1::uuid, $2::uuid)",
                tenant_id,
                document_id,
            )
        else:
            results = await conn.fetch(
                """
                SELECT 
                    id AS chunk_id,
                    content,
                    chunk_index,
                    metadata
                FROM chunks
                WHERE document_id = $1::uuid
                ORDER BY chunk_index
                """,
                document_id,
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
