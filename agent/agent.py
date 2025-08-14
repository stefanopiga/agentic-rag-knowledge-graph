"""
Main Pydantic AI agent for agentic RAG with knowledge graph, adapted for multi-tenancy.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from uuid import UUID

from pydantic_ai import Agent, RunContext
from dotenv import load_dotenv

from .prompts import SYSTEM_PROMPT
from .providers import get_llm_model
from .tools import (
    vector_search_tool,
    graph_search_tool,
    hybrid_search_tool,
    get_document_tool,
    list_documents_tool,
    get_entity_relationships_tool,
    get_entity_timeline_tool,
    VectorSearchInput,
    GraphSearchInput,
    HybridSearchInput,
    DocumentInput,
    DocumentListInput,
    EntityRelationshipInput,
    EntityTimelineInput
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class AgentDependencies:
    """Dependencies for the agent, including multi-tenancy support."""
    session_id: str
    tenant_id: UUID  # Added for multi-tenancy
    user_id: Optional[str] = None
    search_preferences: Dict[str, Any] = field(default_factory=lambda: {
        "use_vector": True,
        "use_graph": True,
        "default_limit": 10
    })


# Initialize the agent
rag_agent = Agent(
    get_llm_model(),
    deps_type=AgentDependencies,
    system_prompt=SYSTEM_PROMPT
)


# Helper to get tenant_id from context
def _get_tenant_id(ctx: RunContext[AgentDependencies]) -> UUID:
    if not ctx.deps.tenant_id:
        raise ValueError("Tenant ID is required but not found in agent dependencies.")
    return ctx.deps.tenant_id


# Register tools with tenant_id propagation
@rag_agent.tool
async def vector_search(ctx: RunContext[AgentDependencies], query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for relevant information using semantic similarity."""
    tenant_id = _get_tenant_id(ctx)
    input_data = VectorSearchInput(query=query, limit=limit)
    results = await vector_search_tool(input_data, tenant_id)
    return [r.dict() for r in results]

@rag_agent.tool
async def graph_search(ctx: RunContext[AgentDependencies], query: str) -> List[Dict[str, Any]]:
    """Search the knowledge graph for facts and relationships."""
    tenant_id = _get_tenant_id(ctx)
    input_data = GraphSearchInput(query=query)
    results = await graph_search_tool(input_data, tenant_id)
    return [r.dict() for r in results]

@rag_agent.tool
async def hybrid_search(ctx: RunContext[AgentDependencies], query: str, limit: int = 10, text_weight: float = 0.3) -> List[Dict[str, Any]]:
    """Perform both vector and keyword search for comprehensive results."""
    tenant_id = _get_tenant_id(ctx)
    input_data = HybridSearchInput(query=query, limit=limit, text_weight=text_weight)
    results = await hybrid_search_tool(input_data, tenant_id)
    return [r.dict() for r in results]

@rag_agent.tool
async def get_document(ctx: RunContext[AgentDependencies], document_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the complete content of a specific document."""
    tenant_id = _get_tenant_id(ctx)
    input_data = DocumentInput(document_id=document_id)
    document = await get_document_tool(input_data, tenant_id)
    if document:
        # Custom formatting for agent consumption
        return {
            "id": document.get("id"),
            "title": document.get("title"),
            "source": document.get("source"),
            "content": document.get("content"),
            "chunk_count": len(document.get("chunks", [])),
            "created_at": document.get("created_at")
        }
    return None

@rag_agent.tool
async def list_documents(ctx: RunContext[AgentDependencies], limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """List available documents with their metadata."""
    tenant_id = _get_tenant_id(ctx)
    input_data = DocumentListInput(limit=limit, offset=offset)
    documents = await list_documents_tool(input_data, tenant_id)
    return [d.dict() for d in documents]

@rag_agent.tool
async def get_entity_relationships(ctx: RunContext[AgentDependencies], entity_name: str, depth: int = 2) -> Dict[str, Any]:
    """Get all relationships for a specific entity in the knowledge graph."""
    tenant_id = _get_tenant_id(ctx)
    input_data = EntityRelationshipInput(entity_name=entity_name, depth=depth)
    return await get_entity_relationships_tool(input_data, tenant_id)

@rag_agent.tool
async def get_entity_timeline(ctx: RunContext[AgentDependencies], entity_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get the timeline of facts for a specific entity."""
    tenant_id = _get_tenant_id(ctx)
    input_data = EntityTimelineInput(entity_name=entity_name, start_date=start_date, end_date=end_date)
    return await get_entity_timeline_tool(input_data, tenant_id)


def get_agent():
    """Get the configured RAG agent instance."""
    return rag_agent
