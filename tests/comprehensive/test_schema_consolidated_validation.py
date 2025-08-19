"""
Test suite per validazione schema consolidato.
Verifica che il nuovo schema_consolidated.sql contenga tutte le feature necessarie
da schema_with_auth.sql (production) + section_tracking_schema.sql (extension).
"""

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import subprocess
import tempfile
from pathlib import Path


class TestSchemaConsolidatedValidation:
    """Test suite per validazione schema consolidato completo."""

    @pytest.fixture(scope="class")
    def db_connection(self):
        """Connessione database temporaneo per testing schema consolidated."""
        # Test database connection string
        test_db_url = os.getenv(
            'TEST_DATABASE_URL',
            'postgresql://postgres:password@localhost:5432/test_schema_consolidated'
        )
        
        try:
            conn = psycopg2.connect(test_db_url)
            conn.autocommit = True
            yield conn
        finally:
            if 'conn' in locals():
                conn.close()

    @pytest.fixture(scope="class") 
    def schema_consolidated_applied(self, db_connection):
        """Applica schema_consolidated.sql al database di test."""
        schema_path = Path(__file__).parent.parent.parent / "sql" / "schema_consolidated.sql"
        
        if not schema_path.exists():
            pytest.skip("schema_consolidated.sql non ancora creato")
            
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
            
        with db_connection.cursor() as cursor:
            cursor.execute(schema_sql)
            
        return True

    def test_extensions_installed(self, db_connection, schema_consolidated_applied):
        """Verifica che tutte le extension necessarie siano installate."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT extname FROM pg_extension 
                WHERE extname IN ('vector', 'uuid-ossp', 'pg_trgm', 'btree_gin')
                ORDER BY extname
            """)
            extensions = [row['extname'] for row in cursor.fetchall()]
            
        expected_extensions = ['btree_gin', 'pg_trgm', 'uuid-ossp', 'vector']
        assert extensions == expected_extensions, f"Extension mancanti: {set(expected_extensions) - set(extensions)}"

    def test_core_multi_tenancy_tables(self, db_connection, schema_consolidated_applied):
        """Verifica esistenza tabelle core multi-tenancy."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('accounts_tenant', 'accounts_user', 'auth_user')
                ORDER BY table_name
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
            
        expected_tables = ['accounts_tenant', 'accounts_user', 'auth_user']
        assert tables == expected_tables, f"Tabelle multi-tenancy mancanti: {set(expected_tables) - set(tables)}"

    def test_rag_system_tables(self, db_connection, schema_consolidated_applied):
        """Verifica esistenza tabelle RAG system complete."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN (
                    'documents', 'chunks', 'document_ingestion_status',
                    'rag_engine_chatsession', 'rag_engine_chatmessage', 'rag_engine_queryanalytics'
                )
                ORDER BY table_name
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
            
        expected_tables = [
            'chunks', 'document_ingestion_status', 'documents',
            'rag_engine_chatmessage', 'rag_engine_chatsession', 'rag_engine_queryanalytics'
        ]
        assert tables == expected_tables, f"Tabelle RAG mancanti: {set(expected_tables) - set(tables)}"

    def test_section_tracking_tables(self, db_connection, schema_consolidated_applied):
        """Verifica esistenza tabelle section tracking da extension."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'document_sections'
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
            
        assert 'document_sections' in tables, "Tabella document_sections da extension mancante"

    def test_medical_content_system_tables(self, db_connection, schema_consolidated_applied):
        """Verifica esistenza tabelle sistema medico completo.""" 
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'medical_content_%'
                ORDER BY table_name
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
            
        expected_tables = [
            'medical_content_medicalcategory', 'medical_content_quiz',
            'medical_content_quizanalytics', 'medical_content_quizanswer',
            'medical_content_quizattempt', 'medical_content_quizcategory',
            'medical_content_quizquestion', 'medical_content_quizresponse'
        ]
        
        for table in expected_tables:
            assert table in tables, f"Tabella medical system mancante: {table}"

    def test_tenant_id_isolation_all_tables(self, db_connection, schema_consolidated_applied):
        """Verifica che tutte le tabelle principali abbiano tenant_id per isolation."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT DISTINCT t.table_name 
                FROM information_schema.tables t
                JOIN information_schema.columns c ON t.table_name = c.table_name
                WHERE t.table_schema = 'public' 
                AND t.table_type = 'BASE TABLE'
                AND c.column_name = 'tenant_id'
                AND t.table_name NOT IN ('auth_user', 'accounts_tenant') -- Queste non hanno tenant_id
                ORDER BY t.table_name
            """)
            tenant_tables = [row['table_name'] for row in cursor.fetchall()]
            
        # Tabelle che DEVONO avere tenant_id
        required_tenant_tables = [
            'accounts_user', 'chunks', 'document_ingestion_status', 'documents',
            'medical_content_medicalcategory', 'medical_content_quiz',
            'medical_content_quizanalytics', 'medical_content_quizanswer',
            'medical_content_quizattempt', 'medical_content_quizcategory',
            'medical_content_quizquestion', 'medical_content_quizresponse',
            'rag_engine_chatmessage', 'rag_engine_chatsession', 'rag_engine_queryanalytics'
        ]
        
        for table in required_tenant_tables:
            assert table in tenant_tables, f"Tabella {table} manca tenant_id per isolation"

    def test_rag_functions_multi_tenant(self, db_connection, schema_consolidated_applied):
        """Verifica che le funzioni RAG supportino multi-tenancy."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT routine_name, routine_definition 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name IN ('match_chunks', 'hybrid_search', 'get_document_chunks')
                ORDER BY routine_name
            """)
            functions = cursor.fetchall()
            
        function_names = [f['routine_name'] for f in functions]
        expected_functions = ['get_document_chunks', 'hybrid_search', 'match_chunks']
        assert function_names == expected_functions, f"Funzioni RAG mancanti: {set(expected_functions) - set(function_names)}"
        
        # Verifica che le funzioni abbiano parametro tenant_id
        for func in functions:
            definition = func['routine_definition']
            assert 'p_tenant_id' in definition, f"Funzione {func['routine_name']} manca parametro p_tenant_id"

    def test_section_tracking_functions(self, db_connection, schema_consolidated_applied):
        """Verifica esistenza funzioni section tracking da extension."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT routine_name FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name IN ('cleanup_failed_sections', 'update_document_sections_timestamp')
                ORDER BY routine_name
            """)
            functions = [row['routine_name'] for row in cursor.fetchall()]
            
        expected_functions = ['cleanup_failed_sections', 'update_document_sections_timestamp']
        assert functions == expected_functions, f"Funzioni section tracking mancanti: {set(expected_functions) - set(functions)}"

    def test_rls_enabled_tenant_tables(self, db_connection, schema_consolidated_applied):
        """Verifica che Row Level Security sia abilitato su tabelle tenant."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT schemaname, tablename, rowsecurity 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename IN (
                    'accounts_tenant', 'accounts_user', 'documents', 'chunks',
                    'rag_engine_chatsession', 'rag_engine_chatmessage'
                )
                ORDER BY tablename
            """)
            rls_tables = cursor.fetchall()
            
        for table in rls_tables:
            assert table['rowsecurity'], f"RLS non abilitato su tabella {table['tablename']}"

    def test_legacy_compatibility_tables(self, db_connection, schema_consolidated_applied):
        """Verifica esistenza tabelle legacy per backward compatibility."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('sessions', 'messages')
                ORDER BY table_name
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
            
        expected_tables = ['messages', 'sessions']
        assert tables == expected_tables, f"Tabelle legacy compatibility mancanti: {set(expected_tables) - set(tables)}"

    def test_document_summaries_view(self, db_connection, schema_consolidated_applied):
        """Verifica esistenza view document_summaries aggiornata."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name = 'document_summaries'
            """)
            views = cursor.fetchall()
            
        assert len(views) == 1, "View document_summaries mancante"
        
        # Verifica che la view includa tenant_id
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT column_name FROM information_schema.view_column_usage 
                WHERE view_name = 'document_summaries' 
                AND column_name = 'tenant_id'
            """)
            tenant_column = cursor.fetchall()
            
        assert len(tenant_column) > 0, "View document_summaries manca tenant_id"

    def test_failed_sections_view(self, db_connection, schema_consolidated_applied):
        """Verifica esistenza view failed_sections da extension."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT table_name FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name = 'failed_sections'
            """)
            views = cursor.fetchall()
            
        assert len(views) == 1, "View failed_sections da extension mancante"

    def test_indexes_comprehensive(self, db_connection, schema_consolidated_applied):
        """Verifica esistenza indici critici per performance."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname LIKE 'idx_%'
                ORDER BY indexname
            """)
            indexes = [row['indexname'] for row in cursor.fetchall()]
            
        # Indici critici che devono esistere
        critical_indexes = [
            'idx_chunks_tenant', 'idx_chunks_embedding', 'idx_documents_tenant',
            'idx_tenant_slug', 'idx_user_tenant', 'idx_document_sections_status'
        ]
        
        for index in critical_indexes:
            assert index in indexes, f"Indice critico mancante: {index}"

    def test_triggers_consolidated(self, db_connection, schema_consolidated_applied):
        """Verifica esistenza trigger consolidati."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT trigger_name, event_object_table 
                FROM information_schema.triggers 
                WHERE trigger_schema = 'public'
                ORDER BY trigger_name
            """)
            triggers = cursor.fetchall()
            
        trigger_names = [t['trigger_name'] for t in triggers]
        
        # Trigger che devono esistere
        expected_triggers = [
            'trigger_update_document_sections_timestamp',
            'update_documents_updated_at',
            'update_ingestion_status_updated_at',
            'update_sessions_updated_at',
            'update_tenant_updated_at',
            'update_user_updated_at'
        ]
        
        for trigger in expected_triggers:
            assert trigger in trigger_names, f"Trigger mancante: {trigger}"

    def test_initial_data_present(self, db_connection, schema_consolidated_applied):
        """Verifica presenza dati iniziali per default tenant."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            # Verifica default tenant
            cursor.execute("SELECT COUNT(*) as count FROM accounts_tenant WHERE slug = 'default'")
            tenant_count = cursor.fetchone()['count']
            assert tenant_count == 1, "Default tenant non presente"
            
            # Verifica categorie mediche default
            cursor.execute("""
                SELECT COUNT(*) as count FROM medical_content_medicalcategory 
                WHERE tenant_id = (SELECT id FROM accounts_tenant WHERE slug = 'default')
            """)
            category_count = cursor.fetchone()['count']
            assert category_count >= 8, f"Categorie mediche default insufficienti: {category_count}"

    def test_no_legacy_schema_conflicts(self, db_connection, schema_consolidated_applied):
        """Verifica che non ci siano conflitti con schema legacy."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            # Verifica che le funzioni legacy siano sovrascritte con versioni multi-tenant
            cursor.execute("""
                SELECT routine_name, specific_name 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name = 'match_chunks'
            """)
            functions = cursor.fetchall()
            
        # Deve esistere solo una versione (quella multi-tenant)
        assert len(functions) == 1, f"Conflitto funzioni legacy: {len(functions)} versioni di match_chunks"

    def test_schema_constraints_integrity(self, db_connection, schema_consolidated_applied):
        """Verifica integrità constraint e foreign key."""
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY' 
                AND table_schema = 'public'
            """)
            fk_count = cursor.fetchone()['count']
            
        # Deve esistere un numero ragionevole di foreign key
        assert fk_count >= 20, f"Foreign key insufficienti: {fk_count}"
        
        # Verifica constraint check specifici
        with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT constraint_name FROM information_schema.check_constraints 
                WHERE constraint_schema = 'public' 
                AND constraint_name LIKE '%_check%'
            """)
            checks = cursor.fetchall()
            
        # Dovrebbero esistere check constraint per enum values
        assert len(checks) >= 5, f"Check constraint insufficienti: {len(checks)}"
