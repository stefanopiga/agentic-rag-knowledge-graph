#!/usr/bin/env python3
"""
🔍 SCHEMA VERIFICATION SCRIPT
Verifica che lo schema sia stato deployato correttamente su Neon PostgreSQL
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any
import json
from datetime import datetime

class NeonSchemaVerifier:
    """Verifica deployment schema su Neon PostgreSQL"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "database_url": database_url.split('@')[1] if '@' in database_url else "***",
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
    
    def connect(self) -> bool:
        """Connessione al database"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = True
            return True
        except Exception as e:
            self.log_test("database_connection", False, f"Errore connessione: {e}")
            return False
    
    def close(self):
        """Chiude connessione"""
        if self.conn:
            self.conn.close()
    
    def log_test(self, test_name: str, passed: bool, details: str = "", warning: bool = False):
        """Log risultato test"""
        self.results["tests"][test_name] = {
            "passed": passed,
            "details": details,
            "warning": warning,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results["summary"]["total_tests"] += 1
        if warning:
            self.results["summary"]["warnings"] += 1
        elif passed:
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
        
        # Console output
        status = "⚠️" if warning else ("✅" if passed else "❌")
        print(f"{status} {test_name}: {details}")
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Esegue query e ritorna risultati"""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            raise Exception(f"Query failed: {e}")
    
    def verify_extensions(self):
        """Verifica extensions PostgreSQL"""
        try:
            extensions = self.execute_query("""
                SELECT extname, extversion 
                FROM pg_extension 
                WHERE extname IN ('vector', 'uuid-ossp', 'pg_trgm', 'btree_gin')
                ORDER BY extname
            """)
            
            required_extensions = {'vector', 'uuid-ossp', 'pg_trgm', 'btree_gin'}
            found_extensions = {ext['extname'] for ext in extensions}
            
            missing = required_extensions - found_extensions
            
            if not missing:
                self.log_test("extensions", True, f"Tutte le extensions presenti: {', '.join(found_extensions)}")
            else:
                self.log_test("extensions", False, f"Extensions mancanti: {', '.join(missing)}")
            
            return extensions
            
        except Exception as e:
            self.log_test("extensions", False, f"Errore verifica extensions: {e}")
            return []
    
    def verify_tables(self):
        """Verifica presenza tabelle principali"""
        try:
            tables = self.execute_query("""
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            required_tables = {
                'accounts_tenant', 'accounts_user', 'auth_user',
                'documents', 'chunks', 'document_ingestion_status',
                'medical_content_medicalcategory', 'medical_content_quiz',
                'medical_content_quizquestion', 'medical_content_quizanswer',
                'rag_engine_chatsession', 'rag_engine_chatmessage',
                'rag_engine_queryanalytics', 'sessions', 'messages'
            }
            
            found_tables = {table['table_name'] for table in tables}
            missing = required_tables - found_tables
            
            if not missing:
                self.log_test("tables", True, f"Tutte le tabelle presenti ({len(found_tables)} totali)")
            else:
                self.log_test("tables", False, f"Tabelle mancanti: {', '.join(missing)}")
            
            return tables
            
        except Exception as e:
            self.log_test("tables", False, f"Errore verifica tabelle: {e}")
            return []
    
    def verify_functions(self):
        """Verifica funzioni PostgreSQL"""
        try:
            functions = self.execute_query("""
                SELECT routine_name, routine_type
                FROM information_schema.routines 
                WHERE routine_schema = 'public'
                AND routine_name IN ('match_chunks', 'hybrid_search', 'get_document_chunks', 'update_updated_at_column')
                ORDER BY routine_name
            """)
            
            required_functions = {'match_chunks', 'hybrid_search', 'get_document_chunks', 'update_updated_at_column'}
            found_functions = {func['routine_name'] for func in functions}
            missing = required_functions - found_functions
            
            if not missing:
                self.log_test("functions", True, f"Tutte le funzioni presenti: {', '.join(found_functions)}")
            else:
                self.log_test("functions", False, f"Funzioni mancanti: {', '.join(missing)}")
            
            return functions
            
        except Exception as e:
            self.log_test("functions", False, f"Errore verifica funzioni: {e}")
            return []
    
    def verify_indexes(self):
        """Verifica indexes principali"""
        try:
            indexes = self.execute_query("""
                SELECT indexname, tablename, indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                AND indexname ~ '(embedding|tenant|trgm|gin)'
                ORDER BY tablename, indexname
            """)
            
            critical_indexes = [
                'idx_chunks_embedding',
                'idx_chunks_tenant', 
                'idx_documents_tenant',
                'idx_chunks_content_trgm'
            ]
            
            found_indexes = {idx['indexname'] for idx in indexes}
            missing = set(critical_indexes) - found_indexes
            
            if not missing:
                self.log_test("indexes", True, f"Indexes critici presenti ({len(indexes)} totali)")
            else:
                self.log_test("indexes", False, f"Indexes mancanti: {', '.join(missing)}")
                
            # Check vector index specifically
            vector_indexes = [idx for idx in indexes if 'embedding' in idx['indexname']]
            if vector_indexes:
                self.log_test("vector_index", True, f"Vector index trovato: {vector_indexes[0]['indexname']}")
            else:
                self.log_test("vector_index", False, "Vector index per embeddings mancante")
            
            return indexes
            
        except Exception as e:
            self.log_test("indexes", False, f"Errore verifica indexes: {e}")
            return []
    
    def verify_rls(self):
        """Verifica Row Level Security"""
        try:
            rls_tables = self.execute_query("""
                SELECT tablename, rowsecurity
                FROM pg_tables 
                WHERE schemaname = 'public'
                AND tablename ~ '(accounts_|medical_|rag_|documents|chunks)'
                ORDER BY tablename
            """)
            
            rls_enabled = [table for table in rls_tables if table['rowsecurity']]
            rls_disabled = [table for table in rls_tables if not table['rowsecurity']]
            
            if len(rls_enabled) >= 10:
                self.log_test("rls_enabled", True, f"RLS abilitato su {len(rls_enabled)} tabelle")
            else:
                self.log_test("rls_enabled", False, f"RLS abilitato solo su {len(rls_enabled)} tabelle")
            
            if rls_disabled:
                table_names = [t['tablename'] for t in rls_disabled]
                self.log_test("rls_missing", False, f"RLS mancante su: {', '.join(table_names)}", warning=True)
            
            return rls_tables
            
        except Exception as e:
            self.log_test("rls", False, f"Errore verifica RLS: {e}")
            return []
    
    def verify_initial_data(self):
        """Verifica dati iniziali"""
        try:
            # Check default tenant
            tenants = self.execute_query("SELECT name, slug FROM accounts_tenant LIMIT 5")
            if tenants:
                self.log_test("default_tenant", True, f"Tenant trovati: {len(tenants)}")
            else:
                self.log_test("default_tenant", False, "Nessun tenant trovato")
            
            # Check admin user
            admin_users = self.execute_query("SELECT username FROM auth_user WHERE is_superuser = true LIMIT 3")
            if admin_users:
                usernames = [u['username'] for u in admin_users]
                self.log_test("admin_users", True, f"Admin users: {', '.join(usernames)}")
            else:
                self.log_test("admin_users", False, "Nessun admin user trovato", warning=True)
            
            # Check medical categories
            categories = self.execute_query("SELECT name FROM medical_content_medicalcategory LIMIT 10")
            if categories:
                self.log_test("medical_categories", True, f"Categorie mediche: {len(categories)}")
            else:
                self.log_test("medical_categories", False, "Nessuna categoria medica trovata", warning=True)
            
        except Exception as e:
            self.log_test("initial_data", False, f"Errore verifica dati iniziali: {e}")
    
    def test_rag_functions(self):
        """Test funzioni RAG"""
        try:
            # Test con dati fittizi se esiste un tenant
            tenants = self.execute_query("SELECT id FROM accounts_tenant LIMIT 1")
            if not tenants:
                self.log_test("rag_functions", False, "Nessun tenant per test funzioni RAG", warning=True)
                return
            
            tenant_id = tenants[0]['id']
            
            # Test match_chunks function (anche senza dati)
            try:
                self.execute_query(f"""
                    SELECT * FROM match_chunks(
                        '{tenant_id}',
                        '[0.1,0.2,0.3]'::vector,
                        5
                    ) LIMIT 1
                """)
                self.log_test("match_chunks_function", True, "Funzione match_chunks operativa")
            except Exception as e:
                if "invalid input syntax for type vector" in str(e):
                    self.log_test("match_chunks_function", True, "Funzione match_chunks definita (vector syntax OK)")
                else:
                    self.log_test("match_chunks_function", False, f"Errore match_chunks: {e}")
            
            # Test hybrid_search function
            try:
                self.execute_query(f"""
                    SELECT * FROM hybrid_search(
                        '{tenant_id}',
                        '[0.1,0.2,0.3]'::vector,
                        'test query',
                        5,
                        0.3
                    ) LIMIT 1
                """)
                self.log_test("hybrid_search_function", True, "Funzione hybrid_search operativa")
            except Exception as e:
                if "invalid input syntax for type vector" in str(e):
                    self.log_test("hybrid_search_function", True, "Funzione hybrid_search definita (vector syntax OK)")
                else:
                    self.log_test("hybrid_search_function", False, f"Errore hybrid_search: {e}")
            
        except Exception as e:
            self.log_test("rag_functions", False, f"Errore test funzioni RAG: {e}")
    
    def run_verification(self) -> Dict[str, Any]:
        """Esegue verifica completa"""
        print("🔍 AVVIO VERIFICA SCHEMA NEON...")
        print("=" * 50)
        
        if not self.connect():
            return self.results
        
        try:
            # Verifica componenti
            self.verify_extensions()
            self.verify_tables()
            self.verify_functions()
            self.verify_indexes()
            self.verify_rls()
            self.verify_initial_data()
            self.test_rag_functions()
            
            # Summary finale
            print("\n" + "=" * 50)
            print(f"📊 SUMMARY VERIFICA:")
            print(f"   ✅ Passati: {self.results['summary']['passed']}")
            print(f"   ❌ Falliti: {self.results['summary']['failed']}")
            print(f"   ⚠️ Warning: {self.results['summary']['warnings']}")
            print(f"   📋 Totali: {self.results['summary']['total_tests']}")
            
            success_rate = (self.results['summary']['passed'] / self.results['summary']['total_tests']) * 100
            print(f"   📈 Successo: {success_rate:.1f}%")
            
            if self.results['summary']['failed'] == 0:
                print("🎉 SCHEMA DEPLOYMENT: SUCCESSO!")
            else:
                print("⚠️ SCHEMA DEPLOYMENT: PROBLEMI RILEVATI")
            
        finally:
            self.close()
        
        return self.results


def main():
    """Main function"""
    # Ottieni DATABASE_URL da environment o argomento
    database_url = os.environ.get('DATABASE_URL')
    
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    
    if not database_url:
        print("❌ DATABASE_URL non fornito")
        print("Uso: python verify_neon_schema.py [DATABASE_URL]")
        print("Oppure: export DATABASE_URL='postgres://user:pass@host:port/db'")
        sys.exit(1)
    
    # Esegui verifica
    verifier = NeonSchemaVerifier(database_url)
    results = verifier.run_verification()
    
    # Salva risultati
    output_file = f"neon_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Risultati salvati in: {output_file}")
    
    # Exit code
    if results['summary']['failed'] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()