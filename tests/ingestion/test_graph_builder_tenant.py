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
