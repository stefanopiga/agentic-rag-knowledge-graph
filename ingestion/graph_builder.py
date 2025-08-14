"""
Knowledge graph builder for extracting entities and relationships, with multi-tenancy support.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import asyncio
import re
from uuid import UUID

from graphiti_core import Graphiti
from dotenv import load_dotenv

from .chunker import DocumentChunk

try:
    from ..agent.graph_utils import GraphitiClient, close_graph
except (ImportError, ValueError):
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent.graph_utils import GraphitiClient, close_graph

load_dotenv()
logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds knowledge graph from document chunks with tenant awareness."""
    
    def __init__(self):
        self.graph_client = GraphitiClient()
        self._initialized = False
    
    async def initialize(self):
        if not self._initialized:
            await self.graph_client.initialize()
            self._initialized = True
    
    async def close(self):
        """Close graph client connection."""
        if self._initialized:
            await close_graph()
            self._initialized = False
    
    async def add_document_to_graph(
        self,
        chunks: List[DocumentChunk],
        document_title: str,
        document_source: str,
        tenant_id: UUID,  # Added for multi-tenancy
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add document chunks to the knowledge graph for a specific tenant."""
        if not self._initialized:
            await self.initialize()
        
        if not chunks:
            return {"episodes_created": 0, "errors": []}
        
        logger.info(f"Adding {len(chunks)} chunks to knowledge graph for document: {document_title} (Tenant: {tenant_id})")
        
        episodes_created = 0
        errors = []
        
        for i, chunk in enumerate(chunks):
            try:
                episode_id = f"{document_source}_{chunk.index}_{datetime.now().timestamp()}"
                episode_content = self._prepare_episode_content(chunk, document_title)
                
                await self.graph_client.add_episode(
                    episode_id=episode_id,
                    content=episode_content,
                    source=f"Doc: {document_title}, Chunk: {chunk.index}",
                    timestamp=datetime.now(timezone.utc),
                    tenant_id=tenant_id,  # Pass tenant_id
                    metadata={
                        "document_title": document_title,
                        "document_source": document_source,
                        "chunk_index": chunk.index,
                        "original_length": len(chunk.content),
                    }
                )
                episodes_created += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                error_msg = f"Failed to add chunk {chunk.index} to graph: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        logger.info(f"Graph building complete: {episodes_created} episodes created, {len(errors)} errors")
        return {
            "episodes_created": episodes_created,
            "total_chunks": len(chunks),
            "errors": errors
        }

    def _prepare_episode_content(self, chunk: DocumentChunk, document_title: str) -> str:
        """Prepare and truncate episode content if necessary."""
        max_content_length = 6000
        content = chunk.content
        if len(content) > max_content_length:
            content = content[:max_content_length] + "... [TRUNCATED]"
        
        return f"[Doc: {document_title[:50]}]\n\n{content}"

    async def extract_entities_from_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Extract medical entities from chunks and add to metadata."""
        # This is a placeholder for a more sophisticated entity extraction logic.
        # For now, it returns the chunks as is.
        logger.info(f"Skipping entity extraction for {len(chunks)} chunks (placeholder).")
        return chunks

    async def clear_graph(self):
        """Clear all data from the knowledge graph."""
        if not self._initialized:
            await self.initialize()
        
        logger.warning("Clearing knowledge graph...")
        # Direct call to driver to clear all nodes and relationships
        await self.graph_client.graphiti.driver.execute_query("MATCH (n) DETACH DELETE n")
        logger.info("Knowledge graph cleared")

def create_graph_builder() -> GraphBuilder:
    return GraphBuilder()

async def main():
    # Example usage requires a valid tenant_id
    from .chunker import ChunkingConfig, create_chunker
    
    builder = create_graph_builder()
    await builder.initialize()
    
    # You would fetch a tenant_id from your database here
    # For example:
    # async with db_pool.acquire() as conn:
    #     tenant_id = await conn.fetchval("SELECT id FROM accounts_tenant WHERE slug = 'default'")
    
    # Dummy tenant_id for example
    tenant_id = UUID('00000000-0000-0000-0000-000000000000')

    # ... rest of the example usage
    
    await builder.close()

if __name__ == "__main__":
    asyncio.run(main())
