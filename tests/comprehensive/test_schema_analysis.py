"""
Test suite for schema analysis utilities
Tests schema consolidation analysis and validation
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from scripts.schema_analysis import SQLSchemaAnalyzer

class TestSQLSchemaAnalyzer:
    """Test schema analysis functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.sql_dir = Path(self.test_dir) / "sql"
        self.sql_dir.mkdir()
        
        # Create test analyzer
        self.analyzer = SQLSchemaAnalyzer(self.test_dir)
        
    def create_test_schema(self, name: str, content: str):
        """Helper to create test schema file"""
        schema_file = self.sql_dir / f"{name}.sql"
        with open(schema_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return schema_file
    
    def test_extract_tables_basic(self):
        """Test basic table extraction"""
        schema_content = """
        CREATE TABLE users (
            id UUID PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE
        );
        
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            user_id UUID REFERENCES users(id)
        );
        """
        
        tables = self.analyzer.extract_tables(schema_content, "test")
        
        assert len(tables) == 2
        assert "users" in tables
        assert "posts" in tables
        
        # Test users table
        users_cols = tables["users"]["columns"]
        assert len(users_cols) == 3
        assert users_cols[0]["name"] == "id"
        assert users_cols[0]["type"] == "UUID"
        assert "PRIMARY KEY" in users_cols[0]["properties"]
        
    def test_extract_tables_with_tenant_id(self):
        """Test multi-tenant table extraction"""
        schema_content = """
        CREATE TABLE documents (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            content TEXT,
            metadata JSONB DEFAULT '{}'
        );
        """
        
        tables = self.analyzer.extract_tables(schema_content, "production")
        
        assert "documents" in tables
        docs_cols = tables["documents"]["columns"]
        
        # Find tenant_id column
        tenant_col = next((col for col in docs_cols if col["name"] == "tenant_id"), None)
        assert tenant_col is not None
        assert tenant_col["type"] == "UUID"
        assert "NOT NULL" in tenant_col["properties"]
        
    def test_extract_functions(self):
        """Test function extraction"""
        schema_content = """
        CREATE OR REPLACE FUNCTION match_chunks(
            query_embedding vector(1536),
            match_count INT DEFAULT 10
        )
        RETURNS TABLE (
            chunk_id UUID,
            similarity FLOAT
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY SELECT id, 1.0 FROM chunks;
        END;
        $$;
        
        CREATE FUNCTION simple_func()
        RETURNS INTEGER AS 'SELECT 42;' LANGUAGE sql;
        """
        
        functions = self.analyzer.extract_functions(schema_content, "test")
        
        assert len(functions) == 2
        assert "match_chunks" in functions
        assert "simple_func" in functions
        
        match_func = functions["match_chunks"]
        assert "query_embedding vector(1536)" in match_func["parameters"]
        assert "LANGUAGE plpgsql" in match_func["body"]
        
    def test_extract_indexes(self):
        """Test index extraction"""
        schema_content = """
        CREATE INDEX idx_documents_tenant ON documents(tenant_id);
        CREATE UNIQUE INDEX idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks 
            USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        """
        
        indexes = self.analyzer.extract_indexes(schema_content, "test")
        
        assert len(indexes) == 3
        assert "idx_documents_tenant" in indexes
        assert "idx_users_email" in indexes
        assert "idx_chunks_embedding" in indexes
        
        tenant_idx = indexes["idx_documents_tenant"]
        assert tenant_idx["table"] == "documents"
        assert tenant_idx["columns"] == "tenant_id"
        
        embedding_idx = indexes["idx_chunks_embedding"]
        assert "lists = 100" in embedding_idx["options"]
        
    def test_extract_extensions(self):
        """Test extension extraction"""
        schema_content = """
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE EXTENSION "uuid-ossp";
        CREATE EXTENSION pg_trgm;
        CREATE EXTENSION IF NOT EXISTS btree_gin;
        """
        
        extensions = self.analyzer.extract_extensions(schema_content, "test")
        
        expected = {"vector", "uuid-ossp", "pg_trgm", "btree_gin"}
        assert extensions == expected
        
    def test_compare_table_definitions(self):
        """Test table comparison logic"""
        legacy_schema = """
        CREATE TABLE documents (
            id UUID PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT
        );
        """
        
        production_schema = """
        CREATE TABLE documents (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            metadata JSONB DEFAULT '{}'
        );
        """
        
        legacy_tables = self.analyzer.extract_tables(legacy_schema, "legacy")
        production_tables = self.analyzer.extract_tables(production_schema, "production")
        
        # Simulate overlapping table comparison
        schemas = {
            "legacy": legacy_tables["documents"],
            "production": production_tables["documents"]
        }
        
        differences = self.analyzer._compare_table_definitions(schemas)
        
        # Should detect missing tenant_id and metadata in legacy
        assert any("tenant_id" in diff for diff in differences)
        assert any("metadata" in diff for diff in differences)
        
    def test_function_parameter_comparison(self):
        """Test function parameter comparison"""
        legacy_func = {
            "legacy": {
                "parameters": "query_embedding vector(1536), match_count INT",
                "schema": "legacy"
            }
        }
        
        production_func = {
            "production": {
                "parameters": "p_tenant_id UUID, query_embedding vector(1536), match_count INT",
                "schema": "production"
            }
        }
        
        schemas = {**legacy_func, **production_func}
        differences = self.analyzer._compare_function_params(schemas)
        
        # Should detect parameter differences
        assert len(differences) > 0
        assert any("p_tenant_id" in str(diff) for diff in differences)
        
    def test_full_analysis_workflow(self):
        """Test complete analysis workflow"""
        # Create test schema files
        legacy_content = """
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
        
        CREATE TABLE documents (
            id UUID PRIMARY KEY,
            title TEXT NOT NULL
        );
        
        CREATE FUNCTION match_chunks(query_embedding vector(1536))
        RETURNS TABLE (chunk_id UUID) AS $$ SELECT id FROM chunks; $$;
        """
        
        production_content = """
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
        CREATE EXTENSION IF NOT EXISTS btree_gin;
        
        CREATE TABLE documents (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            title TEXT NOT NULL
        );
        
        CREATE TABLE accounts_tenant (
            id UUID PRIMARY KEY,
            name VARCHAR(100)
        );
        
        CREATE FUNCTION match_chunks(p_tenant_id UUID, query_embedding vector(1536))
        RETURNS TABLE (chunk_id UUID) AS $$ SELECT id FROM chunks; $$;
        """
        
        # Update analyzer schema files to point to test files
        self.analyzer.schema_files = {
            'legacy': self.create_test_schema('schema', legacy_content),
            'production': self.create_test_schema('schema_with_auth', production_content),
            'extension': self.create_test_schema('section_tracking_schema', 'CREATE TABLE test_table (id INT);')
        }
        
        results = self.analyzer.analyze_schemas()
        
        # Validate results structure
        assert 'tables' in results
        assert 'functions' in results
        assert 'extensions' in results
        assert 'analysis' in results
        
        analysis = results['analysis']
        
        # Check overlapping tables detection
        assert 'documents' in analysis['table_overlaps']
        overlap_info = analysis['table_overlaps']['documents']
        assert 'legacy' in overlap_info['present_in']
        assert 'production' in overlap_info['present_in']
        
        # Check function conflicts detection
        assert 'match_chunks' in analysis['function_conflicts']
        
        # Check extension differences
        assert 'btree_gin' in analysis['extension_differences']
        
        # Check recommendations
        recommendations = analysis['consolidation_recommendations']
        assert len(recommendations) > 0
        assert any("schema_with_auth.sql as base" in rec for rec in recommendations)
        
    def test_consolidation_recommendations(self):
        """Test recommendation generation logic"""
        # Mock results for recommendation testing
        mock_results = {
            'tables': {
                'documents': {
                    'legacy': {'columns': [], 'schema': 'legacy'},
                    'production': {'columns': [], 'schema': 'production'}
                },
                'accounts_tenant': {
                    'production': {'columns': [], 'schema': 'production'}
                }
            },
            'functions': {
                'match_chunks': {
                    'legacy': {'parameters': 'old_params', 'schema': 'legacy'},
                    'production': {'parameters': 'new_params', 'schema': 'production'}
                }
            },
            'extensions': {
                'legacy': ['vector', 'pg_trgm'],
                'production': ['vector', 'pg_trgm', 'btree_gin'],
                'extension': []
            }
        }
        
        mock_analysis = {
            'table_overlaps': {'documents': {}},
            'function_conflicts': {'match_chunks': {}},
            'extension_differences': {'btree_gin': {}}
        }
        
        recommendations = self.analyzer._generate_recommendations(mock_results, mock_analysis)
        
        # Should recommend using production as base
        assert any("schema_with_auth.sql as base" in rec for rec in recommendations)
        
        # Should mention table consolidation needs
        assert any("tables need consolidation" in rec for rec in recommendations)
        
        # Should mention extension standardization
        assert any("extensions" in rec for rec in recommendations)
        
    def test_report_generation(self):
        """Test report file generation"""
        # Use a temporary output file
        output_file = os.path.join(self.test_dir, "test_report.json")
        
        # Create minimal test schemas
        self.analyzer.schema_files = {
            'legacy': self.create_test_schema('schema', 'CREATE TABLE test (id INT);'),
            'production': self.create_test_schema('schema_with_auth', 'CREATE TABLE test (id INT, tenant_id UUID);'),
            'extension': self.create_test_schema('section_tracking_schema', '')
        }
        
        results = self.analyzer.generate_report(output_file)
        
        # Verify file was created
        assert os.path.exists(output_file)
        
        # Verify file content is valid JSON
        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_results = json.load(f)
            
        assert loaded_results == results
        assert 'analysis' in loaded_results
        
    def test_error_handling_missing_files(self):
        """Test behavior with missing schema files"""
        # Use non-existent files
        self.analyzer.schema_files = {
            'legacy': Path('/nonexistent/schema.sql'),
            'production': Path('/nonexistent/schema_with_auth.sql'),
            'extension': Path('/nonexistent/section_tracking_schema.sql')
        }
        
        # Should not crash, should return empty results
        results = self.analyzer.analyze_schemas()
        
        assert 'tables' in results
        assert 'analysis' in results
        assert len(results['tables']) == 0
        
    def test_malformed_sql_handling(self):
        """Test handling of malformed SQL"""
        malformed_content = """
        CREATE TABLE incomplete_table (
            id UUID
            -- Missing closing parenthesis and semicolon
        
        INVALID SQL SYNTAX HERE;
        """
        
        # Should not crash when processing malformed SQL
        tables = self.analyzer.extract_tables(malformed_content, "test")
        functions = self.analyzer.extract_functions(malformed_content, "test")
        
        # May or may not extract partial information, but shouldn't crash
        assert isinstance(tables, dict)
        assert isinstance(functions, dict)

class TestSchemaValidation:
    """Additional validation tests for schema analysis"""
    
    def test_tenant_isolation_detection(self):
        """Test detection of tenant isolation patterns"""
        analyzer = SQLSchemaAnalyzer()
        
        # Schema with proper tenant isolation
        tenant_schema = """
        CREATE TABLE documents (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL REFERENCES accounts_tenant(id),
            title TEXT
        );
        """
        
        # Schema without tenant isolation
        legacy_schema = """
        CREATE TABLE documents (
            id UUID PRIMARY KEY,
            title TEXT
        );
        """
        
        tenant_tables = analyzer.extract_tables(tenant_schema, "production")
        legacy_tables = analyzer.extract_tables(legacy_schema, "legacy")
        
        # Check tenant_id presence
        tenant_doc = tenant_tables["documents"]
        legacy_doc = legacy_tables["documents"]
        
        tenant_cols = [col["name"] for col in tenant_doc["columns"]]
        legacy_cols = [col["name"] for col in legacy_doc["columns"]]
        
        assert "tenant_id" in tenant_cols
        assert "tenant_id" not in legacy_cols
        
    def test_foreign_key_dependency_detection(self):
        """Test foreign key dependency detection"""
        analyzer = SQLSchemaAnalyzer()
        
        schema_content = """
        CREATE TABLE document_sections (
            id SERIAL PRIMARY KEY,
            document_status_id INTEGER REFERENCES document_ingestion_status(id) ON DELETE CASCADE,
            section_position INTEGER NOT NULL
        );
        """
        
        tables = analyzer.extract_tables(schema_content, "extension")
        
        # Should extract table (foreign key info is in the definition)
        assert "document_sections" in tables
        sections_table = tables["document_sections"]
        
        # Check that foreign key information is preserved in definition
        definition = sections_table["definition"]
        assert "REFERENCES document_ingestion_status" in definition
        assert "ON DELETE CASCADE" in definition
