"""
Test suite completo per connessioni database (PostgreSQL e Neo4j).
"""

import pytest
import asyncio
import logging
import os
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from uuid import uuid4, UUID

import asyncpg
from neo4j import GraphDatabase
from dotenv import load_dotenv

from agent.db_utils import DatabasePool, db_pool, test_connection
from agent.graph_utils import GraphitiClient, graph_client

# Setup
load_dotenv()
logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("test_db_session")
class TestPostgreSQLConnections:
    """Test completi per connessioni PostgreSQL."""
    
    @pytest.mark.asyncio
    async def test_basic_connection(self):
        """Test connessione base PostgreSQL."""
        assert db_pool.pool is not None
        async with db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_database_schema_exists(self):
        """Verifica esistenza schema database."""
        async with db_pool.acquire() as conn:
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('documents', 'chunks', 'rag_engine_chatsession', 'rag_engine_chatmessage')
            """)
            table_names = [row['table_name'] for row in tables]
            assert 'documents' in table_names
            assert 'chunks' in table_names
            assert 'rag_engine_chatsession' in table_names
            assert 'rag_engine_chatmessage' in table_names
    
    @pytest.mark.asyncio
    async def test_pgvector_extension(self):
        """Test estensione pgvector."""
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            assert result is not None
            assert result['extname'] == 'vector'
            await conn.execute("SELECT '[1,2,3]'::vector")
    
    @pytest.mark.asyncio
    async def test_transaction_handling(self):
        """Test gestione transazioni."""
        test_session_id = str(uuid4())
        tenant_id = await self._get_default_tenant_id()
        
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO rag_engine_chatsession (id, tenant_id, title)
                    VALUES ($1, $2, 'test_session')
                """, test_session_id, tenant_id)
                result = await conn.fetchrow("SELECT id FROM rag_engine_chatsession WHERE id = $1", test_session_id)
                assert result is not None
            
            result = await conn.fetchrow("SELECT id FROM rag_engine_chatsession WHERE id = $1", test_session_id)
            assert result is not None

    async def _get_default_tenant_id(self) -> UUID:
        async with db_pool.acquire() as conn:
            tenant = await conn.fetchrow("SELECT id FROM accounts_tenant WHERE slug = 'default'")
            if not tenant:
                tenant = await conn.fetchrow("""
                    INSERT INTO accounts_tenant (name, slug) VALUES ('Default Tenant', 'default') RETURNING id
                """)
            return tenant['id']


class TestNeo4jConnections:
    """Test completi per connessioni Neo4j."""
    
    @pytest.fixture(autouse=True)
    async def setup_teardown(self):
        await graph_client.initialize()
        yield
        await self._cleanup_test_data()
    
    async def _cleanup_test_data(self):
        try:
            if graph_client._initialized and graph_client.graphiti:
                async with graph_client.graphiti.driver.session() as session:
                    await session.run("MATCH (n) WHERE n.name CONTAINS 'TEST_' DETACH DELETE n")
        except Exception as e:
            logger.warning(f"Neo4j cleanup failed: {e}")
    
    @pytest.mark.asyncio
    async def test_basic_graph_connection(self):
        """Test connessione base Neo4j."""
        assert graph_client._initialized
        assert graph_client.graphiti is not None
        records, summary, _ = await graph_client.graphiti.driver.execute_query("RETURN 1")
        assert len(records) == 1
        assert summary.counters.nodes_created == 0


class TestDatabaseErrorHandling:
    """Test gestione errori database."""
    
    @pytest.fixture(autouse=True)
    async def setup_teardown(self):
        await db_pool.initialize()
        yield
    
    @pytest.mark.asyncio
    async def test_connection_failure_recovery(self):
        """Test recovery da failure connessione."""
        success = await test_connection()
        assert success is True
        
        graph_success = False
        try:
            tenant_id = await self._get_default_tenant_id()
            if tenant_id:
                await graph_client.search("test", tenant_id)
                graph_success = True
        except Exception as e:
            logger.error(f"Graph connection test in recovery failed: {e}")
            graph_success = False
            
        assert graph_success is True

    @pytest.mark.asyncio
    async def test_invalid_query_handling(self):
        """Test gestione query invalide."""
        async with db_pool.acquire() as conn:
            with pytest.raises(asyncpg.PostgresSyntaxError):
                await conn.execute("INVALID SQL QUERY")

    async def _get_default_tenant_id(self) -> UUID:
        async with db_pool.acquire() as conn:
            tenant = await conn.fetchrow("SELECT id FROM accounts_tenant WHERE slug = 'default'")
            if not tenant:
                tenant = await conn.fetchrow("""
                    INSERT INTO accounts_tenant (name, slug) VALUES ('Default Tenant', 'default') RETURNING id
                """)
            return tenant['id']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
