# Database Schema

This is the database schema implementation for the spec detailed in @.agent-os/specs/2025-08-18-schema-sql-consolidation/spec.md

## Schema Consolidation Strategy

### Base Schema: schema_with_auth.sql (Production Multi-Tenant)
```sql
-- Core tables da mantenere:
- accounts_tenant (tenant management)
- sessions (con tenant_id FK)
- messages (con tenant_id FK) 
- documents, chunks (con tenant_id)
- match_chunks(), hybrid_search() functions (tenant-aware)
```

### Extension Integration: section_tracking_schema.sql
```sql
-- Tabelle da aggiungere al consolidated schema:
- document_sections (tracking sezioni documento)
- section_progress (progress tracking)
- section_analytics (analytics per sezione)
-- Tutte con tenant_id per isolation
```

### Legacy Deprecation: schema.sql
```sql
-- Tabelle legacy da NON includere (deprecated):
- sessions senza tenant_id
- messages senza tenant_id
- match_chunks() senza tenant parameter
-- Queste sono incompatibili con multi-tenancy
```

## Consolidated Schema Structure

**File Target: sql/schema_consolidated.sql**

```sql
-- Header comment
-- Consolidated Database Schema for Agentic RAG Knowledge Graph
-- Combines: schema_with_auth.sql (production) + section_tracking_schema.sql (extension)
-- Deprecates: schema.sql (legacy single-tenant)

-- Extensions (from schema_with_auth.sql)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Tenant Management Tables
CREATE TABLE accounts_tenant (...);

-- Core RAG Tables (with tenant_id)
CREATE TABLE sessions (...);
CREATE TABLE messages (...);
CREATE TABLE documents (...);
CREATE TABLE chunks (...);

-- Section Tracking Extension Tables
CREATE TABLE document_sections (...);
CREATE TABLE section_progress (...);
CREATE TABLE section_analytics (...);

-- Multi-tenant RAG Functions
CREATE OR REPLACE FUNCTION match_chunks(p_tenant_id UUID, ...) ...;
CREATE OR REPLACE FUNCTION hybrid_search(p_tenant_id UUID, ...) ...;

-- Indexes for Performance
CREATE INDEX CONCURRENTLY ...;
```

## Migration Scripts

**File: sql/migrations/legacy_to_consolidated.sql**

```sql
-- Migration from schema.sql (legacy) to schema_consolidated.sql
-- WARNING: Backup database before running

-- Step 1: Add tenant support to existing tables
ALTER TABLE sessions ADD COLUMN tenant_id UUID REFERENCES accounts_tenant(id);
ALTER TABLE messages ADD COLUMN tenant_id UUID REFERENCES accounts_tenant(id);

-- Step 2: Create extension tables
CREATE TABLE document_sections (...);
CREATE TABLE section_progress (...);
CREATE TABLE section_analytics (...);

-- Step 3: Update functions to tenant-aware versions
DROP FUNCTION IF EXISTS match_chunks(vector, int);
CREATE OR REPLACE FUNCTION match_chunks(p_tenant_id UUID, ...) ...;

-- Step 4: Data migration (populate tenant_id for existing data)
UPDATE sessions SET tenant_id = 'default-tenant-uuid' WHERE tenant_id IS NULL;
UPDATE messages SET tenant_id = 'default-tenant-uuid' WHERE tenant_id IS NULL;

-- Step 5: Make tenant_id NOT NULL after data migration
ALTER TABLE sessions ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE messages ALTER COLUMN tenant_id SET NOT NULL;
```

## Validation Queries

```sql
-- Verify schema consolidation success
SELECT table_name, column_name FROM information_schema.columns 
WHERE table_schema = 'public' AND column_name = 'tenant_id';

-- Verify functions are tenant-aware
SELECT routine_name, data_type FROM information_schema.parameters 
WHERE specific_schema = 'public' AND parameter_name = 'p_tenant_id';
```