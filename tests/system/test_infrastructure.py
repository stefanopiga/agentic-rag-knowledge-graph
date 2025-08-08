"""
Test Infrastructure - Database e Connessioni.

Fase 1 del testing di sistema: verifica che tutti i componenti base funzionino.
"""

import os
import sys
import asyncio
import traceback
from pathlib import Path

# Aggiungi project root al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.system.test_logger import create_logger


class InfrastructureTests:
    """Test per verifica infrastruttura di base."""
    
    def __init__(self):
        self.logger = create_logger("infrastructure")
        self.test_results = {
            "python_imports": False,
            "postgresql_connection": False,
            "neo4j_connection": False,
            "agent_configuration": False,
            "provider_validation": False
        }
    
    async def run_all_tests(self) -> dict:
        """Esegue tutti i test dell'infrastruttura."""
        self.logger.log_info("🏗️ INIZIANDO TEST INFRASTRUTTURA...")
        
        try:
            # Test 1: Importazioni Python
            await self.test_python_imports()
            
            # Test 2: Connessione PostgreSQL
            await self.test_postgresql_connection()
            
            # Test 3: Connessione Neo4j
            await self.test_neo4j_connection()
            
            # Test 4: Configurazione Agent
            await self.test_agent_configuration()
            
            # Test 5: Validazione Provider
            await self.test_provider_validation()
            
        except Exception as e:
            self.logger.log_error(f"Errore critico durante test infrastruttura: {e}")
            self.logger.log_error(traceback.format_exc())
        
        finally:
            return self.logger.finalize()
    
    async def test_python_imports(self):
        """Test importazioni Python critiche."""
        self.logger.log_test_start("Verifica importazioni Python critiche")
        
        try:
            # Test importazioni core
            import psycopg2
            self.logger.log_info("✅ psycopg2 importato correttamente")
            
            from neo4j import GraphDatabase
            self.logger.log_info("✅ neo4j driver importato correttamente")
            
            import openai
            self.logger.log_info("✅ openai importato correttamente")
            
            # Test importazioni project
            try:
                from agent import db_utils
                self.logger.log_info("✅ agent.db_utils importato correttamente")
            except ImportError as e:
                self.logger.log_warning(f"⚠️ agent.db_utils non disponibile: {e}")
            
            try:
                from agent import providers
                self.logger.log_info("✅ agent.providers importato correttamente")
            except ImportError as e:
                self.logger.log_warning(f"⚠️ agent.providers non disponibile: {e}")
            
            try:
                from ingestion import ingest
                self.logger.log_info("✅ ingestion.ingest importato correttamente")
            except ImportError as e:
                self.logger.log_warning(f"⚠️ ingestion.ingest non disponibile: {e}")
            
            self.test_results["python_imports"] = True
            self.logger.log_test_success("Verifica importazioni Python critiche", "Tutte le importazioni core riuscite")
            
        except ImportError as e:
            self.test_results["python_imports"] = False
            self.logger.log_test_failure("Verifica importazioni Python critiche", str(e))
    
    async def test_postgresql_connection(self):
        """Test connessione PostgreSQL."""
        self.logger.log_test_start("Verifica connessione PostgreSQL")
        
        try:
            import psycopg2
            from dotenv import load_dotenv
            
            # Carica environment variables
            load_dotenv()
            
            # Usa DATABASE_URL se disponibile, altrimenti fallback a parametri separati
            database_url = os.environ.get('DATABASE_URL')
            
            if database_url:
                self.logger.log_info(f"Tentativo connessione a PostgreSQL via DATABASE_URL")
                # Test connessione con DATABASE_URL
                conn = psycopg2.connect(database_url)
            else:
                # Fallback a parametri separati per compatibilità
                db_params = {
                    'host': os.environ.get('POSTGRES_HOST', 'localhost'),
                    'port': os.environ.get('POSTGRES_PORT', 5432),
                    'database': os.environ.get('POSTGRES_DB', 'rag_knowledge_graph'),
                    'user': os.environ.get('POSTGRES_USER', 'postgres'),
                    'password': os.environ.get('POSTGRES_PASSWORD', 'postgres')
                }
                
                self.logger.log_info(f"Tentativo connessione a PostgreSQL: {db_params['host']}:{db_params['port']}/{db_params['database']}")
                conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()
            
            # Test query base
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            self.logger.log_info(f"✅ PostgreSQL version: {version}")
            
            # Test esistenza tabelle principali
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('documents', 'chunks', 'document_ingestion_status');
            """)
            tables = cursor.fetchall()
            
            if tables:
                table_names = [t[0] for t in tables]
                self.logger.log_info(f"✅ Tabelle trovate: {table_names}")
            else:
                self.logger.log_warning("⚠️ Nessuna tabella principal trovata - potrebbe servire migration")
            
            # Test extension pgvector
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            vector_ext = cursor.fetchone()
            
            if vector_ext:
                self.logger.log_info("✅ Estensione pgvector installata")
            else:
                self.logger.log_warning("⚠️ Estensione pgvector non trovata")
            
            cursor.close()
            conn.close()
            
            self.test_results["postgresql_connection"] = True
            self.logger.log_test_success("Verifica connessione PostgreSQL", f"Connessione riuscita - {len(tables) if tables else 0} tabelle trovate")
            
        except Exception as e:
            self.test_results["postgresql_connection"] = False
            self.logger.log_test_failure("Verifica connessione PostgreSQL", str(e))
    
    async def test_neo4j_connection(self):
        """Test connessione Neo4j."""
        self.logger.log_test_start("Verifica connessione Neo4j")
        
        try:
            from neo4j import GraphDatabase
            
            # Parametri connessione
            uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
            user = os.environ.get('NEO4J_USER', 'neo4j')
            password = os.environ.get('NEO4J_PASSWORD', 'password')
            
            self.logger.log_info(f"Tentativo connessione a Neo4j: {uri}")
            
            # Test connessione
            driver = GraphDatabase.driver(uri, auth=(user, password))
            
            with driver.session() as session:
                # Test query base
                result = session.run("CALL db.info()")
                info = result.single()
                
                if info:
                    self.logger.log_info(f"✅ Neo4j connesso - DB: {info.get('name', 'unknown')}")
                
                # Test conteggio nodi
                result = session.run("MATCH (n) RETURN count(n) as node_count")
                count = result.single()["node_count"]
                self.logger.log_info(f"✅ Nodi presenti nel grafo: {count}")
                
                # Test APOC plugin
                try:
                    result = session.run("CALL apoc.help('apoc')")
                    apoc_funcs = list(result)
                    if apoc_funcs:
                        self.logger.log_info(f"✅ APOC plugin disponibile - {len(apoc_funcs)} funzioni")
                    else:
                        self.logger.log_warning("⚠️ APOC plugin non trovato")
                except:
                    self.logger.log_warning("⚠️ APOC plugin non disponibile")
            
            driver.close()
            
            self.test_results["neo4j_connection"] = True
            self.logger.log_test_success("Verifica connessione Neo4j", f"Connessione riuscita - {count} nodi nel grafo")
            
        except Exception as e:
            self.test_results["neo4j_connection"] = False
            self.logger.log_test_failure("Verifica connessione Neo4j", str(e))
    
    async def test_agent_configuration(self):
        """Test configurazione agent."""
        self.logger.log_test_start("Verifica configurazione Agent")
        
        try:
            # Test importazione agent
            try:
                from agent.agent import get_agent
                agent = get_agent()
                self.logger.log_info("✅ Agent inizializzato correttamente")
                
                # Test tools disponibili
                if hasattr(agent, 'tools') or hasattr(agent, '_tools'):
                    tools = getattr(agent, 'tools', getattr(agent, '_tools', []))
                    self.logger.log_info(f"✅ Tools agent disponibili: {len(tools)}")
                    
                    # Lista tool names se disponibili
                    try:
                        tool_names = [getattr(t, 'name', str(t)) for t in tools]
                        self.logger.log_info(f"   Tool names: {tool_names}")
                    except:
                        pass
                
            except Exception as e:
                self.logger.log_warning(f"⚠️ Agent non disponibile: {e}")
            
            # Test database utils
            try:
                from agent.db_utils import test_connection
                # Nota: non eseguiamo test_connection qui per evitare duplicati
                self.logger.log_info("✅ db_utils.test_connection disponibile")
            except Exception as e:
                self.logger.log_warning(f"⚠️ db_utils non disponibile: {e}")
            
            self.test_results["agent_configuration"] = True
            self.logger.log_test_success("Verifica configurazione Agent", "Configurazione base disponibile")
            
        except Exception as e:
            self.test_results["agent_configuration"] = False
            self.logger.log_test_failure("Verifica configurazione Agent", str(e))
    
    async def test_provider_validation(self):
        """Test validazione provider configuration."""
        self.logger.log_test_start("Verifica validazione Provider")
        
        try:
            # Test variabili environment
            required_vars = [
                'LLM_PROVIDER', 'LLM_API_KEY', 'LLM_CHOICE',
                'EMBEDDING_PROVIDER', 'EMBEDDING_API_KEY', 'EMBEDDING_MODEL'
            ]
            
            missing_vars = []
            for var in required_vars:
                value = os.environ.get(var)
                if not value:
                    missing_vars.append(var)
                else:
                    # Mask API keys per security
                    if 'API_KEY' in var:
                        masked_value = value[:8] + "..." if len(value) > 8 else "***"
                        self.logger.log_info(f"✅ {var}: {masked_value}")
                    else:
                        self.logger.log_info(f"✅ {var}: {value}")
            
            if missing_vars:
                self.logger.log_warning(f"⚠️ Variabili environment mancanti: {missing_vars}")
            
            # Test provider validation se disponibile
            try:
                from agent.providers import validate_configuration
                validation_result = validate_configuration()
                
                if validation_result:
                    self.logger.log_info("✅ Validazione provider riuscita")
                else:
                    self.logger.log_warning("⚠️ Validazione provider fallita - variabili mancanti")
                    
            except Exception as e:
                self.logger.log_warning(f"⚠️ Validazione provider non disponibile: {e}")
            
            # Test OpenAI connection se API key disponibile
            api_key = os.environ.get('LLM_API_KEY') or os.environ.get('OPENAI_API_KEY')
            if api_key and not api_key.startswith('sk-test'):
                try:
                    import openai
                    client = openai.OpenAI(api_key=api_key)
                    
                    # Test minimal API call
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=5
                    )
                    
                    if response.choices:
                        self.logger.log_info("✅ OpenAI API connessione riuscita")
                    
                except Exception as e:
                    self.logger.log_warning(f"⚠️ Test OpenAI API fallito: {e}")
            else:
                self.logger.log_info("ℹ️ OpenAI API test saltato (test key o key mancante)")
            
            self.test_results["provider_validation"] = True
            self.logger.log_test_success("Verifica validazione Provider", "Configurazione provider verificata")
            
        except Exception as e:
            self.test_results["provider_validation"] = False
            self.logger.log_test_failure("Verifica validazione Provider", str(e))


async def main():
    """Esegue tutti i test dell'infrastruttura."""
    tester = InfrastructureTests()
    results = await tester.run_all_tests()
    
    # Return code based on results
    if results["summary"]["failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)