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

# Carica le variabili d'ambiente prima di ogni altra cosa
load_dotenv()

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

@pytest.fixture(scope="session")
def event_loop():
    """Crea un loop di eventi per l'intera sessione di test."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def manage_database_connections(event_loop):
    """
    Gestisce l'inizializzazione e la chiusura delle connessioni al database
    una sola volta per l'intera sessione di test.
    """
    # Inizializza le connessioni
    await initialize_database()
    await initialize_graph()
    
    # Esegui lo schema SQL per assicurarti che il database sia pulito e pronto
    try:
        async with db_pool.acquire() as conn:
            schema_path = project_root / "sql" / "schema_with_auth.sql"
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            await conn.execute(schema_sql)
    except Exception as e:
        pytest.fail(f"Failed to apply database schema: {e}")

    yield

    # Chiudi le connessioni alla fine di tutti i test
    await close_graph()
    await close_database()

@pytest.fixture
def test_db_session():
    """
    Questo è un marcatore per i test che richiedono una sessione di database.
    La gestione effettiva è ora in `manage_database_connections`.
    """
    pass
