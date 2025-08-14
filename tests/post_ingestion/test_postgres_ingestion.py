import os
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from uuid import UUID

# Aggiungi il percorso del progetto
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.db_utils import db_pool
from ingestion.ingest import DocumentIngestionPipeline
from agent.models import IngestionConfig

load_dotenv()

# --- Fixture a livello di modulo per gestire il pool di connessioni ---

@pytest_asyncio.fixture(scope="function", autouse=True)
async def module_db_pool():
    """Inizializza e chiude il pool per ogni test (evita ScopeMismatch con event_loop function-scoped)."""
    await db_pool.initialize()
    try:
        yield
    finally:
        await db_pool.close()

# --- Fixtures a livello di funzione per garantire l'isolamento dei test ---

@pytest_asyncio.fixture(scope="function")
async def db_conn():
    """Fornisce una connessione al database per un singolo test."""
    async with db_pool.acquire() as connection:
        yield connection

@pytest_asyncio.fixture(scope="function")
async def tenant_id(db_conn) -> UUID:
    """Recupera o crea l'ID del tenant di default per un singolo test."""
    tenant_id_val = await db_conn.fetchval("SELECT id FROM accounts_tenant WHERE slug = 'default' LIMIT 1")
    if tenant_id_val is None:
        tenant_id_val = await db_conn.fetchval("INSERT INTO accounts_tenant (name, slug) VALUES ('Default Tenant', 'default') RETURNING id")
    return tenant_id_val

@pytest_asyncio.fixture(scope="function")
async def ingested_data(db_conn, tenant_id: UUID):
    """Garantisce dati ingeriti per il tenant, altrimenti esegue un'ingestione minima di fallback."""
    # Prova a leggere ultimo documento
    doc_result = await db_conn.fetchrow(
        """
        SELECT id, title 
        FROM documents 
        WHERE tenant_id = $1
        ORDER BY created_at DESC 
        LIMIT 1
        """,
        tenant_id,
    )

    if not doc_result:
        # Ingestione minimale di fallback
        config = IngestionConfig(chunk_size=100, chunk_overlap=20, skip_graph_building=True)
        pipeline = DocumentIngestionPipeline(config=config, documents_folder="documents")
        await pipeline.initialize()
        try:
            await pipeline.ingest_documents(tenant_slug="default")
        finally:
            await pipeline.close()
        # Rileggi dopo ingestione
        doc_result = await db_conn.fetchrow(
            """
            SELECT id, title 
            FROM documents 
            WHERE tenant_id = $1
            ORDER BY created_at DESC 
            LIMIT 1
            """,
            tenant_id,
        )

    assert doc_result is not None, f"Nessun documento trovato per il tenant {tenant_id}. Eseguire l'ingestione prima dei test."

    data = {
        'doc_id': doc_result['id'],
        'doc_title': doc_result['title'],
    }

    data['chunk_count'] = await db_conn.fetchval(
        "SELECT COUNT(*) FROM chunks WHERE document_id = $1 AND tenant_id = $2",
        data['doc_id'],
        tenant_id,
    )

    assert data.get('chunk_count', 0) > 0, f"Il documento '{data.get('doc_title')}' non ha chunk associati."
    return data

# --- Suite di Test ---

@pytest.mark.asyncio
class TestPostgresIngestion:

    async def test_document_exists(self, ingested_data):
        """Verifica che i dati del documento siano stati caricati correttamente."""
        assert ingested_data.get('doc_id') is not None
        assert ingested_data.get('doc_title') is not None
        print(f"✅ Documento '{ingested_data['doc_title']}' (ID: {ingested_data['doc_id']}) trovato.")

    async def test_chunk_count_correct(self, ingested_data):
        """Verifica che il numero di chunk sia corretto."""
        assert ingested_data.get('chunk_count') > 0
        print(f"✅ Trovati {ingested_data['chunk_count']} chunk per il documento, come atteso.")

    async def test_chunk_integrity(self, db_conn, ingested_data, tenant_id: UUID):
        """Verifica l'integrità di un chunk campione utilizzando la connessione isolata."""
        result = await db_conn.fetchrow("SELECT embedding, tenant_id FROM chunks WHERE document_id = $1 AND tenant_id = $2 LIMIT 1", ingested_data['doc_id'], tenant_id)
        assert result is not None, "Nessun chunk trovato."
        assert result['embedding'] is not None, "L'embedding del chunk non deve essere nullo."
        assert result['tenant_id'] == tenant_id, "Il tenant_id del chunk non corrisponde."
        print("✅ Chunk campione verificato con successo (embedding e tenant ID presenti e corretti).")
