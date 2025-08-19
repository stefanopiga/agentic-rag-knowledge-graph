# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-18-entity-graph-extraction/spec.md

## Technical Requirements

- **NLP Library Integration**: Utilizzare spaCy con modello pre-trained (en_core_web_sm o en_core_web_lg) per entity extraction, configurare pipeline con NER component
- **Entity Types**: Estrarre PERSON, ORG, GPE, DATE, MONEY, PRODUCT plus custom medical entities se disponibili nel modello
- **Neo4j Integration**: Utilizzare neo4j driver esistente, creare nodi Entity con properties (name, type, tenant_id, confidence, source_chunk_id)
- **Tenant Isolation**: Aggiungere tenant_id property a tutti i nodi e relazioni, filtrare tutte le query Cypher con WHERE n.tenant_id = $tenant_id
- **Entity Deduplication**: Implementare match-or-create pattern per evitare duplicati: MERGE (e:Entity {name: $name, type: $type, tenant_id: $tenant_id})
- **Relationship Creation**: Creare relazioni CO_OCCURS tra entità nello stesso chunk, MENTIONED_IN tra entità e chunks
- **Graph Traversal**: Implementare Cypher queries per get_related_entities con depth limit e tenant filtering
- **Error Handling**: Gestire spaCy model loading failures, Neo4j connection errors, malformed entity data
- **Performance**: Batch entity creation per ridurre round-trips, utilizzare indexes Neo4j su (tenant_id, name, type)
- **Metadata Enrichment**: Aggiungere confidence scores, chunk positions, extraction timestamps alle entità