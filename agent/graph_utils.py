"""
Graph utilities for Neo4j/Graphiti integration, with multi-tenancy support.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import asyncio
from uuid import UUID

from graphiti_core import Graphiti
from graphiti_core.utils.maintenance.graph_data_operations import clear_data
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_client import OpenAIClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from dotenv import load_dotenv

# Load .env without overriding process env (so per-command set vars win)
load_dotenv()

logger = logging.getLogger(__name__)

class GraphitiClient:
    """Manages Graphiti knowledge graph operations with multi-tenancy."""
    
    def __init__(self, neo4j_uri: Optional[str] = None, neo4j_user: Optional[str] = None, neo4j_password: Optional[str] = None):
        # Prefer NEO4J_URI_HOST for esecuzioni su host; fallback a NEO4J_URI
        self.neo4j_uri = (
            neo4j_uri
            or os.getenv("NEO4J_URI_HOST")
            or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        )
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        self.llm_api_key = os.getenv("LLM_API_KEY")
        self.embedding_api_key = os.getenv("EMBEDDING_API_KEY")

        if not self.neo4j_password or not self.llm_api_key or not self.embedding_api_key:
            app_env = os.getenv("APP_ENV", "development").lower()
            if app_env in ("production", "prod"):
                raise ValueError("Missing required environment variables for Neo4j/LLM/Embedding.")
            # In ambienti non-prod permetti import; l'inizializzazione potrà fallire e verrà gestita in runtime

        self.graphiti: Optional[Graphiti] = None
        self._initialized = False
        # In-memory fallback store for episodes when using DummyDriver
        self._episodes_by_tenant: dict[str, list[dict]] = {}

    async def initialize(self):
        if self._initialized:
            return
        
        try:
            llm_config = LLMConfig(api_key=self.llm_api_key, model=os.getenv("LLM_CHOICE", "gpt-4.1-mini"), base_url=os.getenv("LLM_BASE_URL"))
            llm_client = OpenAIClient(config=llm_config)
            embedder = OpenAIEmbedder(config=OpenAIEmbedderConfig(api_key=self.embedding_api_key, embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"), embedding_dim=int(os.getenv("VECTOR_DIMENSION", "1536")), base_url=os.getenv("EMBEDDING_BASE_URL")))
            
            # Try primary URI; on DNS failure fallback to localhost
            candidate_uris = [self.neo4j_uri]
            # Fallback aggressivo: se l'URI usa schema neo4j:// forza bolt://localhost
            if self.neo4j_uri.startswith("neo4j://"):
                candidate_uris = ["bolt://localhost:7687", "bolt://127.0.0.1:7687", self.neo4j_uri]

            last_err: Optional[Exception] = None
            for uri in candidate_uris:
                try:
                    self.graphiti = Graphiti(uri, self.neo4j_user, self.neo4j_password, llm_client=llm_client, embedder=embedder)
                    await self.graphiti.build_indices_and_constraints()
                    self.neo4j_uri = uri
                    last_err = None
                    break
                except Exception as e:
                    logger.error(f"Error initializing Graphiti with URI {uri}: {e}")
                    last_err = e

            if last_err is not None:
                raise last_err
            # Add constraint for tenant_id on Episode nodes
            # Neo4j Community Edition does not support property existence constraints.
            # Use an index instead, compatible with Community and sufficient for filtering.
            try:
                await self.graphiti.driver.execute_query(
                    "CREATE INDEX episode_tenant_id_index IF NOT EXISTS FOR (n:Episode) ON (n.tenant_id)"
                )
            except Exception:
                # Best-effort: ignore index creation failures to avoid blocking startup
                logger.warning("Skipping Episode(tenant_id) index creation; proceeding without it")

            self._initialized = True
            logger.info("Graphiti client initialized successfully.")

            # If DummyDriver, patch basic MATCH/RETURN behavior using in-memory store
            try:
                from graphiti_core.client import DummyDriver  # type: ignore
                if isinstance(self.graphiti.driver, DummyDriver):
                    original_execute = self.graphiti.driver.execute_query
                    episodes_store = self._episodes_by_tenant
                    async def execute_query_patched(query: str, **params):
                        q = query.strip().upper()
                        if q.startswith("MATCH (E:EPISODE)") and "RETURN" in q:
                            tenant = params.get("tenant_id")
                            query_text = params.get("query", "")
                            items = []
                            for ep in episodes_store.get(str(tenant), []):
                                if query_text in ep.get("body", ""):
                                    items.append({
                                        "fact": ep.get("body"),
                                        "uuid": ep.get("name"),
                                        "valid_at": ep.get("reference_time")
                                    })
                            return [items], None, None
                        return await original_execute(query, **params)
                    self.graphiti.driver.execute_query = execute_query_patched  # type: ignore
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            raise

    async def add_episode(self, episode_id: str, content: str, source: str, tenant_id: UUID, timestamp: Optional[datetime] = None, metadata: Optional[Dict[str, Any]] = None):
        if not self._initialized:
            await self.initialize()
        
        from graphiti_core.nodes import EpisodeType
        
        # Add tenant_id to the graph episode
        await self.graphiti.driver.execute_query(
            """
            MERGE (e:Episode {name: $episode_id})
            ON CREATE SET e.source = $source, e.source_description = $source_description,
                          e.reference_time = $reference_time, e.body = $body, e.tenant_id = $tenant_id,
                          e.metadata = $metadata
            """,
            episode_id=episode_id,
            source=EpisodeType.text.value,
            source_description=source,
            reference_time=timestamp or datetime.now(timezone.utc),
            body=content,
            tenant_id=str(tenant_id),
            metadata=json.dumps(metadata or {})
        )
        # Keep an in-memory mirror for DummyDriver to support searches
        key = str(tenant_id)
        self._episodes_by_tenant.setdefault(key, []).append({
            "name": episode_id,
            "body": content,
            "reference_time": timestamp or datetime.now(timezone.utc)
        })
        logger.info(f"Added episode {episode_id} for tenant {tenant_id} to knowledge graph")

    async def search(self, query: str, tenant_id: UUID) -> List[Dict[str, Any]]:
        """Search the knowledge graph with tenant isolation."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # We can't use graphiti.search directly as it doesn't support tenant filtering.
            # Custom Cypher query is needed. This is a simplified search.
            # A full implementation would replicate graphiti's complex search logic.
            results = await self.graphiti.driver.execute_query(
                """
                MATCH (e:Episode)
                WHERE e.tenant_id = $tenant_id AND e.body CONTAINS $query
                RETURN e.body AS fact, e.name as uuid, e.reference_time as valid_at
                LIMIT 10
                """,
                tenant_id=str(tenant_id),
                query=query
            )
            return [dict(record) for record in results[0]]
        except Exception as e:
            logger.error(f"Graph search failed for tenant {tenant_id}: {e}")
            return []

    async def get_related_entities(self, entity_name: str, tenant_id: UUID, depth: int = 1) -> Dict[str, Any]:
        """Get entities related to a given entity with tenant isolation."""
        if not self._initialized:
            await self.initialize()
        
        # This requires a more complex Cypher query to traverse relationships
        # within a tenant's data. Placeholder for now.
        return {
            "central_entity": entity_name,
            "related_facts": [],
            "note": "Tenant-isolated relationship search needs a specific Cypher implementation."
        }
        
    async def get_entity_timeline(self, entity_name: str, tenant_id: UUID, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get timeline of facts for an entity with tenant isolation."""
        if not self._initialized:
            await self.initialize()
            
        query = """
            MATCH (e:Episode)
            WHERE e.tenant_id = $tenant_id AND e.body CONTAINS $entity_name
            RETURN e.body AS fact, e.name as uuid, e.reference_time as valid_at
            ORDER BY e.reference_time DESC
            LIMIT 20
        """
        # Date filtering would be added to the WHERE clause
        # if start_date and end_date were used.
        
        results = await self.graphiti.driver.execute_query(
            query,
            tenant_id=str(tenant_id),
            entity_name=entity_name
        )
        return [dict(record) for record in results[0]]

    async def health_check(self) -> Dict[str, Any]:
        """Basic health check for Neo4j/Graphiti and tenant index presence."""
        if not self._initialized:
            await self.initialize()
        try:
            # Connectivity check
            records, summary, _ = await self.graphiti.driver.execute_query("RETURN 1 AS ok")
            connected = False
            if records:
                try:
                    rec_map = dict(records[0])
                except Exception:
                    # Fallback: access by key if dict conversion fails
                    rec_map = {"ok": records[0]["ok"]} if "ok" in records[0].keys() else {}
                ok_val = rec_map.get("ok")
                connected = ok_val == 1 or ok_val is True

            # Index existence check for Episode(tenant_id)
            tenant_index_exists = False
            try:
                idx_query = (
                    "CALL db.indexes() YIELD labelsOrTypes, properties "
                    "WITH labelsOrTypes, properties "
                    "WHERE 'Episode' IN labelsOrTypes AND 'tenant_id' IN properties "
                    "RETURN count(*) > 0 AS exists"
                )
                idx_records, _, _ = await self.graphiti.driver.execute_query(idx_query)
                if idx_records:
                    try:
                        idx_map = dict(idx_records[0])
                    except Exception:
                        idx_map = {"exists": idx_records[0]["exists"]} if "exists" in idx_records[0].keys() else {}
                    tenant_index_exists = bool(idx_map.get("exists"))
            except Exception:
                # Fallback: SHOW INDEXES syntax (Neo4j 5)
                try:
                    alt_query = (
                        "SHOW INDEXES YIELD labelsOrTypes, properties "
                        "WITH labelsOrTypes, properties "
                        "WHERE 'Episode' IN labelsOrTypes AND 'tenant_id' IN properties "
                        "RETURN count(*) > 0 AS exists"
                    )
                    idx_records, _, _ = await self.graphiti.driver.execute_query(alt_query)
                    if idx_records:
                        try:
                            idx_map = dict(idx_records[0])
                        except Exception:
                            idx_map = {"exists": idx_records[0]["exists"]} if "exists" in idx_records[0].keys() else {}
                        tenant_index_exists = bool(idx_map.get("exists"))
                except Exception:
                    tenant_index_exists = False

            return {
                "connected": connected,
                "tenant_index_exists": tenant_index_exists,
                "uri": self.neo4j_uri,
            }
        except Exception as e:
            logger.error(f"Graph health check failed: {e}")
            return {
                "connected": False,
                "tenant_index_exists": False,
                "uri": self.neo4j_uri,
                "error": str(e),
            }

graph_client = GraphitiClient()

async def initialize_graph():
    await graph_client.initialize()

async def close_graph():
    if graph_client.graphiti:
        await graph_client.graphiti.close()

# Updated convenience functions
async def add_to_knowledge_graph(content: str, source: str, tenant_id: UUID, episode_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
    if not episode_id:
        episode_id = f"episode_{datetime.now(timezone.utc).isoformat()}"
    
    await graph_client.add_episode(
        episode_id=episode_id,
        content=content,
        source=source,
        tenant_id=tenant_id,
        metadata=metadata
    )
    return episode_id

async def search_knowledge_graph(query: str, tenant_id: UUID) -> List[Dict[str, Any]]:
    return await graph_client.search(query, tenant_id)

async def get_entity_relationships(entity: str, tenant_id: UUID, depth: int = 2) -> Dict[str, Any]:
    return await graph_client.get_related_entities(entity, tenant_id, depth=depth)

async def test_graph_connection() -> bool:
    """Test the graph database connection."""
    try:
        if graph_client and graph_client._initialized and graph_client.graphiti:
            # Simple test query compatible with Community Edition
            await graph_client.graphiti.driver.execute_query("RETURN 1 AS ok")
            return True
        return False
    except Exception as e:
        logger.error(f"Graph connection test failed: {e}")
        return False