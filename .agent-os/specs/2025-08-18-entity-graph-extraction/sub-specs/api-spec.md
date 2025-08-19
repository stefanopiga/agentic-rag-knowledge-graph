# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-18-entity-graph-extraction/spec.md

## Controllers

### Entity Extraction Functions (ingestion/graph_builder.py)

**Updated Function Signature:**

```python
async def extract_entities_from_chunks(
    self, 
    chunks: List[DocumentChunk]
) -> List[DocumentChunk]
```

**Purpose:** Estrarre entità NLP da chunks e arricchire metadata
**Parameters:** chunks (List[DocumentChunk]): Lista di chunks da processare
**Response:** Lista di chunks con metadata entities arricchiti
**Implementation:**
- Utilizzare spaCy NER per estrarre entità da chunk.content
- Aggiungere entities list a chunk.metadata["entities"]
- Formato entity: {"name": str, "type": str, "start": int, "end": int, "confidence": float}
**Errors:** 
- RuntimeWarning se spaCy model non disponibile
- ValueError per chunks malformati

### Graph Navigation Functions (agent/graph_utils.py)

**Updated Function Signature:**

```python
async def get_related_entities(
    self, 
    entity_name: str, 
    tenant_id: UUID, 
    depth: int = 1
) -> Dict[str, Any]
```

**Purpose:** Trovare entità correlate nel knowledge graph con tenant isolation
**Parameters:**
- entity_name (str): Nome dell'entità di partenza
- tenant_id (UUID): ID tenant per isolamento  
- depth (int, default=1): Profondità massima traversal (1-3)
**Response:** Dict con central_entity, related_entities, relationships, stats
**Implementation:**
- Utilizzare Cypher query per traversal con depth limit
- Filtrare risultati per tenant_id
- Restituire entità correlate con relationship types e confidence scores
**Errors:**
- ValueError per depth > 3 o entity_name vuoto
- Neo4jError per connection failures

### Internal Graph Operations

**New Function:**

```python
async def store_entities_in_graph(
    self,
    entities: List[Dict[str, Any]], 
    chunk_id: str,
    tenant_id: UUID
) -> Dict[str, int]
```

**Purpose:** Salvare entità estratte nel Neo4j graph
**Parameters:** entities list, chunk_id, tenant_id
**Response:** Statistics (entities_created, relationships_created)
**Implementation:**
- Batch create entities con MERGE pattern per deduplication
- Creare relazioni MENTIONED_IN tra entità e chunks
- Creare relazioni CO_OCCURS tra entità dello stesso chunk
**Errors:** Neo4jError per failures, ValueError per dati malformati

## Neo4j Schema Extensions

**New Node Types:**
```cypher
(:Entity {
  name: STRING,
  type: STRING, 
  tenant_id: UUID,
  confidence: FLOAT,
  created_at: DATETIME,
  chunk_count: INT
})
```

**New Relationship Types:**
```cypher
(:Entity)-[:CO_OCCURS {weight: FLOAT, chunk_id: STRING}]->(:Entity)
(:Entity)-[:MENTIONED_IN {position: INT, confidence: FLOAT}]->(:Chunk)
```

**Required Indexes:**
```cypher
CREATE INDEX entity_tenant_name IF NOT EXISTS FOR (e:Entity) ON (e.tenant_id, e.name)
CREATE INDEX entity_type_tenant IF NOT EXISTS FOR (e:Entity) ON (e.type, e.tenant_id)
```