-- Schema per tracking granulare delle sezioni documento
-- Consente recovery intelligente solo delle sezioni fallite

-- Tabella per tracking sezioni individuali
CREATE TABLE IF NOT EXISTS document_sections (
    id SERIAL PRIMARY KEY,
    document_status_id INTEGER REFERENCES document_ingestion_status(id) ON DELETE CASCADE,
    
    -- Identificazione sezione
    section_position INTEGER NOT NULL,
    section_type VARCHAR(50) NOT NULL,  -- paragraph, table, heading, etc.
    section_hash VARCHAR(64) NOT NULL,  -- Hash contenuto sezione
    
    -- Metadati sezione
    content_length INTEGER NOT NULL,
    content_preview TEXT,  -- Prime 200 char per debugging
    
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    error_message TEXT,
    
    -- Processing info
    chunks_created INTEGER DEFAULT 0,
    entities_extracted INTEGER DEFAULT 0,
    graph_episodes_created INTEGER DEFAULT 0,
    
    -- Timing
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata JSON per estensibilità
    metadata JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indici per performance
    CONSTRAINT unique_document_section UNIQUE (document_status_id, section_position)
);

-- Indici ottimizzati
CREATE INDEX IF NOT EXISTS idx_document_sections_status ON document_sections(document_status_id, status);
CREATE INDEX IF NOT EXISTS idx_document_sections_position ON document_sections(document_status_id, section_position);
CREATE INDEX IF NOT EXISTS idx_document_sections_failed ON document_sections(status) WHERE status IN ('failed', 'processing');

-- Vista per recovery rapido
CREATE OR REPLACE VIEW failed_sections AS
SELECT 
    ds.id,
    ds.document_status_id,
    dis.file_path,
    dis.category,
    ds.section_position,
    ds.section_type,
    ds.status,
    ds.error_message,
    ds.processing_started_at
FROM document_sections ds
JOIN document_ingestion_status dis ON ds.document_status_id = dis.id
WHERE ds.status IN ('failed', 'processing')
ORDER BY dis.file_path, ds.section_position;

-- Funzione per cleanup sezioni fallite
CREATE OR REPLACE FUNCTION cleanup_failed_sections(p_document_status_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    sections_cleaned INTEGER := 0;
BEGIN
    -- Rimuovi chunks delle sezioni fallite
    DELETE FROM chunks 
    WHERE document_id IN (
        SELECT d.id 
        FROM documents d
        JOIN document_ingestion_status dis ON d.source = dis.file_path
        WHERE dis.id = p_document_status_id
    )
    AND id IN (
        SELECT chunk_id 
        FROM document_sections ds
        WHERE ds.document_status_id = p_document_status_id 
        AND ds.status = 'failed'
    );
    
    -- Reset status sezioni fallite
    UPDATE document_sections 
    SET status = 'pending',
        error_message = NULL,
        processing_started_at = NULL,
        processing_completed_at = NULL,
        chunks_created = 0,
        entities_extracted = 0,
        graph_episodes_created = 0,
        updated_at = NOW()
    WHERE document_status_id = p_document_status_id 
    AND status = 'failed';
    
    GET DIAGNOSTICS sections_cleaned = ROW_COUNT;
    
    RETURN sections_cleaned;
END;
$$ LANGUAGE plpgsql;

-- Trigger per aggiornamento automatico timestamp
CREATE OR REPLACE FUNCTION update_document_sections_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_document_sections_timestamp
    BEFORE UPDATE ON document_sections
    FOR EACH ROW
    EXECUTE FUNCTION update_document_sections_timestamp();