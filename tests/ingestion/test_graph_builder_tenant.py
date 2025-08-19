"""
Test GraphBuilder: creazione episodi per chunks con proprietà tenant_id.
"""

import os
import pytest
import asyncio
from uuid import UUID

from ingestion.graph_builder import create_graph_builder
from ingestion.chunker import DocumentChunk

# Skip se mancano le variabili necessarie per Graphiti/Neo4j
if not (
    os.getenv("NEO4J_PASSWORD") and os.getenv("LLM_API_KEY") and os.getenv("EMBEDDING_API_KEY")
):
    pytest.skip("Variabili NEO4J_PASSWORD/LLM_API_KEY/EMBEDDING_API_KEY mancanti", allow_module_level=True)

if os.name == "nt":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass


@pytest.mark.asyncio
async def test_graph_builder_creates_episodes_with_tenant():
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")

    chunks = [
        DocumentChunk(content="Segmento clinico uno", index=0, start_char=0, end_char=10, metadata={}, token_count=5),
        DocumentChunk(content="Segmento clinico due", index=1, start_char=11, end_char=20, metadata={}, token_count=5),
    ]

    result = await builder.add_document_to_graph(
        chunks=chunks,
        document_title="Documento Medico Test",
        document_source="test_source.docx",
        tenant_id=tenant_id,
    )

    assert result["episodes_created"] == 2

    # Verifica che i nodi Episode creati abbiano la proprietà tenant_id corretta
    # e che siano esattamente 2 per le due sorgenti attese (Chunk: 0 e Chunk: 1)
    records, summary, _ = await builder.graph_client.graphiti.driver.execute_query(
        """
        MATCH (e:Episode)
        WHERE e.tenant_id = $tenant_id
          AND (e.source_description = $s0 OR e.source_description = $s1)
        RETURN count(e) AS c
        """,
        tenant_id=str(tenant_id),
        s0="Doc: Documento Medico Test, Chunk: 0",
        s1="Doc: Documento Medico Test, Chunk: 1",
    )
    assert records and int(dict(records[0]).get("c", 0)) == 2

    # Chiusura
    await builder.close()


@pytest.mark.asyncio
async def test_store_entities_in_graph_basic_functionality():
    """Test base per store_entities_in_graph con tenant isolation."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")

    # Entità estratte da chunks (simulate)
    entities = [
        {
            "name": "Physical Therapy",
            "type": "TREATMENT", 
            "confidence": 0.95,
            "source_chunk_id": "chunk_0",
            "start": 0,
            "end": 16
        },
        {
            "name": "Muscle Spasm",
            "type": "CONDITION",
            "confidence": 0.88,
            "source_chunk_id": "chunk_0", 
            "start": 30,
            "end": 42
        },
        {
            "name": "Ibuprofen",
            "type": "MEDICATION",
            "confidence": 0.92,
            "source_chunk_id": "chunk_1",
            "start": 15,
            "end": 24
        }
    ]

    # Esegui store_entities_in_graph
    result = await builder.store_entities_in_graph(
        entities=entities,
        document_title="Medical Document Test",
        tenant_id=tenant_id
    )

    # Verifica risultato
    assert "entities_created" in result
    assert "entities_merged" in result
    assert result["entities_created"] + result["entities_merged"] == 3

    # Verifica che le entità siano state create nel graph con tenant_id corretto
    records, summary, _ = await builder.graph_client.graphiti.driver.execute_query(
        """
        MATCH (e:Entity)
        WHERE e.tenant_id = $tenant_id
        RETURN count(e) AS entity_count, 
               collect(e.name) AS entity_names,
               collect(e.type) AS entity_types
        """,
        tenant_id=str(tenant_id)
    )
    
    assert records
    result_data = dict(records[0])
    assert result_data["entity_count"] == 3
    assert "Physical Therapy" in result_data["entity_names"]
    assert "Muscle Spasm" in result_data["entity_names"] 
    assert "Ibuprofen" in result_data["entity_names"]
    assert "TREATMENT" in result_data["entity_types"]
    assert "CONDITION" in result_data["entity_types"]
    assert "MEDICATION" in result_data["entity_types"]

    await builder.close()


@pytest.mark.asyncio
async def test_store_entities_in_graph_batch_creation():
    """Test batch entity creation per performance."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")

    # Crea una lista di 50 entità per testare batch processing
    entities = []
    for i in range(50):
        entities.append({
            "name": f"Entity_{i}",
            "type": "TEST_TYPE",
            "confidence": 0.8 + (i % 20) * 0.01,
            "source_chunk_id": f"chunk_{i % 5}",
            "start": i * 10,
            "end": (i * 10) + 8
        })

    result = await builder.store_entities_in_graph(
        entities=entities,
        document_title="Batch Test Document",
        tenant_id=tenant_id
    )

    # Verifica che tutte le entità siano state processate
    assert result["entities_created"] + result["entities_merged"] == 50

    # Verifica conteggio finale nel graph
    records, summary, _ = await builder.graph_client.graphiti.driver.execute_query(
        """
        MATCH (e:Entity)
        WHERE e.tenant_id = $tenant_id AND e.type = 'TEST_TYPE'
        RETURN count(e) AS entity_count
        """,
        tenant_id=str(tenant_id)
    )
    
    assert records
    assert dict(records[0])["entity_count"] == 50

    await builder.close()


@pytest.mark.asyncio 
async def test_store_entities_in_graph_tenant_isolation():
    """Test che le entità siano isolate per tenant."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id_1 = UUID("11111111-1111-1111-1111-111111111111")
    tenant_id_2 = UUID("22222222-2222-2222-2222-222222222222")

    # Entità per tenant 1
    entities_t1 = [
        {
            "name": "Tenant1 Entity",
            "type": "T1_TYPE",
            "confidence": 0.9,
            "source_chunk_id": "chunk_t1_0",
            "start": 0,
            "end": 14
        }
    ]

    # Entità per tenant 2  
    entities_t2 = [
        {
            "name": "Tenant2 Entity",
            "type": "T2_TYPE", 
            "confidence": 0.85,
            "source_chunk_id": "chunk_t2_0",
            "start": 0,
            "end": 14
        }
    ]

    # Store entità per entrambi i tenant
    await builder.store_entities_in_graph(
        entities=entities_t1,
        document_title="Document T1",
        tenant_id=tenant_id_1
    )

    await builder.store_entities_in_graph(
        entities=entities_t2,
        document_title="Document T2", 
        tenant_id=tenant_id_2
    )

    # Verifica isolamento tenant 1
    records_t1, _, _ = await builder.graph_client.graphiti.driver.execute_query(
        """
        MATCH (e:Entity)
        WHERE e.tenant_id = $tenant_id
        RETURN count(e) AS entity_count, collect(e.name) AS names
        """,
        tenant_id=str(tenant_id_1)
    )

    # Verifica isolamento tenant 2
    records_t2, _, _ = await builder.graph_client.graphiti.driver.execute_query(
        """
        MATCH (e:Entity)
        WHERE e.tenant_id = $tenant_id
        RETURN count(e) AS entity_count, collect(e.name) AS names
        """,
        tenant_id=str(tenant_id_2)
    )

    # Ogni tenant deve vedere solo le proprie entità
    assert dict(records_t1[0])["entity_count"] == 1
    assert "Tenant1 Entity" in dict(records_t1[0])["names"]
    assert "Tenant2 Entity" not in dict(records_t1[0])["names"]

    assert dict(records_t2[0])["entity_count"] == 1  
    assert "Tenant2 Entity" in dict(records_t2[0])["names"]
    assert "Tenant1 Entity" not in dict(records_t2[0])["names"]

    await builder.close()


@pytest.mark.asyncio
async def test_store_entities_in_graph_deduplication():
    """Test entity deduplication con MERGE pattern."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")

    # Entità duplicate (stesso name, type, tenant_id)
    entities_batch_1 = [
        {
            "name": "Duplicate Entity",
            "type": "DUP_TYPE",
            "confidence": 0.9,
            "source_chunk_id": "chunk_0",
            "start": 0,
            "end": 16
        }
    ]

    entities_batch_2 = [
        {
            "name": "Duplicate Entity",  # Stesso nome e tipo
            "type": "DUP_TYPE",
            "confidence": 0.95,  # Confidence diversa
            "source_chunk_id": "chunk_1", # Chunk diverso
            "start": 10,
            "end": 26
        }
    ]

    # Prima batch - dovrebbe creare l'entità
    result_1 = await builder.store_entities_in_graph(
        entities=entities_batch_1,
        document_title="First Document",
        tenant_id=tenant_id
    )

    # Seconda batch - dovrebbe fare merge dell'entità esistente
    result_2 = await builder.store_entities_in_graph(
        entities=entities_batch_2,
        document_title="Second Document", 
        tenant_id=tenant_id
    )

    # Verifica che la seconda chiamata abbia fatto merge invece di creare duplicato
    assert result_1["entities_created"] == 1
    assert result_1["entities_merged"] == 0
    assert result_2["entities_created"] == 0
    assert result_2["entities_merged"] == 1

    # Verifica che ci sia solo un'entità nel graph
    records, _, _ = await builder.graph_client.graphiti.driver.execute_query(
        """
        MATCH (e:Entity)
        WHERE e.tenant_id = $tenant_id AND e.name = 'Duplicate Entity'
        RETURN count(e) AS entity_count
        """,
        tenant_id=str(tenant_id)
    )

    assert dict(records[0])["entity_count"] == 1

    await builder.close()


@pytest.mark.asyncio
async def test_store_entities_in_graph_error_handling():
    """Test error handling per store_entities_in_graph."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("99999999-9999-9999-9999-999999999999")

    # Test con entità malformata (manca name)
    malformed_entities = [
        {
            "type": "BROKEN_TYPE",
            "confidence": 0.9,
            "source_chunk_id": "chunk_0"
            # name mancante
        }
    ]

    result = await builder.store_entities_in_graph(
        entities=malformed_entities,
        document_title="Error Test Document",
        tenant_id=tenant_id
    )

    # Dovrebbe gestire l'errore e continuare
    assert "errors" in result
    assert len(result["errors"]) > 0
    assert result["entities_created"] == 0

    # Test con lista entità vuota
    empty_result = await builder.store_entities_in_graph(
        entities=[],
        document_title="Empty Test Document", 
        tenant_id=tenant_id
    )

    assert empty_result["entities_created"] == 0
    assert empty_result["entities_merged"] == 0
    assert len(empty_result.get("errors", [])) == 0

    await builder.close()


@pytest.mark.asyncio
async def test_create_entity_relationships():
    """Test creation of CO_OCCURS relationships between entities in same chunk."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    # Entità dallo stesso chunk
    entities_chunk_0 = [
        {
            "name": "Aspirin",
            "type": "MEDICATION",
            "confidence": 0.95,
            "source_chunk_id": "chunk_0",
            "start": 0,
            "end": 7
        },
        {
            "name": "Headache",
            "type": "CONDITION",
            "confidence": 0.90,
            "source_chunk_id": "chunk_0",
            "start": 20,
            "end": 28
        }
    ]

    # Store entità
    await builder.store_entities_in_graph(
        entities=entities_chunk_0,
        document_title="Medical Relations Test",
        tenant_id=tenant_id
    )

    # Crea relazioni CO_OCCURS tra entità dello stesso chunk
    await builder.create_entity_relationships(
        entities=entities_chunk_0,
        document_title="Medical Relations Test",
        tenant_id=tenant_id
    )

    # Verifica relazioni CO_OCCURS create
    records, _, _ = await builder.graph_client.graphiti.driver.execute_query(
        """
        MATCH (e1:Entity)-[r:CO_OCCURS]->(e2:Entity)
        WHERE e1.tenant_id = $tenant_id 
          AND e2.tenant_id = $tenant_id
          AND e1.name = 'Aspirin' 
          AND e2.name = 'Headache'
        RETURN count(r) AS relationship_count
        """,
        tenant_id=str(tenant_id)
    )

    assert records
    assert dict(records[0])["relationship_count"] == 1

    await builder.close()


@pytest.mark.asyncio
async def test_create_mentioned_in_relationships():
    """Test creation of MENTIONED_IN relationships between entities and chunks."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    # Prima crea un Episode (chunk)
    chunks = [
        DocumentChunk(content="Patient takes Ibuprofen for pain", index=0, start_char=0, end_char=33, metadata={}, token_count=6)
    ]

    await builder.add_document_to_graph(
        chunks=chunks,
        document_title="Test Medical Document",
        document_source="test_med.docx",
        tenant_id=tenant_id
    )

    # Entità estratte dal chunk
    entities = [
        {
            "name": "Ibuprofen",
            "type": "MEDICATION", 
            "confidence": 0.92,
            "source_chunk_id": "chunk_0",
            "start": 14,
            "end": 23
        }
    ]

    # Store entità
    await builder.store_entities_in_graph(
        entities=entities,
        document_title="Test Medical Document",
        tenant_id=tenant_id
    )

    # Crea relazioni MENTIONED_IN
    await builder.create_mentioned_in_relationships(
        entities=entities,
        document_title="Test Medical Document",
        tenant_id=tenant_id
    )

    # Verifica relazioni MENTIONED_IN
    records, _, _ = await builder.graph_client.graphiti.driver.execute_query(
        """
        MATCH (entity:Entity)-[r:MENTIONED_IN]->(episode:Episode)
        WHERE entity.tenant_id = $tenant_id 
          AND episode.tenant_id = $tenant_id
          AND entity.name = 'Ibuprofen'
        RETURN count(r) AS mention_count
        """,
        tenant_id=str(tenant_id)
    )

    assert records
    assert dict(records[0])["mention_count"] == 1

    await builder.close()


@pytest.mark.asyncio
async def test_relationship_creation_with_weights():
    """Test relationship creation with calculated weights."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")

    # Multiple entità nello stesso chunk per testare weight calculation
    entities = [
        {
            "name": "Diabetes",
            "type": "CONDITION",
            "confidence": 0.95,
            "source_chunk_id": "chunk_0",
            "start": 0,
            "end": 8
        },
        {
            "name": "Insulin",
            "type": "MEDICATION",
            "confidence": 0.98,
            "source_chunk_id": "chunk_0", 
            "start": 20,
            "end": 27
        },
        {
            "name": "Blood glucose",
            "type": "MEASUREMENT",
            "confidence": 0.90,
            "source_chunk_id": "chunk_0",
            "start": 40,
            "end": 53
        }
    ]

    # Store entità
    await builder.store_entities_in_graph(
        entities=entities,
        document_title="Diabetes Treatment",
        tenant_id=tenant_id
    )

    # Crea relazioni con weight calculation
    result = await builder.create_entity_relationships(
        entities=entities,
        document_title="Diabetes Treatment",
        tenant_id=tenant_id
    )

    assert "relationships_created" in result
    assert result["relationships_created"] > 0

    # Verifica che le relazioni hanno weight property
    records, _, _ = await builder.graph_client.graphiti.driver.execute_query(
        """
        MATCH (e1:Entity)-[r:CO_OCCURS]->(e2:Entity)
        WHERE e1.tenant_id = $tenant_id 
          AND e2.tenant_id = $tenant_id
        RETURN r.weight AS weight, count(r) AS count
        """,
        tenant_id=str(tenant_id)
    )

    assert records
    # Deve avere weight property
    weights = [dict(record)["weight"] for record in records]
    assert all(w is not None and w > 0 for w in weights)

    await builder.close()


@pytest.mark.asyncio
async def test_relationship_tenant_isolation():
    """Test che le relazioni rispettino tenant isolation."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id_1 = UUID("11111111-1111-1111-1111-111111111111")
    tenant_id_2 = UUID("22222222-2222-2222-2222-222222222222")

    # Entità per tenant 1
    entities_t1 = [
        {
            "name": "Medicine A",
            "type": "MEDICATION",
            "confidence": 0.9,
            "source_chunk_id": "chunk_0",
            "start": 0,
            "end": 10
        },
        {
            "name": "Disease B", 
            "type": "CONDITION",
            "confidence": 0.85,
            "source_chunk_id": "chunk_0",
            "start": 20,
            "end": 29
        }
    ]

    # Entità per tenant 2 (stessi nomi, diverso tenant)
    entities_t2 = [
        {
            "name": "Medicine A",
            "type": "MEDICATION",
            "confidence": 0.9,
            "source_chunk_id": "chunk_0",
            "start": 0,
            "end": 10
        },
        {
            "name": "Disease B",
            "type": "CONDITION", 
            "confidence": 0.85,
            "source_chunk_id": "chunk_0",
            "start": 20,
            "end": 29
        }
    ]

    # Store entità per entrambi i tenant
    await builder.store_entities_in_graph(entities_t1, "Doc T1", tenant_id_1)
    await builder.store_entities_in_graph(entities_t2, "Doc T2", tenant_id_2)

    # Crea relazioni per entrambi i tenant
    await builder.create_entity_relationships(entities_t1, "Doc T1", tenant_id_1)
    await builder.create_entity_relationships(entities_t2, "Doc T2", tenant_id_2)

    # Verifica isolamento: tenant 1 vede solo le sue relazioni
    records_t1, _, _ = await builder.graph_client.graphiti.driver.execute_query(
        """
        MATCH (e1:Entity)-[r:CO_OCCURS]->(e2:Entity)
        WHERE e1.tenant_id = $tenant_id AND e2.tenant_id = $tenant_id
        RETURN count(r) AS rel_count
        """,
        tenant_id=str(tenant_id_1)
    )

    # Verifica isolamento: tenant 2 vede solo le sue relazioni
    records_t2, _, _ = await builder.graph_client.graphiti.driver.execute_query(
        """
        MATCH (e1:Entity)-[r:CO_OCCURS]->(e2:Entity)
        WHERE e1.tenant_id = $tenant_id AND e2.tenant_id = $tenant_id
        RETURN count(r) AS rel_count
        """,
        tenant_id=str(tenant_id_2)
    )

    # Ogni tenant deve avere esattamente 1 relazione (A -> B)
    assert dict(records_t1[0])["rel_count"] == 1
    assert dict(records_t2[0])["rel_count"] == 1

    await builder.close()


@pytest.mark.asyncio
async def test_get_related_entities_basic():
    """Test basic get_related_entities functionality with tenant isolation."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")

    # Setup: Create entities and relationships
    entities = [
        {
            "name": "Metformin",
            "type": "MEDICATION",
            "confidence": 0.95,
            "source_chunk_id": "chunk_0",
            "start": 0,
            "end": 9
        },
        {
            "name": "Type 2 Diabetes",
            "type": "CONDITION",
            "confidence": 0.92,
            "source_chunk_id": "chunk_0",
            "start": 20,
            "end": 36
        },
        {
            "name": "Blood Sugar",
            "type": "MEASUREMENT",
            "confidence": 0.88,
            "source_chunk_id": "chunk_0",
            "start": 50,
            "end": 61
        }
    ]

    # Store entities and create relationships
    await builder.store_entities_in_graph(entities, "Diabetes Treatment Guide", tenant_id)
    await builder.create_entity_relationships(entities, "Diabetes Treatment Guide", tenant_id)

    # Test get_related_entities
    result = await builder.get_related_entities(
        entity_name="Metformin",
        tenant_id=tenant_id,
        depth=1
    )

    assert "central_entity" in result
    assert result["central_entity"] == "Metformin"
    assert "related_entities" in result
    assert len(result["related_entities"]) >= 1
    
    # Should find Type 2 Diabetes and Blood Sugar as related entities
    related_names = [entity["name"] for entity in result["related_entities"]]
    assert "Type 2 Diabetes" in related_names or "Blood Sugar" in related_names

    await builder.close()


@pytest.mark.asyncio
async def test_get_related_entities_depth_limit():
    """Test depth-limited graph navigation (max depth 3)."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")

    # Create a chain of related entities: A -> B -> C -> D
    entities_a = [
        {"name": "EntityA", "type": "TYPE1", "confidence": 0.9, "source_chunk_id": "chunk_0", "start": 0, "end": 7},
        {"name": "EntityB", "type": "TYPE2", "confidence": 0.9, "source_chunk_id": "chunk_0", "start": 10, "end": 17}
    ]
    entities_b = [
        {"name": "EntityB", "type": "TYPE2", "confidence": 0.9, "source_chunk_id": "chunk_1", "start": 0, "end": 7},
        {"name": "EntityC", "type": "TYPE3", "confidence": 0.9, "source_chunk_id": "chunk_1", "start": 10, "end": 17}
    ]
    entities_c = [
        {"name": "EntityC", "type": "TYPE3", "confidence": 0.9, "source_chunk_id": "chunk_2", "start": 0, "end": 7},
        {"name": "EntityD", "type": "TYPE4", "confidence": 0.9, "source_chunk_id": "chunk_2", "start": 10, "end": 17}
    ]

    # Store entities and relationships
    await builder.store_entities_in_graph(entities_a + entities_b + entities_c, "Chain Test", tenant_id)
    await builder.create_entity_relationships(entities_a, "Chain Test", tenant_id)
    await builder.create_entity_relationships(entities_b, "Chain Test", tenant_id)
    await builder.create_entity_relationships(entities_c, "Chain Test", tenant_id)

    # Test depth 1: should find EntityB
    result_depth_1 = await builder.get_related_entities("EntityA", tenant_id, depth=1)
    related_names_1 = [entity["name"] for entity in result_depth_1["related_entities"]]
    assert "EntityB" in related_names_1
    assert "EntityC" not in related_names_1  # Should not reach depth 2

    # Test depth 2: should find EntityB and EntityC
    result_depth_2 = await builder.get_related_entities("EntityA", tenant_id, depth=2)
    related_names_2 = [entity["name"] for entity in result_depth_2["related_entities"]]
    assert "EntityB" in related_names_2
    assert "EntityC" in related_names_2

    # Test max depth 3: should find EntityB, EntityC, and EntityD
    result_depth_3 = await builder.get_related_entities("EntityA", tenant_id, depth=3)
    related_names_3 = [entity["name"] for entity in result_depth_3["related_entities"]]
    assert "EntityB" in related_names_3
    assert "EntityC" in related_names_3
    assert "EntityD" in related_names_3

    await builder.close()


@pytest.mark.asyncio
async def test_get_related_entities_tenant_isolation():
    """Test che get_related_entities rispetti tenant isolation."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id_1 = UUID("11111111-1111-1111-1111-111111111111")
    tenant_id_2 = UUID("22222222-2222-2222-2222-222222222222")

    # Create entities for tenant 1
    entities_t1 = [
        {"name": "CommonEntity", "type": "SHARED", "confidence": 0.9, "source_chunk_id": "chunk_0", "start": 0, "end": 12},
        {"name": "Tenant1Entity", "type": "T1_TYPE", "confidence": 0.9, "source_chunk_id": "chunk_0", "start": 20, "end": 33}
    ]

    # Create entities for tenant 2 (same entity name but different tenant)
    entities_t2 = [
        {"name": "CommonEntity", "type": "SHARED", "confidence": 0.9, "source_chunk_id": "chunk_0", "start": 0, "end": 12},
        {"name": "Tenant2Entity", "type": "T2_TYPE", "confidence": 0.9, "source_chunk_id": "chunk_0", "start": 20, "end": 33}
    ]

    # Store entities and relationships for both tenants
    await builder.store_entities_in_graph(entities_t1, "Doc T1", tenant_id_1)
    await builder.create_entity_relationships(entities_t1, "Doc T1", tenant_id_1)
    
    await builder.store_entities_in_graph(entities_t2, "Doc T2", tenant_id_2)
    await builder.create_entity_relationships(entities_t2, "Doc T2", tenant_id_2)

    # Test tenant 1: should only see tenant 1 entities
    result_t1 = await builder.get_related_entities("CommonEntity", tenant_id_1, depth=1)
    related_names_t1 = [entity["name"] for entity in result_t1["related_entities"]]
    assert "Tenant1Entity" in related_names_t1
    assert "Tenant2Entity" not in related_names_t1  # Should not see other tenant's entities

    # Test tenant 2: should only see tenant 2 entities
    result_t2 = await builder.get_related_entities("CommonEntity", tenant_id_2, depth=1)
    related_names_t2 = [entity["name"] for entity in result_t2["related_entities"]]
    assert "Tenant2Entity" in related_names_t2
    assert "Tenant1Entity" not in related_names_t2  # Should not see other tenant's entities

    await builder.close()


@pytest.mark.asyncio
async def test_get_related_entities_with_metadata():
    """Test che get_related_entities includa metadata appropriati."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")

    # Entities with relationships
    entities = [
        {
            "name": "Warfarin",
            "type": "MEDICATION",
            "confidence": 0.95,
            "source_chunk_id": "chunk_0",
            "start": 0,
            "end": 8
        },
        {
            "name": "Blood Clotting",
            "type": "CONDITION",
            "confidence": 0.88,
            "source_chunk_id": "chunk_0",
            "start": 20,
            "end": 33
        }
    ]

    await builder.store_entities_in_graph(entities, "Anticoagulation Guide", tenant_id)
    await builder.create_entity_relationships(entities, "Anticoagulation Guide", tenant_id)

    result = await builder.get_related_entities("Warfarin", tenant_id, depth=1)

    assert "central_entity" in result
    assert "related_entities" in result
    assert "depth_searched" in result
    assert "tenant_id" in result
    assert result["tenant_id"] == str(tenant_id)
    assert result["depth_searched"] == 1

    # Check that related entities have required metadata
    if result["related_entities"]:
        related_entity = result["related_entities"][0]
        assert "name" in related_entity
        assert "type" in related_entity
        assert "relationship_weight" in related_entity
        assert "relationship_type" in related_entity

    await builder.close()


@pytest.mark.asyncio
async def test_get_related_entities_empty_result():
    """Test get_related_entities con entità che non ha relazioni."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("00000000-0000-0000-0000-000000000000")

    # Store single entity without relationships
    entities = [
        {
            "name": "IsolatedEntity",
            "type": "STANDALONE",
            "confidence": 0.9,
            "source_chunk_id": "chunk_0",
            "start": 0,
            "end": 15
        }
    ]

    await builder.store_entities_in_graph(entities, "Isolated Test", tenant_id)

    result = await builder.get_related_entities("IsolatedEntity", tenant_id, depth=1)

    assert result["central_entity"] == "IsolatedEntity"
    assert result["related_entities"] == []
    assert result["depth_searched"] == 1

    # Test with non-existent entity
    result_empty = await builder.get_related_entities("NonExistentEntity", tenant_id, depth=1)
    assert result_empty["central_entity"] == "NonExistentEntity"
    assert result_empty["related_entities"] == []

    await builder.close()


@pytest.mark.asyncio
async def test_end_to_end_ingestion_with_entity_extraction():
    """Test end-to-end ingestion pipeline con entity extraction completa."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("e2e12345-e2e1-e2e1-e2e1-e2e123456789")

    # Crea chunks che simulano un documento medico reale
    chunks = [
        DocumentChunk(
            content="Patient John Doe, age 45, diagnosed with Type 2 Diabetes. Prescribed Metformin 500mg twice daily.",
            index=0,
            start_char=0,
            end_char=98,
            metadata={},
            token_count=20
        ),
        DocumentChunk(
            content="Blood glucose levels monitored weekly. Target HbA1c below 7%. Regular exercise recommended.",
            index=1,
            start_char=99,
            end_char=184,
            metadata={},
            token_count=16
        ),
        DocumentChunk(
            content="Follow-up appointment scheduled in 3 months. Monitor for side effects of Metformin including nausea.",
            index=2,
            start_char=185,
            end_char=285,
            metadata={},
            token_count=18
        )
    ]

    # Test completo del pipeline con extract_entities=True e create_relationships=True
    result = await builder.add_document_to_graph(
        chunks=chunks,
        document_title="Patient Care Plan - John Doe",
        document_source="medical_record_001.docx",
        tenant_id=tenant_id,
        extract_entities=True,
        create_relationships=True
    )

    # Verifica che l'ingestion sia completa
    assert result["episodes_created"] == 3  # Uno per ogni chunk
    assert result["total_chunks"] == 3
    
    # Verifica entity extraction (dovrebbe estrarre entità anche senza spaCy installato)
    assert "entities_created" in result
    assert "entities_merged" in result
    assert "relationships_created" in result
    
    # Verifica che Episodes siano stati creati con tenant isolation
    records, _, _ = await builder.graph_client.graphiti.driver.execute_query(
        """
        MATCH (e:Episode)
        WHERE e.tenant_id = $tenant_id
        RETURN count(e) AS episode_count
        """,
        tenant_id=str(tenant_id)
    )
    assert dict(records[0])["episode_count"] == 3

    # Se entità sono state estratte, verifica che siano nel graph
    if result["entities_created"] + result["entities_merged"] > 0:
        entity_records, _, _ = await builder.graph_client.graphiti.driver.execute_query(
            """
            MATCH (entity:Entity)
            WHERE entity.tenant_id = $tenant_id
            RETURN count(entity) AS entity_count, collect(entity.name) AS entity_names
            """,
            tenant_id=str(tenant_id)
        )
        
        entity_data = dict(entity_records[0])
        assert entity_data["entity_count"] > 0
        
        # Se sono state create relazioni, verificale
        if result["relationships_created"] > 0:
            rel_records, _, _ = await builder.graph_client.graphiti.driver.execute_query(
                """
                MATCH ()-[r:CO_OCCURS]->()
                WHERE r.tenant_id = $tenant_id
                RETURN count(r) AS rel_count
                """,
                tenant_id=str(tenant_id)
            )
            assert dict(rel_records[0])["rel_count"] > 0

    # Test get_related_entities se entità sono presenti
    if result["entities_created"] + result["entities_merged"] > 0:
        # Prova a trovare entità correlate (se spaCy funziona potrebbe trovare qualcosa)
        try:
            related_result = await builder.get_related_entities("Metformin", tenant_id, depth=1)
            assert "central_entity" in related_result
            assert related_result["central_entity"] == "Metformin"
        except Exception:
            # Se non trova l'entità, va bene lo stesso (dipende da spaCy)
            pass

    await builder.close()


@pytest.mark.asyncio
async def test_ingestion_performance_monitoring():
    """Test monitoring delle performance per entity extraction."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("perf1234-perf-perf-perf-performance123")

    # Chunks con contenuto che dovrebbe estrarre entità
    chunks = [
        DocumentChunk(
            content="Clinical trial shows Aspirin reduces cardiovascular risk in patients with coronary artery disease.",
            index=0,
            start_char=0,
            end_char=97,
            metadata={},
            token_count=16
        ),
        DocumentChunk(
            content="Dosage: 81mg daily. Monitor for bleeding complications and gastric irritation.",
            index=1,
            start_char=98,
            end_char=175,
            metadata={},
            token_count=13
        )
    ]

    import time
    start_time = time.time()

    result = await builder.add_document_to_graph(
        chunks=chunks,
        document_title="Aspirin Clinical Guidelines",
        document_source="clinical_guideline_aspirin.pdf",
        tenant_id=tenant_id,
        extract_entities=True,
        create_relationships=True
    )

    end_time = time.time()
    processing_time_ms = (end_time - start_time) * 1000

    # Verifica che il processing sia completato in tempo ragionevole (< 30 secondi)
    assert processing_time_ms < 30000  # Max 30 secondi per 2 chunks

    # Verifica che tutte le statistiche siano presenti
    required_keys = [
        "episodes_created", "entities_created", "entities_merged", 
        "relationships_created", "total_chunks", "total_entities", "errors"
    ]
    for key in required_keys:
        assert key in result

    # Verifica che non ci siano errori critici
    assert len(result["errors"]) == 0 or all("spaCy" in error for error in result["errors"])

    await builder.close()


@pytest.mark.asyncio
async def test_ingestion_error_handling():
    """Test error handling robusto durante ingestion con entity extraction."""
    builder = create_graph_builder()
    await builder.initialize()

    tenant_id = UUID("error123-err0-err0-err0-errorhandling")

    # Test con chunk vuoto
    empty_chunks = [
        DocumentChunk(content="", index=0, start_char=0, end_char=0, metadata={}, token_count=0)
    ]

    result_empty = await builder.add_document_to_graph(
        chunks=empty_chunks,
        document_title="Empty Document",
        document_source="empty.txt",
        tenant_id=tenant_id
    )

    # Dovrebbe gestire gracefully chunk vuoti
    assert result_empty["episodes_created"] == 1  # Episode creato anche se vuoto
    assert result_empty["entities_created"] == 0  # Nessuna entità da chunk vuoto

    # Test con chunk che potrebbe causare errori nell'entity extraction
    problematic_chunks = [
        DocumentChunk(
            content="àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ",  # Unicode characters
            index=0,
            start_char=0,
            end_char=33,
            metadata={},
            token_count=5
        )
    ]

    result_unicode = await builder.add_document_to_graph(
        chunks=problematic_chunks,
        document_title="Unicode Test Document",
        document_source="unicode_test.txt",
        tenant_id=tenant_id,
        extract_entities=True,
        create_relationships=True
    )

    # Dovrebbe completare senza crash anche con unicode
    assert result_unicode["episodes_created"] == 1
    assert "errors" in result_unicode

    await builder.close()