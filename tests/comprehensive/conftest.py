"""
Configurazione pytest per test completi, con gestione centralizzata del loop di eventi e delle connessioni al database.
"""

import pytest
import asyncio
import logging
import os
import sys
from pathlib import Path
import asyncpg
from dotenv import load_dotenv

# Carica le variabili d'ambiente prima di ogni altra cosa (forza override da .env)
load_dotenv(override=True)
# Allinea credenziali Neo4j per i test (priorità a .env)
if os.getenv("NEO4J_PASSWORD"):
    os.environ["NEO4J_PASSWORD"] = os.getenv("NEO4J_PASSWORD")
# Modalità offline per embeddings durante i test
os.environ.setdefault("EMBEDDINGS_OFFLINE", "1")

# Setup environment
os.environ.setdefault("APP_ENV", "test")

# Aggiungi la root del progetto al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent.db_utils import db_pool, initialize_database, close_database
from agent.graph_utils import graph_client, initialize_graph, close_graph

# Setup logging
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Compatibilità asincrona per Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="function")
def event_loop():
    """Crea un loop di eventi per ogni test (evita ScopeMismatch con pytest-asyncio)."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()

@pytest.fixture(scope="function", autouse=True)
async def manage_database_connections(event_loop):
    """
    Gestisce l'inizializzazione e la chiusura delle connessioni al database
    una sola volta per l'intera sessione di test.
    """
    # Inizializza le connessioni
    await initialize_database()
    # Forza re-instanziazione del client Neo4j con le credenziali correnti da .env
    try:
        import agent.graph_utils as gg
        gg.graph_client = gg.GraphitiClient(
            neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
            neo4j_password=os.getenv("NEO4J_PASSWORD")
        )
        # Aggiorna anche il riferimento importato nei test già caricati
        try:
            import tests.comprehensive.test_database_connections as tdc
            tdc.graph_client = gg.graph_client
        except Exception:
            pass
    except Exception:
        pass
    await initialize_graph()
    
    # Esegui lo schema SQL per assicurarti che il database sia pulito e pronto
    # Applica schema solo se necessario in questo test function-scope
    try:
        async with db_pool.acquire() as conn:
            schema_path = project_root / "sql" / "schema_with_auth.sql"
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            await conn.execute(schema_sql)
    except Exception as e:
        pytest.fail(f"Failed to apply database schema: {e}")

    yield

    # Chiudi le connessioni alla fine del test
    await close_graph()
    await close_database()



@pytest.fixture
def test_db_session():
    """
    Questo è un marcatore per i test che richiedono una sessione di database.
    La gestione effettiva è ora in `manage_database_connections`.
    """
    pass
