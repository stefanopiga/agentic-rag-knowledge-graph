# Schema Analysis Results

## Overview

Analisi completa delle differenze tra i tre file schema SQL:

- **legacy**: `schema.sql` (5 tabelle, base RAG senza multi-tenancy)
- **production**: `schema_with_auth.sql` (19 tabelle, completo con Django auth e multi-tenancy)
- **extension**: `section_tracking_schema.sql` (1 tabella, tracking granulare sezioni)

## Table Analysis

### Overlapping Tables (5)

Tabelle presenti sia in legacy che production con differenze strutturali significative:

#### 1. `documents`

- **Legacy**: Base table senza tenant isolation
- **Production**: Multi-tenant con `tenant_id`, medical categories, extended metadata
- **Key Differences**:
  - Production aggiunge: `tenant_id UUID NOT NULL`, `category_id UUID`, structured citation fields
  - Extended metadata: `file_type`, `file_size`, `file_hash`, content statistics

#### 2. `chunks`

- **Legacy**: Base chunks senza tenant isolation
- **Production**: Multi-tenant con denormalized citation data
- **Key Differences**:
  - Production aggiunge: `tenant_id UUID NOT NULL`, position info (`start_page`, `end_page`)
  - Denormalized fields: `document_title`, `document_source` per performance

#### 3. `document_ingestion_status`

- **Legacy**: Basic ingestion tracking
- **Production**: Multi-tenant con extended error tracking
- **Key Differences**:
  - Production aggiunge: `tenant_id UUID NOT NULL`, `error_message TEXT`, `error_details JSONB`
  - Enhanced constraint: `UNIQUE(tenant_id, file_path)`

#### 4. `sessions`

- **Legacy**: Simple session management
- **Production**: Multi-tenant legacy compatibility layer
- **Key Differences**:
  - Production aggiunge: `tenant_id UUID` (nullable per backwards compatibility)

#### 5. `messages`

- **Legacy**: Basic message storage
- **Production**: Multi-tenant message storage
- **Key Differences**:
  - Production aggiunge: `tenant_id UUID` (nullable per backwards compatibility)

### Production-Only Tables (14)

Tabelle presenti solo nello schema production che forniscono funzionalità complete:

#### Multi-Tenancy Core

- `accounts_tenant`: Tenant management con subscription info
- `auth_user`: Django standard auth table
- `accounts_user`: Extended user model con tenant relationship

#### Medical Content System

- `medical_content_medicalcategory`: Medical categories con hierarchy
- `rag_engine_chatsession`: Modern chat session management
- `rag_engine_chatmessage`: Enhanced message storage con RAG metadata
- `rag_engine_queryanalytics`: Query performance e user feedback tracking

#### Quiz System (Complete)

- `medical_content_quizcategory`: Quiz categories
- `medical_content_quiz`: Quiz definitions con AI generation metadata
- `medical_content_quizquestion`: Question storage con source tracking
- `medical_content_quizanswer`: Answer options con explanations
- `medical_content_quizattempt`: User attempt tracking
- `medical_content_quizresponse`: Individual response tracking
- `medical_content_quizanalytics`: Quiz performance analytics

### Extension-Only Tables (1)

#### `document_sections`

- **Purpose**: Granular section tracking per recovery intelligente
- **Integration Need**: Deve essere aggiunto al production schema
- **Key Features**:
  - Section-level status tracking (pending/processing/completed/failed)
  - Recovery function `cleanup_failed_sections()`
  - View `failed_sections` per monitoring

## Function Analysis

### Function Conflicts (4)

Tutte le funzioni hanno conflicts tra legacy (no-tenant) e production (tenant-aware):

#### 1. `match_chunks`

- **Legacy**: `match_chunks(query_embedding, match_count)`
- **Production**: `match_chunks(p_tenant_id, query_embedding, match_count)`
- **Resolution**: Use production version (tenant-aware)

#### 2. `hybrid_search`

- **Legacy**: No tenant parameter
- **Production**: Tenant-aware con Italian language support
- **Resolution**: Use production version

#### 3. `get_document_chunks`

- **Legacy**: `get_document_chunks(doc_id)`
- **Production**: `get_document_chunks(p_tenant_id, doc_id)`
- **Resolution**: Use production version

#### 4. `update_updated_at_column`

- **Conflict**: Identical function in both schemas
- **Resolution**: Keep single version from production

## Extension Requirements

### PostgreSQL Extensions

#### Common Extensions

- `vector`: Vector similarity search (tutte le versioni)
- `uuid-ossp`: UUID generation (tutte le versioni)
- `pg_trgm`: Trigram text search (legacy, production)

#### Production-Only

- `btree_gin`: Advanced indexing per performance (production only)

#### Recommendation

Standardizzare su production extension set: `vector`, `uuid-ossp`, `pg_trgm`, `btree_gin`

## Migration Strategy

### Phase 1: Base Consolidation

1. **Base Schema**: Use `schema_with_auth.sql` as foundation
2. **Add Extension**: Integrate `document_sections` table from section_tracking_schema.sql
3. **Tenant Isolation**: Ensure all new tables have proper `tenant_id` constraints

### Phase 2: Legacy Migration

1. **ALTER TABLE Scripts**: Add `tenant_id` columns to legacy tables
2. **Data Migration**: Populate tenant_id per existing records
3. **Function Replacement**: Replace legacy functions con tenant-aware versions

### Phase 3: Cleanup

1. **Remove Legacy**: Deprecate `schema.sql`
2. **Update Documentation**: Reflect consolidated schema
3. **Application Updates**: Ensure application code works con consolidated schema

## Consolidation Recommendations

### Immediate Actions

1. ✅ **Use schema_with_auth.sql as base** (production-ready con multi-tenancy)
2. ✅ **Integrate document_sections table** from extension schema
3. ✅ **Standardize extensions** across all environments
4. ✅ **Resolve function conflicts** usando tenant-aware versions

### Schema Structure for `schema_consolidated.sql`

```sql
-- Base: schema_with_auth.sql (19 tables)
-- Add: document_sections from section_tracking_schema.sql (1 table)
-- Remove: Legacy compatibility where possible
-- Total: 20 tables con full multi-tenancy support
```

### Backward Compatibility Notes

- Sessions/messages tables mantengono nullable `tenant_id` per transition
- Legacy functions potrebbero essere wrappate per gradual migration
- RLS policies permettono fine-grained access control

## Risk Assessment

### Low Risk ✅

- Extension integration (document_sections)
- Function standardization
- New table additions

### Medium Risk ⚠️

- Tenant_id migration per existing data
- Legacy function replacement
- RLS policy enforcement

### High Risk 🔴

- Production database schema changes
- Data migration con potential downtime
- Application compatibility durante transition

## Section Tracking Dependencies Analysis

### `document_sections` Table Dependencies

#### Direct Dependencies

- **Foreign Key**: `document_status_id INTEGER REFERENCES document_ingestion_status(id) ON DELETE CASCADE`
- **Constraint**: `UNIQUE (document_status_id, section_position)`

#### Integration Requirements with Production Schema

1. **Compatible**: `document_ingestion_status` table exists in production schema
2. **Tenant Isolation Required**: Must add `tenant_id` column for multi-tenancy
3. **Index Compatibility**: All indexes are compatible with production

#### Functions in Extension Schema

##### `cleanup_failed_sections(p_document_status_id INTEGER)`

- **Purpose**: Reset failed sections for re-processing
- **Dependencies**: Accesses `chunks`, `documents`, `document_ingestion_status`
- **Integration**: Needs tenant-aware version for production

##### `update_document_sections_timestamp()`

- **Purpose**: Auto-update timestamp trigger
- **Dependencies**: None (self-contained)
- **Integration**: Ready for production

#### Views in Extension Schema

##### `failed_sections` View

- **Dependencies**: Joins `document_sections` with `document_ingestion_status`
- **Integration**: Compatible, but may need tenant filtering

#### Schema Integration Strategy

```sql
-- Required modifications for production integration:

-- 1. Add tenant_id to document_sections
ALTER TABLE document_sections
ADD COLUMN tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE;

-- 2. Update constraint to include tenant_id
ALTER TABLE document_sections
DROP CONSTRAINT unique_document_section,
ADD CONSTRAINT unique_document_section_tenant
UNIQUE (tenant_id, document_status_id, section_position);

-- 3. Add tenant isolation index
CREATE INDEX idx_document_sections_tenant
ON document_sections(tenant_id);

-- 4. Update cleanup function for tenant awareness
CREATE OR REPLACE FUNCTION cleanup_failed_sections(
    p_tenant_id UUID,
    p_document_status_id INTEGER
) ...
```

#### RLS Policy Required

```sql
ALTER TABLE document_sections ENABLE ROW LEVEL SECURITY;
CREATE POLICY section_isolation_policy
ON document_sections FOR ALL
USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

## Next Steps

1. **Create Tests**: Schema validation tests per consolidated schema
2. **Build Migration Scripts**: ALTER TABLE scripts per legacy upgrade
3. **Documentation Update**: Complete schema documentation
4. **Validation**: Test consolidated schema con existing application code
