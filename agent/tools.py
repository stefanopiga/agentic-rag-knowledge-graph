"""
Tools for the Pydantic AI agent, adapted for a multi-tenant architecture.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from uuid import UUID

from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .db_utils import (
    vector_search,
    hybrid_search,
    get_document,
    list_documents,
    get_document_chunks
)
from .graph_utils import (
    search_knowledge_graph,
    get_entity_relationships,
    graph_client
)
from .models import ChunkResult, GraphSearchResult, DocumentMetadata
from .providers import get_embedding_client, get_embedding_model
from .cache_manager import cache_manager
from .monitoring import monitor_performance

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize embedding client
embedding_client = get_embedding_client()
EMBEDDING_MODEL = get_embedding_model()


@monitor_performance("embedding_generation", warning_threshold=2.0)
async def generate_embedding(text: str, tenant_id: Optional[str] = None) -> List[float]:
    """Generate embedding for text with caching."""
    try:
        # Check cache first if tenant_id provided
        if tenant_id:
            cached_embedding = await cache_manager.get_embedding_cache(tenant_id, text)
            if cached_embedding:
                logger.debug(f"Embedding cache hit for text: {text[:50]}...")
                return cached_embedding
        
        # Generate embedding via API
        response = await embedding_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        embedding = response.data[0].embedding
        
        # Cache embedding if tenant_id provided
        if tenant_id:
            await cache_manager.cache_embedding(tenant_id, text, embedding)
            logger.debug(f"Embedding cached for text: {text[:50]}...")
        
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


# Tool Input Models
class VectorSearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Maximum number of results")

class GraphSearchInput(BaseModel):
    query: str = Field(..., description="Search query")

class HybridSearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Maximum number of results")
    text_weight: float = Field(default=0.3, description="Weight for text similarity (0-1)")

class DocumentInput(BaseModel):
    document_id: str = Field(..., description="Document ID to retrieve")

class DocumentListInput(BaseModel):
    limit: int = Field(default=20, description="Maximum number of documents")
    offset: int = Field(default=0, description="Number of documents to skip")

class EntityRelationshipInput(BaseModel):
    entity_name: str = Field(..., description="Name of the entity")
    depth: int = Field(default=2, description="Maximum traversal depth")

class EntityTimelineInput(BaseModel):
    entity_name: str = Field(..., description="Name of the entity")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")


# Tool Implementation Functions
@monitor_performance("vector_search", warning_threshold=1.0)
async def vector_search_tool(input_data: VectorSearchInput, tenant_id: UUID) -> List[ChunkResult]:
    """Perform vector similarity search for a specific tenant with caching."""
    try:
        tenant_id_str = str(tenant_id)
        
        # Generate embedding with caching
        embedding = await generate_embedding(input_data.query, tenant_id_str)
        
        # Check search result cache
        cached_results = await cache_manager.get_vector_search_cache(
            tenant_id_str, embedding, input_data.limit
        )
        if cached_results:
            logger.debug(f"Vector search cache hit for query: {input_data.query[:50]}...")
            return [ChunkResult(**r) for r in cached_results]
        
        # Perform search
        results = await vector_search(
            tenant_id=tenant_id,
            embedding=embedding,
            limit=input_data.limit
        )
        
        # Cache results
        await cache_manager.cache_vector_search(
            tenant_id_str, embedding, input_data.limit, results
        )
        logger.debug(f"Vector search results cached for query: {input_data.query[:50]}...")
        
        return [ChunkResult(**r) for r in results]
    except Exception as e:
        logger.error(f"Vector search failed for tenant {tenant_id}: {e}")
        return []

@monitor_performance("graph_search", warning_threshold=2.0)
async def graph_search_tool(input_data: GraphSearchInput, tenant_id: UUID) -> List[GraphSearchResult]:
    """Search the knowledge graph for a specific tenant with caching."""
    try:
        tenant_id_str = str(tenant_id)
        
        # Check cache first
        cached_results = await cache_manager.get_graph_search_cache(
            tenant_id_str, input_data.query
        )
        if cached_results:
            logger.debug(f"Graph search cache hit for query: {input_data.query[:50]}...")
            return [GraphSearchResult(**r) for r in cached_results]
        
        # Perform graph search
        results = await search_knowledge_graph(
            query=input_data.query,
            tenant_id=tenant_id 
        )
        
        # Cache results
        await cache_manager.cache_graph_search(
            tenant_id_str, input_data.query, results
        )
        logger.debug(f"Graph search results cached for query: {input_data.query[:50]}...")
        
        return [GraphSearchResult(**r) for r in results]
    except Exception as e:
        logger.error(f"Graph search failed for tenant {tenant_id}: {e}")
        return []

@monitor_performance("hybrid_search", warning_threshold=1.5)
async def hybrid_search_tool(input_data: HybridSearchInput, tenant_id: UUID) -> List[ChunkResult]:
    """Perform hybrid search for a specific tenant with caching."""
    try:
        tenant_id_str = str(tenant_id)
        
        # Generate embedding with caching
        embedding = await generate_embedding(input_data.query, tenant_id_str)
        
        # Check cache first
        cached_results = await cache_manager.get_hybrid_search_cache(
            tenant_id_str, embedding, input_data.query, 
            input_data.limit, input_data.text_weight
        )
        if cached_results:
            logger.debug(f"Hybrid search cache hit for query: {input_data.query[:50]}...")
            return [ChunkResult(**r) for r in cached_results]
        
        # Perform hybrid search
        results = await hybrid_search(
            tenant_id=tenant_id,
            embedding=embedding,
            query_text=input_data.query,
            limit=input_data.limit,
            text_weight=input_data.text_weight
        )
        
        # Cache results
        await cache_manager.cache_hybrid_search(
            tenant_id_str, embedding, input_data.query,
            input_data.limit, input_data.text_weight, results
        )
        logger.debug(f"Hybrid search results cached for query: {input_data.query[:50]}...")
        
        return [ChunkResult(**r) for r in results]
    except Exception as e:
        logger.error(f"Hybrid search failed for tenant {tenant_id}: {e}")
        return []

async def get_document_tool(input_data: DocumentInput, tenant_id: UUID) -> Optional[Dict[str, Any]]:
    """Retrieve a complete document for a specific tenant."""
    try:
        document = await get_document(input_data.document_id, tenant_id)
        if document:
            chunks = await get_document_chunks(input_data.document_id, tenant_id)
            document["chunks"] = chunks
        return document
    except Exception as e:
        logger.error(f"Document retrieval failed for tenant {tenant_id}: {e}")
        return None

async def list_documents_tool(input_data: DocumentListInput, tenant_id: UUID) -> List[DocumentMetadata]:
    """List available documents for a specific tenant."""
    try:
        documents = await list_documents(
            tenant_id=tenant_id,
            limit=input_data.limit,
            offset=input_data.offset
        )
        return [DocumentMetadata(**d) for d in documents]
    except Exception as e:
        logger.error(f"Document listing failed for tenant {tenant_id}: {e}")
        return []

async def get_entity_relationships_tool(input_data: EntityRelationshipInput, tenant_id: UUID) -> Dict[str, Any]:
    """Get relationships for an entity for a specific tenant."""
    try:
        # Assuming graph_utils is updated to handle tenant_id if necessary
        return await get_entity_relationships(
            entity=input_data.entity_name,
            depth=input_data.depth,
            tenant_id=tenant_id
        )
    except Exception as e:
        logger.error(f"Entity relationship query failed for tenant {tenant_id}: {e}")
        return {"error": str(e)}

async def get_entity_timeline_tool(input_data: EntityTimelineInput, tenant_id: UUID) -> List[Dict[str, Any]]:
    """Get timeline of facts for an entity for a specific tenant."""
    try:
        # Assuming graph_utils is updated to handle tenant_id if necessary
        return await graph_client.get_entity_timeline(
            entity_name=input_data.entity_name,
            start_date=datetime.fromisoformat(input_data.start_date) if input_data.start_date else None,
            end_date=datetime.fromisoformat(input_data.end_date) if input_data.end_date else None,
            tenant_id=tenant_id
        )
    except Exception as e:
        logger.error(f"Entity timeline query failed for tenant {tenant_id}: {e}")
        return []

# Combined search function for agent use
@monitor_performance("comprehensive_search", warning_threshold=3.0)
async def perform_comprehensive_search(
    query: str,
    tenant_id: UUID,
    use_vector: bool = True,
    use_graph: bool = True,
    limit: int = 10
) -> Dict[str, Any]:
    """Perform a comprehensive search using multiple methods for a specific tenant."""
    results = {
        "query": query,
        "vector_results": [],
        "graph_results": [],
    }
    
    tasks = []
    if use_vector:
        tasks.append(vector_search_tool(VectorSearchInput(query=query, limit=limit), tenant_id))
    if use_graph:
        tasks.append(graph_search_tool(GraphSearchInput(query=query), tenant_id))
    
    if tasks:
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        vector_idx = 0
        if use_vector:
            if not isinstance(search_results[vector_idx], Exception):
                results["vector_results"] = search_results[vector_idx]
        
        graph_idx = 1 if use_vector else 0
        if use_graph:
            if not isinstance(search_results[graph_idx], Exception):
                results["graph_results"] = search_results[graph_idx]
    
    results["total_results"] = len(results.get("vector_results", [])) + len(results.get("graph_results", []))
    return results
