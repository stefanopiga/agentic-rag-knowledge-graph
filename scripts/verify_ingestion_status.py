
import asyncio
import os
import psycopg2
from dotenv import load_dotenv

# Carica le variabili d'ambiente prima di ogni altra operazione
load_dotenv()

# Aggiungi il percorso del progetto per importare i moduli dell'agent
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.graph_utils import GraphitiClient

# --- CONFIGURAZIONE ---
DOCUMENT_TITLE_TO_CHECK = "THORACIC PAIN"

# --- Funzioni di Verifica ---

async def check_neo4j_data(tenant_id: str):
    """Verifica i dati su Neo4j in due modi: query diretta e ricerca tramite l'agent."""
    print("\n--- Verificando dati su Neo4j ---")
    
    # Prepara le credenziali
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        print("🛑 ERRORE: Variabili d'ambiente NEO4J non trovate. Salto verifica Neo4j.")
        return

    # 1. Verifica diretta tramite GraphitiClient (usando il metodo search)
    graph_client = None
    try:
        print(f"1. Tentativo di ricerca tramite Agent per '{DOCUMENT_TITLE_TO_CHECK}'...")
        graph_client = GraphitiClient(neo4j_uri=uri, neo4j_user=user, neo4j_password=password)
        await graph_client.initialize()
        
        # Test di ricerca semantica
        search_results = await graph_client.search(f"fatti su {DOCUMENT_TITLE_TO_CHECK}", tenant_id=tenant_id)
        if search_results:
            print(f"✅ SUCCESSO: Trovati {len(search_results)} risultati tramite ricerca semantica.")
        else:
            print(f"⚠️ ATTENZIONE: Nessun risultato trovato tramite ricerca semantica per '{DOCUMENT_TITLE_TO_CHECK}'.")
            
        # Test di recupero timeline/episodi
        timeline_results = await graph_client.get_entity_timeline(DOCUMENT_TITLE_TO_CHECK, tenant_id=tenant_id)
        if timeline_results:
            print(f"✅ SUCCESSO: Trovati {len(timeline_results)} episodi/fatti nella timeline.")
        else:
            print(f"⚠️ ATTENZIONE: Nessun episodio trovato nella timeline per '{DOCUMENT_TITLE_TO_CHECK}'.")

    except Exception as e:
        print(f"🛑 ERRORE durante la comunicazione con Neo4j tramite GraphitiClient: {e}")
    finally:
        try:
            if graph_client and graph_client.graphiti:
                await graph_client.graphiti.close()
                print("Connessione Neo4j chiusa.")
        except Exception:
            pass


async def check_postgres_data():
    """Verifica lo stato di ingestione del documento su PostgreSQL."""
    print("\n--- Verificando stato ingestione su PostgreSQL ---")
    
    # Costruisce la connection string
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        try:
            user = os.environ['POSTGRES_USER']
            password = os.environ['POSTGRES_PASSWORD']
            host = os.environ['POSTGRES_HOST']
            port = os.environ['POSTGRES_PORT']
            dbname = os.environ['POSTGRES_DB']
            db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        except KeyError:
            print("🛑 ERRORE: Variabili d'ambiente PostgreSQL non trovate.")
            return

    conn = None
    try:
        conn = psycopg2.connect(db_url)
        print("✅ Connessione a PostgreSQL stabilita.")
        
        with conn.cursor() as cur:
            # Query per trovare lo stato di ingestione del documento
            query = """
                SELECT id, status, error_message, created_at, updated_at 
                FROM document_ingestion_status
                WHERE file_path LIKE %s;
            """
            # Usa un pattern LIKE per essere flessibile con il percorso
            file_pattern = f"%{DOCUMENT_TITLE_TO_CHECK.replace(' ', '%')}%"
            
            cur.execute(query, (file_pattern,))
            result = cur.fetchone()
            
            if result:
                doc_id, status, error, created, updated = result
                print(f"✅ Trovato record di ingestione per il documento:")
                print(f"  - ID Status: {doc_id}")
                print(f"  - Status: {status}")
                print(f"  - Messaggio di Errore: {'Nessuno' if not error else error}")
                print(f"  - Creato il: {created}")
                print(f"  - Aggiornato il: {updated}")
            else:
                print(f"⚠️ ATTENZIONE: Nessun record di ingestione trovato per un documento contenente '{DOCUMENT_TITLE_TO_CHECK}'.")

    except psycopg2.OperationalError as e:
        print(f"🛑 ERRORE di connessione a PostgreSQL: {e}")
    except Exception as e:
        print(f"🛑 ERRORE durante la verifica di PostgreSQL: {e}")
    finally:
        if conn:
            conn.close()
            print("Connessione PostgreSQL chiusa.")


async def main():
    """Esegue tutte le verifiche."""
    print("--- Avvio Script di Diagnostica Ingestione ---")
    # Recupera tenant_id per 'default'
    tenant_id = None
    try:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cur:
                cur.execute("SELECT id::text FROM accounts_tenant WHERE slug = 'default'")
                row = cur.fetchone()
                if row:
                    tenant_id = row[0]
            conn.close()
    except Exception:
        pass

    await check_postgres_data()
    if tenant_id:
        await check_neo4j_data(tenant_id)
    else:
        print("⚠️ ATTENZIONE: tenant_id non disponibile; salto la verifica semantica su Neo4j.")
    print("\n--- Diagnostica Completata ---")

if __name__ == "__main__":
    # Esegue l'applicazione asincrona
    try:
        asyncio.run(main())
    except RuntimeError as e:
        print(f"Errore nell'esecuzione del loop asyncio: {e}")

