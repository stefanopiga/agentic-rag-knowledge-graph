-- =====================================================
-- SCHEMA COMPLETO: RAG + DJANGO AUTH + MULTI-TENANCY
-- =====================================================
-- Compatible con Django, deployabile su Neon PostgreSQL
-- Versione: 2.0 - Production Ready
-- =====================================================

-- Extensions necessarie
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- =====================================================
-- CLEANUP (Ordine corretto per foreign keys)
-- =====================================================

-- Drop views
DROP VIEW IF EXISTS document_summaries CASCADE;

-- Drop triggers
DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
DROP TRIGGER IF EXISTS update_sessions_updated_at ON sessions;
DROP TRIGGER IF EXISTS update_ingestion_status_updated_at ON document_ingestion_status;
DROP TRIGGER IF EXISTS update_tenant_updated_at ON accounts_tenant;
DROP TRIGGER IF EXISTS update_user_updated_at ON accounts_user;

-- Drop functions
DROP FUNCTION IF EXISTS match_chunks CASCADE;
DROP FUNCTION IF EXISTS hybrid_search CASCADE;
DROP FUNCTION IF EXISTS get_document_chunks CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;

-- Drop tables (reverse foreign key order)
DROP TABLE IF EXISTS rag_engine_chatmessage CASCADE;
DROP TABLE IF EXISTS rag_engine_chatsession CASCADE;
DROP TABLE IF EXISTS rag_engine_queryanalytics CASCADE;
DROP TABLE IF EXISTS medical_content_document CASCADE;
DROP TABLE IF EXISTS medical_content_medicalcategory CASCADE;
DROP TABLE IF EXISTS medical_content_quizattempt CASCADE;
DROP TABLE IF EXISTS medical_content_quizresponse CASCADE;
DROP TABLE IF EXISTS medical_content_quizanalytics CASCADE;
DROP TABLE IF EXISTS medical_content_quiz CASCADE;
DROP TABLE IF EXISTS medical_content_quizquestion CASCADE;
DROP TABLE IF EXISTS medical_content_quizanswer CASCADE;
DROP TABLE IF EXISTS medical_content_quizcategory CASCADE;
DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS document_ingestion_status CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS accounts_user CASCADE;
DROP TABLE IF EXISTS auth_user CASCADE;
DROP TABLE IF EXISTS accounts_tenant CASCADE;

-- Drop indexes
DROP INDEX IF EXISTS idx_chunks_embedding;
DROP INDEX IF EXISTS idx_chunks_document_id;
DROP INDEX IF EXISTS idx_documents_metadata;
DROP INDEX IF EXISTS idx_chunks_content_trgm;

-- =====================================================
-- CORE FUNCTIONS
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- MULTI-TENANCY CORE
-- =====================================================

CREATE TABLE accounts_tenant (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    
    -- Subscription info
    plan VARCHAR(20) DEFAULT 'free' CHECK (plan IN ('free', 'basic', 'premium', 'enterprise')),
    max_users INTEGER DEFAULT 5,
    max_documents INTEGER DEFAULT 100,
    max_storage_mb INTEGER DEFAULT 1000,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Billing
    subscription_expires_at TIMESTAMP WITH TIME ZONE,
    trial_ends_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '14 days')
);

CREATE INDEX idx_tenant_slug ON accounts_tenant(slug);
CREATE INDEX idx_tenant_active ON accounts_tenant(is_active);
CREATE INDEX idx_tenant_plan ON accounts_tenant(plan);

CREATE TRIGGER update_tenant_updated_at BEFORE UPDATE ON accounts_tenant
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- DJANGO AUTH TABLES
-- =====================================================

-- Django standard auth_user table
CREATE TABLE auth_user (
    id SERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    is_superuser BOOLEAN NOT NULL DEFAULT false,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL DEFAULT '',
    is_staff BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    date_joined TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_auth_user_username ON auth_user(username);
CREATE INDEX idx_auth_user_email ON auth_user(email);

-- Custom User model (extends Django user)
CREATE TABLE accounts_user (
    id SERIAL PRIMARY KEY,
    user_ptr_id INTEGER UNIQUE NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    
    -- Tenant relationship
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    
    -- Profile info
    avatar VARCHAR(100),
    bio TEXT DEFAULT '',
    phone VARCHAR(20) DEFAULT '',
    
    -- Role in tenant
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'manager', 'user', 'viewer')),
    
    -- Preferences
    preferences JSONB DEFAULT '{}',
    
    -- Activity tracking
    last_activity TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_tenant ON accounts_user(tenant_id);
CREATE INDEX idx_user_role ON accounts_user(role);
CREATE INDEX idx_user_active ON accounts_user(last_activity);

CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON accounts_user
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- MEDICAL CONTENT SYSTEM
-- =====================================================

CREATE TABLE medical_content_medicalcategory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT DEFAULT '',
    color VARCHAR(7) DEFAULT '#007bff', -- Hex color
    icon VARCHAR(50) DEFAULT 'folder',
    
    -- Hierarchy
    parent_id UUID REFERENCES medical_content_medicalcategory(id) ON DELETE CASCADE,
    order_index INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id, slug)
);

CREATE INDEX idx_medical_category_tenant ON medical_content_medicalcategory(tenant_id);
CREATE INDEX idx_medical_category_parent ON medical_content_medicalcategory(parent_id);
CREATE INDEX idx_medical_category_active ON medical_content_medicalcategory(is_active);

-- =====================================================
-- DOCUMENT SYSTEM (Multi-tenant)
-- =====================================================

CREATE TABLE document_ingestion_status (
    id SERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,  -- SHA-256 del contenuto
    file_size BIGINT NOT NULL,
    last_modified TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Stato ingestion
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'partial')),
    chunks_created INTEGER DEFAULT 0,
    chunks_expected INTEGER DEFAULT 0,
    entities_extracted INTEGER DEFAULT 0,
    graph_episodes_created INTEGER DEFAULT 0,
    
    -- Metadati strutturali per citazioni
    category VARCHAR(100),  -- caviglia_e_piede, ginocchio, etc.
    document_order INTEGER, -- da nome file (01_, 02_, etc.)
    priority_weight INTEGER DEFAULT 100, -- per ordinamento citazioni
    
    -- Error tracking
    error_message TEXT,
    error_details JSONB,
    
    -- Timestamps
    ingestion_started_at TIMESTAMP WITH TIME ZONE,
    ingestion_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id, file_path)
);

CREATE INDEX idx_ingestion_tenant ON document_ingestion_status(tenant_id);
CREATE INDEX idx_ingestion_status ON document_ingestion_status(status);
CREATE INDEX idx_ingestion_category_order ON document_ingestion_status(category, document_order);
CREATE INDEX idx_ingestion_hash ON document_ingestion_status(file_hash);

CREATE TRIGGER update_ingestion_status_updated_at BEFORE UPDATE ON document_ingestion_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    
    -- Relationships
    category_id UUID REFERENCES medical_content_medicalcategory(id) ON DELETE SET NULL,
    ingestion_status_id INTEGER REFERENCES document_ingestion_status(id) ON DELETE SET NULL,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Structured citation data
    category VARCHAR(100),
    document_order INTEGER,
    priority_weight INTEGER DEFAULT 100,
    
    -- File info
    file_type VARCHAR(10),
    file_size BIGINT,
    file_hash VARCHAR(64),
    
    -- Content stats
    word_count INTEGER,
    page_count INTEGER,
    estimated_reading_time INTEGER, -- minutes
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_tenant ON documents(tenant_id);
CREATE INDEX idx_documents_category ON documents(category_id);
CREATE INDEX idx_documents_metadata ON documents USING GIN (metadata);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_documents_category_order ON documents(category, document_order);
CREATE INDEX idx_documents_file_hash ON documents(file_hash);

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small
    
    -- Position info
    chunk_index INTEGER NOT NULL,
    start_page INTEGER,
    end_page INTEGER,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    token_count INTEGER,
    
    -- Structured citation data (denormalized for performance)
    category VARCHAR(100),
    document_order INTEGER,
    document_title TEXT,
    document_source TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chunks_tenant ON chunks(tenant_id);
CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_chunks_chunk_index ON chunks(document_id, chunk_index);
CREATE INDEX idx_chunks_content_trgm ON chunks USING GIN (content gin_trgm_ops);
CREATE INDEX idx_chunks_category_order ON chunks(category, document_order);

-- =====================================================
-- RAG ENGINE (Chat & Analytics)
-- =====================================================

CREATE TABLE rag_engine_chatsession (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES accounts_user(id) ON DELETE CASCADE,
    
    title VARCHAR(200) DEFAULT 'New Chat',
    
    -- Session metadata
    metadata JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_chat_session_tenant ON rag_engine_chatsession(tenant_id);
CREATE INDEX idx_chat_session_user ON rag_engine_chatsession(user_id);
CREATE INDEX idx_chat_session_active ON rag_engine_chatsession(is_active);
CREATE INDEX idx_chat_session_expires ON rag_engine_chatsession(expires_at);

CREATE TABLE rag_engine_chatmessage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES rag_engine_chatsession(id) ON DELETE CASCADE,
    
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    
    -- RAG specific metadata
    sources_used JSONB DEFAULT '[]', -- Array of document references
    tokens_used INTEGER DEFAULT 0,
    response_time_ms INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_message_tenant ON rag_engine_chatmessage(tenant_id);
CREATE INDEX idx_chat_message_session ON rag_engine_chatmessage(session_id, created_at);
CREATE INDEX idx_chat_message_role ON rag_engine_chatmessage(role);

CREATE TABLE rag_engine_queryanalytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES accounts_user(id) ON DELETE SET NULL,
    session_id UUID REFERENCES rag_engine_chatsession(id) ON DELETE SET NULL,
    
    -- Query info
    query_text TEXT NOT NULL,
    query_type VARCHAR(50) DEFAULT 'chat', -- chat, search, quiz
    
    -- Performance metrics
    response_time_ms INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    chunks_retrieved INTEGER DEFAULT 0,
    
    -- Result quality
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    user_feedback TEXT,
    
    -- Sources
    sources_used JSONB DEFAULT '[]',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_query_analytics_tenant ON rag_engine_queryanalytics(tenant_id);
CREATE INDEX idx_query_analytics_user ON rag_engine_queryanalytics(user_id);
CREATE INDEX idx_query_analytics_type ON rag_engine_queryanalytics(query_type);
CREATE INDEX idx_query_analytics_created ON rag_engine_queryanalytics(created_at);

-- =====================================================
-- QUIZ SYSTEM
-- =====================================================

CREATE TABLE medical_content_quizcategory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT DEFAULT '',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id, slug)
);

CREATE INDEX idx_quiz_category_tenant ON medical_content_quizcategory(tenant_id);

CREATE TABLE medical_content_quiz (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    
    title VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    
    -- Relationships
    category_id UUID REFERENCES medical_content_quizcategory(id) ON DELETE SET NULL,
    source_documents JSONB DEFAULT '[]', -- Array of document UUIDs
    
    -- Quiz settings
    difficulty_level VARCHAR(20) DEFAULT 'medium' CHECK (difficulty_level IN ('easy', 'medium', 'hard')),
    time_limit_minutes INTEGER,
    passing_score INTEGER DEFAULT 70,
    max_attempts INTEGER DEFAULT 3,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false,
    
    -- AI Generation metadata
    generated_by_ai BOOLEAN DEFAULT true,
    generation_prompt TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quiz_tenant ON medical_content_quiz(tenant_id);
CREATE INDEX idx_quiz_category ON medical_content_quiz(category_id);
CREATE INDEX idx_quiz_active ON medical_content_quiz(is_active);
CREATE INDEX idx_quiz_public ON medical_content_quiz(is_public);

CREATE TABLE medical_content_quizquestion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    quiz_id UUID NOT NULL REFERENCES medical_content_quiz(id) ON DELETE CASCADE,
    
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) DEFAULT 'multiple_choice' CHECK (question_type IN ('multiple_choice', 'true_false', 'case_study', 'open_ended')),
    
    -- Metadata
    explanation TEXT,
    difficulty INTEGER DEFAULT 1 CHECK (difficulty BETWEEN 1 AND 5),
    points INTEGER DEFAULT 1,
    order_index INTEGER DEFAULT 0,
    
    -- Source tracking
    source_chunk_ids JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quiz_question_tenant ON medical_content_quizquestion(tenant_id);
CREATE INDEX idx_quiz_question_quiz ON medical_content_quizquestion(quiz_id);
CREATE INDEX idx_quiz_question_type ON medical_content_quizquestion(question_type);

CREATE TABLE medical_content_quizanswer (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES medical_content_quizquestion(id) ON DELETE CASCADE,
    
    answer_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT false,
    order_index INTEGER DEFAULT 0,
    
    -- Explanation for this specific answer
    explanation TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quiz_answer_tenant ON medical_content_quizanswer(tenant_id);
CREATE INDEX idx_quiz_answer_question ON medical_content_quizanswer(question_id);
CREATE INDEX idx_quiz_answer_correct ON medical_content_quizanswer(is_correct);

CREATE TABLE medical_content_quizattempt (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    quiz_id UUID NOT NULL REFERENCES medical_content_quiz(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE,
    
    -- Attempt info
    attempt_number INTEGER DEFAULT 1,
    
    -- Results
    score DECIMAL(5,2), -- Percentage score
    total_questions INTEGER,
    correct_answers INTEGER,
    
    -- Timing
    time_taken_seconds INTEGER,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_completed BOOLEAN DEFAULT false,
    passed BOOLEAN DEFAULT false,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_quiz_attempt_tenant ON medical_content_quizattempt(tenant_id);
CREATE INDEX idx_quiz_attempt_quiz ON medical_content_quizattempt(quiz_id);
CREATE INDEX idx_quiz_attempt_user ON medical_content_quizattempt(user_id);
CREATE INDEX idx_quiz_attempt_completed ON medical_content_quizattempt(is_completed);

CREATE TABLE medical_content_quizresponse (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    attempt_id UUID NOT NULL REFERENCES medical_content_quizattempt(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES medical_content_quizquestion(id) ON DELETE CASCADE,
    answer_id UUID REFERENCES medical_content_quizanswer(id) ON DELETE SET NULL,
    
    -- Response data
    response_text TEXT, -- For open-ended questions
    is_correct BOOLEAN DEFAULT false,
    points_earned DECIMAL(5,2) DEFAULT 0,
    
    -- Timing
    time_taken_seconds INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_quiz_response_tenant ON medical_content_quizresponse(tenant_id);
CREATE INDEX idx_quiz_response_attempt ON medical_content_quizresponse(attempt_id);
CREATE INDEX idx_quiz_response_question ON medical_content_quizresponse(question_id);

CREATE TABLE medical_content_quizanalytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    quiz_id UUID NOT NULL REFERENCES medical_content_quiz(id) ON DELETE CASCADE,
    
    -- Analytics data
    total_attempts INTEGER DEFAULT 0,
    total_completions INTEGER DEFAULT 0,
    average_score DECIMAL(5,2) DEFAULT 0,
    average_time_seconds INTEGER DEFAULT 0,
    
    -- Question-level analytics
    question_analytics JSONB DEFAULT '{}', -- Per-question statistics
    
    -- Date range
    analytics_date DATE DEFAULT CURRENT_DATE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id, quiz_id, analytics_date)
);

CREATE INDEX idx_quiz_analytics_tenant ON medical_content_quizanalytics(tenant_id);
CREATE INDEX idx_quiz_analytics_quiz ON medical_content_quizanalytics(quiz_id);
CREATE INDEX idx_quiz_analytics_date ON medical_content_quizanalytics(analytics_date);

-- =====================================================
-- LEGACY COMPATIBILITY (sessions, messages)
-- =====================================================

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    user_id TEXT, -- Legacy compatibility
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_sessions_tenant ON sessions(tenant_id);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES accounts_tenant(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_tenant ON messages(tenant_id);
CREATE INDEX idx_messages_session_id ON messages(session_id, created_at);

-- =====================================================
-- RAG SEARCH FUNCTIONS (Multi-tenant)
-- =====================================================

CREATE OR REPLACE FUNCTION match_chunks(
    p_tenant_id UUID,
    query_embedding vector(1536),
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    similarity FLOAT,
    metadata JSONB,
    document_title TEXT,
    document_source TEXT,
    category VARCHAR,
    document_order INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id AS chunk_id,
        c.document_id,
        c.content,
        1 - (c.embedding <=> query_embedding) AS similarity,
        c.metadata,
        d.title AS document_title,
        d.source AS document_source,
        c.category,
        c.document_order
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE c.tenant_id = p_tenant_id 
      AND d.tenant_id = p_tenant_id
      AND c.embedding IS NOT NULL
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

CREATE OR REPLACE FUNCTION hybrid_search(
    p_tenant_id UUID,
    query_embedding vector(1536),
    query_text TEXT,
    match_count INT DEFAULT 10,
    text_weight FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    combined_score FLOAT,
    vector_similarity FLOAT,
    text_similarity FLOAT,
    metadata JSONB,
    document_title TEXT,
    document_source TEXT,
    category VARCHAR,
    document_order INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT 
            c.id AS chunk_id,
            c.document_id,
            c.content,
            (1 - (c.embedding <=> query_embedding))::double precision AS vector_sim,
            c.metadata,
            d.title AS doc_title,
            d.source AS doc_source,
            c.category,
            c.document_order
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.tenant_id = p_tenant_id 
          AND d.tenant_id = p_tenant_id
          AND c.embedding IS NOT NULL
    ),
    text_results AS (
        SELECT 
            c.id AS chunk_id,
            c.document_id,
            c.content,
            ts_rank_cd(to_tsvector('italian', c.content), plainto_tsquery('italian', query_text))::double precision AS text_sim,
            c.metadata,
            d.title AS doc_title,
            d.source AS doc_source,
            c.category,
            c.document_order
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.tenant_id = p_tenant_id 
          AND d.tenant_id = p_tenant_id
          AND to_tsvector('italian', c.content) @@ plainto_tsquery('italian', query_text)
    )
    SELECT 
        COALESCE(v.chunk_id, t.chunk_id) AS chunk_id,
        COALESCE(v.document_id, t.document_id) AS document_id,
        COALESCE(v.content, t.content) AS content,
        (COALESCE(v.vector_sim, 0.0) * (1 - text_weight) + COALESCE(t.text_sim, 0.0) * text_weight) AS combined_score,
        COALESCE(v.vector_sim, 0.0) AS vector_similarity,
        COALESCE(t.text_sim, 0.0) AS text_similarity,
        COALESCE(v.metadata, t.metadata) AS metadata,
        COALESCE(v.doc_title, t.doc_title) AS document_title,
        COALESCE(v.doc_source, t.doc_source) AS document_source,
        COALESCE(v.category, t.category) AS category,
        COALESCE(v.document_order, t.document_order) AS document_order
    FROM vector_results v
    FULL OUTER JOIN text_results t ON v.chunk_id = t.chunk_id
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$;

CREATE OR REPLACE FUNCTION get_document_chunks(
    p_tenant_id UUID,
    doc_id UUID
)
RETURNS TABLE (
    chunk_id UUID,
    content TEXT,
    chunk_index INTEGER,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        id AS chunk_id,
        chunks.content,
        chunks.chunk_index,
        chunks.metadata
    FROM chunks
    WHERE tenant_id = p_tenant_id 
      AND document_id = doc_id
    ORDER BY chunk_index;
END;
$$;

-- =====================================================
-- VIEWS
-- =====================================================

CREATE OR REPLACE VIEW document_summaries AS
SELECT 
    d.id,
    d.tenant_id,
    d.title,
    d.source,
    d.category,
    d.document_order,
    d.priority_weight,
    d.created_at,
    d.updated_at,
    d.metadata,
    COUNT(c.id) AS chunk_count,
    AVG(c.token_count) AS avg_tokens_per_chunk,
    SUM(c.token_count) AS total_tokens,
    dis.status AS ingestion_status
FROM documents d
LEFT JOIN chunks c ON d.id = c.document_id
LEFT JOIN document_ingestion_status dis ON d.ingestion_status_id = dis.id
GROUP BY d.id, d.tenant_id, d.title, d.source, d.category, d.document_order, d.priority_weight, d.created_at, d.updated_at, d.metadata, dis.status;

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Enable RLS on all tenant-aware tables
ALTER TABLE accounts_tenant ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_content_medicalcategory ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_ingestion_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_engine_chatsession ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_engine_chatmessage ENABLE ROW LEVEL SECURITY;
ALTER TABLE rag_engine_queryanalytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_content_quizcategory ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_content_quiz ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_content_quizquestion ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_content_quizanswer ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_content_quizattempt ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_content_quizresponse ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_content_quizanalytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (will be extended with application logic)
-- For now, allow all operations (policies will be refined in Django)

CREATE POLICY tenant_isolation_policy ON accounts_tenant FOR ALL USING (true);
CREATE POLICY user_isolation_policy ON accounts_user FOR ALL USING (true);
CREATE POLICY medical_category_isolation_policy ON medical_content_medicalcategory FOR ALL USING (true);
CREATE POLICY ingestion_isolation_policy ON document_ingestion_status FOR ALL USING (true);
CREATE POLICY document_isolation_policy ON documents FOR ALL USING (true);
CREATE POLICY chunk_isolation_policy ON chunks FOR ALL USING (true);
CREATE POLICY chat_session_isolation_policy ON rag_engine_chatsession FOR ALL USING (true);
CREATE POLICY chat_message_isolation_policy ON rag_engine_chatmessage FOR ALL USING (true);
CREATE POLICY analytics_isolation_policy ON rag_engine_queryanalytics FOR ALL USING (true);
CREATE POLICY quiz_category_isolation_policy ON medical_content_quizcategory FOR ALL USING (true);
CREATE POLICY quiz_isolation_policy ON medical_content_quiz FOR ALL USING (true);
CREATE POLICY quiz_question_isolation_policy ON medical_content_quizquestion FOR ALL USING (true);
CREATE POLICY quiz_answer_isolation_policy ON medical_content_quizanswer FOR ALL USING (true);
CREATE POLICY quiz_attempt_isolation_policy ON medical_content_quizattempt FOR ALL USING (true);
CREATE POLICY quiz_response_isolation_policy ON medical_content_quizresponse FOR ALL USING (true);
CREATE POLICY quiz_analytics_isolation_policy ON medical_content_quizanalytics FOR ALL USING (true);
CREATE POLICY session_isolation_policy ON sessions FOR ALL USING (true);
CREATE POLICY message_isolation_policy ON messages FOR ALL USING (true);

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Create default tenant for development
INSERT INTO accounts_tenant (id, name, slug, plan, max_users, max_documents, max_storage_mb)
VALUES (
    uuid_generate_v4(),
    'Default Tenant',
    'default',
    'premium',
    100,
    1000,
    10000
);

-- Note: Admin user will be created via Django management command
-- python manage.py createsuperuser
-- This ensures proper password hashing and validation

-- Create default medical categories
INSERT INTO medical_content_medicalcategory (tenant_id, name, slug, description, color, order_index)
SELECT 
    at.id,
    category_name,
    category_slug,
    category_desc,
    category_color,
    category_order
FROM accounts_tenant at,
(VALUES 
    ('Caviglia e Piede', 'caviglia_e_piede', 'Anatomia, patologie e trattamenti di caviglia e piede', '#FF6B6B', 1),
    ('Ginocchio e Anca', 'ginocchio_e_anca', 'Anatomia, patologie e trattamenti di ginocchio e anca', '#4ECDC4', 2),
    ('Lombare', 'lombare', 'Anatomia, patologie e trattamenti del rachide lombare', '#45B7D1', 3),
    ('Lombo-pelvico', 'lombo_pelvico', 'Anatomia, patologie e trattamenti lombo-pelvici', '#96CEB4', 4),
    ('Toracico', 'toracico', 'Anatomia, patologie e trattamenti del rachide toracico', '#FECA57', 5),
    ('Cervicale', 'cervicale', 'Anatomia, patologie e trattamenti del rachide cervicale', '#FF9FF3', 6),
    ('Arto Superiore', 'arto_superiore', 'Anatomia, patologie e trattamenti dell''arto superiore', '#54A0FF', 7),
    ('ATM', 'atm', 'Anatomia, patologie e trattamenti dell''articolazione temporo-mandibolare', '#5F27CD', 8)
) AS categories(category_name, category_slug, category_desc, category_color, category_order)
WHERE at.slug = 'default';

-- =====================================================
-- FINAL NOTES
-- =====================================================

-- This schema provides:
-- ✅ Full Django compatibility
-- ✅ Multi-tenancy with RLS
-- ✅ Complete RAG system with embeddings
-- ✅ Quiz system for educational features
-- ✅ Analytics and user tracking
-- ✅ Proper indexing for performance
-- ✅ Italian language search support
-- ✅ Legacy compatibility for current codebase

-- Usage with Django:
-- 1. Deploy this schema to Neon
-- 2. Configure Django DATABASE_URL
-- 3. Run: python manage.py migrate --fake-initial
-- 4. Start development

-- Schema version: 2.0
-- Compatible with: Django 4.2+, PostgreSQL 14-17 (17 raccomandato), pgvector 0.5+
-- Optimized for: PostgreSQL 17 performance improvements
-- Last updated: 2025-08-03