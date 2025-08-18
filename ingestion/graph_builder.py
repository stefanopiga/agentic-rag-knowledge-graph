"""
Knowledge graph builder for extracting entities and relationships, with multi-tenancy support.
"""

import os
import logging
import warnings
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import asyncio
import re
from uuid import UUID

from graphiti_core import Graphiti
from dotenv import load_dotenv

from .chunker import DocumentChunk

# spaCy imports with fallback
try:
    import spacy
    from spacy.lang.en import English
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    warnings.warn("spaCy not available. Entity extraction will be disabled.")
    spacy = None
    English = None

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
        self._nlp_model = None  # Lazy-loaded spaCy model
        self._nlp_loading_lock = asyncio.Lock()  # Prevent concurrent loading
    
    async def initialize(self):
        if not self._initialized:
            await self.graph_client.initialize()
            await self._create_entity_indexes()
            self._initialized = True
    
    async def close(self):
        """Close graph client connection."""
        if self._initialized:
            await close_graph()
            self._initialized = False

    async def _create_entity_indexes(self):
        """Create necessary indexes for Entity nodes performance."""
        try:
            # Index for tenant isolation and entity lookup
            indexes_queries = [
                # Composite index for tenant + name + type (unique entities per tenant)
                "CREATE INDEX entity_tenant_name_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.tenant_id, e.name, e.type)",
                # Index for tenant isolation
                "CREATE INDEX entity_tenant_idx IF NOT EXISTS FOR (e:Entity) ON (e.tenant_id)",
                # Index for entity name searches
                "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                # Index for entity type filtering
                "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.type)"
            ]
            
            for query in indexes_queries:
                await self.graph_client.graphiti.driver.execute_query(query)
                
            logger.info("Entity indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating entity indexes (may already exist): {e}")

    async def _load_nlp_model(self):
        """Load spaCy model with lazy initialization and thread safety."""
        if self._nlp_model is not None:
            return self._nlp_model
            
        async with self._nlp_loading_lock:
            # Double-check pattern to avoid loading twice
            if self._nlp_model is not None:
                return self._nlp_model
                
            if not SPACY_AVAILABLE:
                logger.warning("spaCy not available. Entity extraction will be skipped.")
                return None
                
            try:
                # Load spaCy model in a thread to avoid blocking the event loop
                def load_model():
                    try:
                        # Try to load the medical model first, fallback to general model
                        try:
                            model = spacy.load("en_core_web_sm")
                            logger.info("Loaded spaCy model: en_core_web_sm")
                            return model
                        except OSError:
                            # Fallback to basic English model
                            logger.warning("en_core_web_sm not found, using basic English model")
                            model = English()
                            # Add basic NER component if available
                            if 'ner' not in model.pipe_names:
                                model.add_pipe('ner')
                            return model
                    except Exception as e:
                        logger.error(f"Failed to load spaCy model: {e}")
                        return None
                
                loop = asyncio.get_event_loop()
                self._nlp_model = await loop.run_in_executor(None, load_model)
                
                if self._nlp_model is None:
                    logger.warning("Could not load any spaCy model. Entity extraction disabled.")
                
                return self._nlp_model
                
            except Exception as e:
                logger.error(f"Error during spaCy model loading: {e}")
                self._nlp_model = None
                return None
    
    async def add_document_to_graph(
        self,
        chunks: List[DocumentChunk],
        document_title: str,
        document_source: str,
        tenant_id: UUID,  # Added for multi-tenancy
        document_metadata: Optional[Dict[str, Any]] = None,
        extract_entities: bool = True,  # New parameter to control entity extraction
        create_relationships: bool = True  # New parameter to control relationship creation
    ) -> Dict[str, Any]:
        """Add document chunks to the knowledge graph for a specific tenant with entity extraction and relationships."""
        if not self._initialized:
            await self.initialize()
        
        if not chunks:
            return {"episodes_created": 0, "entities_created": 0, "relationships_created": 0, "errors": []}
        
        logger.info(f"Adding {len(chunks)} chunks to knowledge graph for document: {document_title} (Tenant: {tenant_id})")
        
        episodes_created = 0
        entities_created = 0
        entities_merged = 0
        relationships_created = 0
        errors = []
        
        # Step 1: Extract entities from chunks if enabled
        processed_chunks = chunks
        if extract_entities:
            try:
                logger.info("Extracting entities from chunks...")
                processed_chunks = await self.extract_entities_from_chunks(chunks)
                logger.info(f"Entity extraction completed for {len(processed_chunks)} chunks")
            except Exception as e:
                error_msg = f"Entity extraction failed: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Step 2: Create Episodes for chunks
        for i, chunk in enumerate(processed_chunks):
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
                        "entities_count": len(chunk.metadata.get('entities', []))
                    }
                )
                episodes_created += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                error_msg = f"Failed to add chunk {chunk.index} to graph: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Step 3: Store entities in graph if entities were extracted
        if extract_entities:
            try:
                # Collect all entities from all chunks
                all_entities = []
                for chunk in processed_chunks:
                    entities = chunk.metadata.get('entities', [])
                    for entity in entities:
                        entity['source_chunk_id'] = f"chunk_{chunk.index}"
                    all_entities.extend(entities)
                
                if all_entities:
                    logger.info(f"Storing {len(all_entities)} entities in graph...")
                    entity_result = await self.store_entities_in_graph(
                        entities=all_entities,
                        document_title=document_title,
                        tenant_id=tenant_id
                    )
                    entities_created = entity_result.get("entities_created", 0)
                    entities_merged = entity_result.get("entities_merged", 0)
                    errors.extend(entity_result.get("errors", []))
                    
                    # Step 4: Create relationships if enabled
                    if create_relationships and len(all_entities) > 1:
                        logger.info("Creating entity relationships...")
                        
                        # Create CO_OCCURS relationships
                        co_occurs_result = await self.create_entity_relationships(
                            entities=all_entities,
                            document_title=document_title,
                            tenant_id=tenant_id
                        )
                        relationships_created += co_occurs_result.get("relationships_created", 0)
                        errors.extend(co_occurs_result.get("errors", []))
                        
                        # Create MENTIONED_IN relationships
                        mentioned_in_result = await self.create_mentioned_in_relationships(
                            entities=all_entities,
                            document_title=document_title,
                            tenant_id=tenant_id
                        )
                        relationships_created += mentioned_in_result.get("relationships_created", 0)
                        errors.extend(mentioned_in_result.get("errors", []))
                        
                        logger.info(f"Relationship creation completed: {relationships_created} relationships created")
                
            except Exception as e:
                error_msg = f"Entity/relationship processing failed: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        logger.info(f"Graph building complete: {episodes_created} episodes, {entities_created + entities_merged} entities, {relationships_created} relationships, {len(errors)} errors")
        return {
            "episodes_created": episodes_created,
            "entities_created": entities_created,
            "entities_merged": entities_merged,
            "relationships_created": relationships_created,
            "total_chunks": len(chunks),
            "total_entities": entities_created + entities_merged,
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
        if not chunks:
            return chunks
            
        # Load spaCy model with lazy initialization
        nlp_model = await self._load_nlp_model()
        if nlp_model is None:
            logger.warning("spaCy model not available. Returning chunks without entity extraction.")
            # Add empty entities list to all chunks if model is not available
            for chunk in chunks:
                if 'entities' not in chunk.metadata:
                    chunk.metadata['entities'] = []
            return chunks
        
        logger.info(f"Extracting entities from {len(chunks)} chunks using spaCy NLP")
        
        processed_chunks = []
        for chunk in chunks:
            try:
                # Skip empty content
                if not chunk.content or not chunk.content.strip():
                    chunk.metadata['entities'] = []
                    processed_chunks.append(chunk)
                    continue
                
                # Process text with spaCy model in executor to avoid blocking
                def extract_entities_sync(text):
                    doc = nlp_model(text)
                    entities = []
                    
                    for ent in doc.ents:
                        # Get confidence score if available, otherwise default
                        confidence = getattr(ent._, 'confidence', 0.8)
                        
                        entity_data = {
                            "name": ent.text.strip(),
                            "type": ent.label_,
                            "start": ent.start_char,
                            "end": ent.end_char,
                            "confidence": float(confidence)
                        }
                        entities.append(entity_data)
                    
                    return entities
                
                # Run entity extraction in executor to avoid blocking async loop
                loop = asyncio.get_event_loop()
                entities = await loop.run_in_executor(None, extract_entities_sync, chunk.content)
                
                # Add entities to chunk metadata (preserving existing metadata)
                chunk.metadata['entities'] = entities
                processed_chunks.append(chunk)
                
                logger.debug(f"Extracted {len(entities)} entities from chunk {chunk.index}")
                
            except Exception as e:
                logger.error(f"Error extracting entities from chunk {chunk.index}: {e}")
                # Add empty entities list on error
                chunk.metadata['entities'] = []
                processed_chunks.append(chunk)
        
        total_entities = sum(len(chunk.metadata.get('entities', [])) for chunk in processed_chunks)
        logger.info(f"Entity extraction complete: {total_entities} entities extracted from {len(chunks)} chunks")
        
        return processed_chunks

    async def store_entities_in_graph(
        self,
        entities: List[Dict[str, Any]],
        document_title: str,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Store extracted entities in Neo4j knowledge graph with tenant isolation."""
        if not self._initialized:
            await self.initialize()
        
        if not entities:
            return {
                "entities_created": 0,
                "entities_merged": 0,
                "errors": []
            }
        
        logger.info(f"Storing {len(entities)} entities in graph for document: {document_title} (Tenant: {tenant_id})")
        
        entities_created = 0
        entities_merged = 0
        errors = []
        
        # Batch size per performance
        batch_size = 25
        
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            batch_result = await self._store_entity_batch(batch, document_title, tenant_id)
            
            entities_created += batch_result["entities_created"]
            entities_merged += batch_result["entities_merged"]
            errors.extend(batch_result["errors"])
        
        logger.info(f"Entity storage complete: {entities_created} created, {entities_merged} merged, {len(errors)} errors")
        
        return {
            "entities_created": entities_created,
            "entities_merged": entities_merged,
            "total_entities": len(entities),
            "errors": errors
        }

    async def _store_entity_batch(
        self,
        entities: List[Dict[str, Any]],
        document_title: str,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Store a batch of entities using Cypher MERGE pattern."""
        entities_created = 0
        entities_merged = 0
        errors = []
        
        # Prepare batch query with MERGE pattern for deduplication
        cypher_query = """
        UNWIND $entities AS entity
        MERGE (e:Entity {
            name: entity.name,
            type: entity.type,
            tenant_id: $tenant_id
        })
        ON CREATE SET
            e.confidence = entity.confidence,
            e.source_chunk_id = entity.source_chunk_id,
            e.start_position = entity.start,
            e.end_position = entity.end,
            e.document_title = $document_title,
            e.created_at = datetime(),
            e.updated_at = datetime(),
            e.occurrence_count = 1
        ON MATCH SET
            e.confidence = CASE 
                WHEN entity.confidence > e.confidence 
                THEN entity.confidence 
                ELSE e.confidence 
            END,
            e.updated_at = datetime(),
            e.occurrence_count = e.occurrence_count + 1
        RETURN 
            count(CASE WHEN e.created_at = e.updated_at THEN 1 END) AS created_count,
            count(CASE WHEN e.created_at <> e.updated_at THEN 1 END) AS merged_count
        """
        
        try:
            # Validate and prepare entities
            valid_entities = []
            for entity in entities:
                try:
                    # Validate required fields
                    if not entity.get("name") or not entity.get("type"):
                        errors.append(f"Entity missing required fields (name/type): {entity}")
                        continue
                    
                    # Clean and prepare entity data
                    clean_entity = {
                        "name": str(entity["name"]).strip(),
                        "type": str(entity["type"]).strip(),
                        "confidence": float(entity.get("confidence", 0.8)),
                        "source_chunk_id": str(entity.get("source_chunk_id", "")),
                        "start": int(entity.get("start", 0)),
                        "end": int(entity.get("end", 0))
                    }
                    
                    # Validate confidence range
                    if not (0.0 <= clean_entity["confidence"] <= 1.0):
                        clean_entity["confidence"] = 0.8
                    
                    valid_entities.append(clean_entity)
                    
                except (ValueError, TypeError) as e:
                    errors.append(f"Invalid entity data: {entity} - {str(e)}")
                    continue
            
            if not valid_entities:
                return {
                    "entities_created": 0,
                    "entities_merged": 0,
                    "errors": errors
                }
            
            # Execute batch query
            records, summary, _ = await self.graph_client.graphiti.driver.execute_query(
                cypher_query,
                entities=valid_entities,
                tenant_id=str(tenant_id),
                document_title=document_title
            )
            
            if records and len(records) > 0:
                result = dict(records[0])
                entities_created = int(result.get("created_count", 0))
                entities_merged = int(result.get("merged_count", 0))
            
            logger.debug(f"Processed batch of {len(valid_entities)} entities: {entities_created} created, {entities_merged} merged")
            
        except Exception as e:
            error_msg = f"Error storing entity batch: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return {
            "entities_created": entities_created,
            "entities_merged": entities_merged,
            "errors": errors
        }

    async def create_entity_relationships(
        self,
        entities: List[Dict[str, Any]],
        document_title: str,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Create CO_OCCURS relationships between entities in the same chunk."""
        if not self._initialized:
            await self.initialize()
        
        if len(entities) < 2:
            return {"relationships_created": 0, "errors": []}
        
        logger.info(f"Creating CO_OCCURS relationships for {len(entities)} entities in document: {document_title}")
        
        relationships_created = 0
        errors = []
        
        # Group entities by source_chunk_id
        entities_by_chunk = {}
        for entity in entities:
            chunk_id = entity.get("source_chunk_id", "unknown")
            if chunk_id not in entities_by_chunk:
                entities_by_chunk[chunk_id] = []
            entities_by_chunk[chunk_id].append(entity)
        
        # Create relationships within each chunk
        for chunk_id, chunk_entities in entities_by_chunk.items():
            if len(chunk_entities) < 2:
                continue
                
            try:
                batch_result = await self._create_co_occurs_batch(
                    chunk_entities, document_title, tenant_id, chunk_id
                )
                relationships_created += batch_result["relationships_created"]
                errors.extend(batch_result["errors"])
                
            except Exception as e:
                error_msg = f"Error creating relationships for chunk {chunk_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        logger.info(f"Relationship creation complete: {relationships_created} CO_OCCURS relationships created")
        
        return {
            "relationships_created": relationships_created,
            "total_entities": len(entities),
            "errors": errors
        }

    async def _create_co_occurs_batch(
        self,
        entities: List[Dict[str, Any]],
        document_title: str,
        tenant_id: UUID,
        chunk_id: str
    ) -> Dict[str, Any]:
        """Create CO_OCCURS relationships for entities in the same chunk."""
        relationships_created = 0
        errors = []
        
        # Calculate relationship strength based on proximity and confidence
        def calculate_weight(entity1, entity2):
            confidence_avg = (entity1.get("confidence", 0.8) + entity2.get("confidence", 0.8)) / 2
            
            # Distance-based weight (closer entities have stronger relationships)
            start1, end1 = entity1.get("start", 0), entity1.get("end", 0)
            start2, end2 = entity2.get("start", 0), entity2.get("end", 0)
            
            if start1 != start2 and end1 != end2:
                distance = min(abs(start1 - end2), abs(start2 - end1))
                distance_factor = max(0.1, 1.0 / (1.0 + distance / 100.0))  # Normalize distance
            else:
                distance_factor = 1.0
            
            return round(confidence_avg * distance_factor, 3)
        
        # Create relationships between all pairs of entities in chunk
        relationship_pairs = []
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                entity1, entity2 = entities[i], entities[j]
                
                # Skip if same entity name (avoid self-references)
                if entity1.get("name") == entity2.get("name"):
                    continue
                
                weight = calculate_weight(entity1, entity2)
                
                relationship_pairs.append({
                    "entity1_name": entity1["name"],
                    "entity1_type": entity1["type"],
                    "entity2_name": entity2["name"],
                    "entity2_type": entity2["type"],
                    "weight": weight,
                    "chunk_id": chunk_id
                })
        
        if not relationship_pairs:
            return {"relationships_created": 0, "errors": []}
        
        # Batch create relationships
        cypher_query = """
        UNWIND $relationships AS rel
        MATCH (e1:Entity {name: rel.entity1_name, type: rel.entity1_type, tenant_id: $tenant_id})
        MATCH (e2:Entity {name: rel.entity2_name, type: rel.entity2_type, tenant_id: $tenant_id})
        MERGE (e1)-[r:CO_OCCURS]->(e2)
        ON CREATE SET
            r.weight = rel.weight,
            r.chunk_id = rel.chunk_id,
            r.document_title = $document_title,
            r.created_at = datetime(),
            r.tenant_id = $tenant_id
        ON MATCH SET
            r.weight = CASE 
                WHEN rel.weight > r.weight THEN rel.weight 
                ELSE r.weight 
            END,
            r.updated_at = datetime()
        RETURN count(r) AS relationships_count
        """
        
        try:
            records, summary, _ = await self.graph_client.graphiti.driver.execute_query(
                cypher_query,
                relationships=relationship_pairs,
                tenant_id=str(tenant_id),
                document_title=document_title
            )
            
            if records and len(records) > 0:
                relationships_created = int(dict(records[0]).get("relationships_count", 0))
            
            logger.debug(f"Created {relationships_created} CO_OCCURS relationships for chunk {chunk_id}")
            
        except Exception as e:
            error_msg = f"Error executing CO_OCCURS batch query: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return {
            "relationships_created": relationships_created,
            "errors": errors
        }

    async def create_mentioned_in_relationships(
        self,
        entities: List[Dict[str, Any]],
        document_title: str,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Create MENTIONED_IN relationships between entities and their source chunks."""
        if not self._initialized:
            await self.initialize()
        
        if not entities:
            return {"relationships_created": 0, "errors": []}
        
        logger.info(f"Creating MENTIONED_IN relationships for {len(entities)} entities")
        
        relationships_created = 0
        errors = []
        
        # Group entities by chunk for batch processing
        entities_by_chunk = {}
        for entity in entities:
            chunk_id = entity.get("source_chunk_id", "unknown")
            if chunk_id not in entities_by_chunk:
                entities_by_chunk[chunk_id] = []
            entities_by_chunk[chunk_id].append(entity)
        
        for chunk_id, chunk_entities in entities_by_chunk.items():
            try:
                batch_result = await self._create_mentioned_in_batch(
                    chunk_entities, document_title, tenant_id, chunk_id
                )
                relationships_created += batch_result["relationships_created"]
                errors.extend(batch_result["errors"])
                
            except Exception as e:
                error_msg = f"Error creating MENTIONED_IN relationships for chunk {chunk_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        logger.info(f"MENTIONED_IN relationship creation complete: {relationships_created} relationships created")
        
        return {
            "relationships_created": relationships_created,
            "total_entities": len(entities),
            "errors": errors
        }

    async def _create_mentioned_in_batch(
        self,
        entities: List[Dict[str, Any]],
        document_title: str,
        tenant_id: UUID,
        chunk_id: str
    ) -> Dict[str, Any]:
        """Create MENTIONED_IN relationships for entities to their source chunk."""
        relationships_created = 0
        errors = []
        
        # Prepare entity data for batch processing
        entity_data = []
        for entity in entities:
            try:
                entity_data.append({
                    "name": entity["name"],
                    "type": entity["type"],
                    "confidence": entity.get("confidence", 0.8),
                    "start_position": entity.get("start", 0),
                    "end_position": entity.get("end", 0),
                    "chunk_index": int(chunk_id.split("_")[-1]) if "_" in chunk_id else 0
                })
            except (ValueError, KeyError) as e:
                errors.append(f"Invalid entity data for MENTIONED_IN: {entity} - {str(e)}")
                continue
        
        if not entity_data:
            return {"relationships_created": 0, "errors": errors}
        
        # Create MENTIONED_IN relationships
        cypher_query = """
        UNWIND $entities AS entity
        MATCH (e:Entity {name: entity.name, type: entity.type, tenant_id: $tenant_id})
        MATCH (episode:Episode) 
        WHERE episode.tenant_id = $tenant_id 
          AND episode.source_description CONTAINS $episode_source_pattern
        MERGE (e)-[r:MENTIONED_IN]->(episode)
        ON CREATE SET
            r.confidence = entity.confidence,
            r.start_position = entity.start_position,
            r.end_position = entity.end_position,
            r.created_at = datetime(),
            r.tenant_id = $tenant_id
        ON MATCH SET
            r.updated_at = datetime()
        RETURN count(r) AS relationships_count
        """
        
        try:
            # Build episode source pattern to match the Episode created for this chunk
            episode_source_pattern = f"Doc: {document_title}, Chunk: {entity_data[0]['chunk_index']}"
            
            records, summary, _ = await self.graph_client.graphiti.driver.execute_query(
                cypher_query,
                entities=entity_data,
                tenant_id=str(tenant_id),
                episode_source_pattern=episode_source_pattern
            )
            
            if records and len(records) > 0:
                relationships_created = int(dict(records[0]).get("relationships_count", 0))
            
            logger.debug(f"Created {relationships_created} MENTIONED_IN relationships for chunk {chunk_id}")
            
        except Exception as e:
            error_msg = f"Error executing MENTIONED_IN batch query: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return {
            "relationships_created": relationships_created,
            "errors": errors
        }

    async def get_related_entities(
        self,
        entity_name: str,
        tenant_id: UUID,
        depth: int = 1
    ) -> Dict[str, Any]:
        """Get entities related to a given entity with tenant isolation."""
        if not self._initialized:
            await self.initialize()
        
        # Delegate to GraphitiClient for graph traversal
        return await self.graph_client.get_related_entities(
            entity_name=entity_name,
            tenant_id=tenant_id,
            depth=min(depth, 3)  # Enforce max depth 3
        )

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
