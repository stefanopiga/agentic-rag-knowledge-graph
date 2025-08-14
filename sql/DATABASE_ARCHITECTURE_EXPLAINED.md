# 🏗️ **DATABASE ARCHITECTURE - SPIEGAZIONE COMPLETA**

## 📋 **RISPOSTA ALLA TUA DOMANDA**

### **Come vengono gestiti i 3 files SQL?**

#### **1. `schema.sql` → Legacy Agent OS**

```sql
-- Schema base originale (solo RAG)
documents, chunks, sessions, messages
```

**Quando usarlo**: Setup semplice senza Django
**Target**: PostgreSQL locale o cloud base

#### **2. `schema_with_auth.sql` → PRODUCTION MAIN** ⭐

```sql
-- Schema completo (913 righe)
-- Include TUTTO quello che serve
RAG + Django Auth + Multi-tenancy + Quiz + Analytics
```

**Quando usarlo**: **Deploy production su Neon PostgreSQL**
**Target**: **Database principale - contiene tutto**

#### **3. `section_tracking_schema.sql` → ESTENSIONE**

```sql
-- Aggiunge solo recovery granulare
document_sections + funzioni recovery
```

**Quando usarlo**: **DOPO aver deployato schema_with_auth.sql**
**Target**: **Estensione per file grandi**

---

## 🎯 **STRATEGIE DEPLOYMENT**

### **📊 NEON POSTGRESQL (Vector + Django)**

#### **Deploy completo:**

```bash
# STEP 1: Schema production completo
psql "$DATABASE_URL" -f sql/schema_with_auth.sql

# STEP 2: Estensione recovery (opzionale ma raccomandata)
python scripts/deploy_section_tracking.py
```

**Risultato Neon:**

```
✅ 15+ tabelle Django (accounts_user, django_admin_log, etc.)
✅ 8+ tabelle RAG (documents, chunks, embeddings, etc.)
✅ 6+ tabelle Quiz (medical_content_quiz*, etc.)
✅ 4+ tabelle Chat (rag_engine_*, etc.)
✅ 1 tabella Recovery (document_sections)
✅ Funzioni SQL (match_chunks, hybrid_search, cleanup_failed_sections)
✅ Indici ottimizzati (vector search, performance, recovery)
```

### **🌐 NEO4J AURA (Knowledge Graph)**

**Neo4j è separato:**

- **NO file SQL** (usa Cypher + Graphiti)
- **Auto-gestito** da `graph_builder.py`
- **Connection string**: `NEO4J_URI` in `.env`

**Struttura automatica:**

```cypher
// Graphiti crea automaticamente
(Document)-[:CONTAINS]->(Chunk)
(Chunk)-[:MENTIONS]->(Entity)
(Entity)-[:RELATES_TO]->(Entity)
```

---

## 🔄 **SECTION TRACKING - COME FUNZIONA**

### **Problema risolto:**

- **Prima**: File grande fallisce → Re-ingestione COMPLETA (14MB)
- **Dopo**: Sezione fallisce → Re-processamento SOLO quella sezione

### **Flusso operativo:**

#### **Durante ingestione normale:**

```python
# 1. Documento viene splittato in sezioni
for section in streaming_processor.process_docx_streaming(file_path):

    # 2. Ogni sezione viene tracciata
    section_id = await track_section(
        document_status_id=doc_id,
        section_position=position,  # 1, 2, 3, ...
        section_type="paragraph",   # paragraph, table, heading
        content=section.content,
        section_hash=hash(content)  # Per detect modifiche
    )

    # 3. Processing con recovery
    try:
        await update_section_status(section_id, 'processing')
        chunks = await process_section(section)  # Chunking + Embeddings + Graph
        await update_section_status(section_id, 'completed', chunks_created=len(chunks))
    except Exception as e:
        # 4. Fallimento sezione → continua comunque
        await update_section_status(section_id, 'failed', error_message=str(e))
        continue  # ← PROSEGUE con sezione successiva
```

#### **Stato database dopo processing:**

```sql
-- Document status: 'partial' (alcune sezioni failed)
document_ingestion_status: status='partial'

-- Section status granulare
document_sections:
  - section_position=1, status='completed', chunks_created=5
  - section_position=2, status='completed', chunks_created=3
  - section_position=3, status='failed', error_message='Timeout'
  - section_position=4, status='completed', chunks_created=4
```

### **Recovery intelligente:**

#### **Identificazione problemi:**

```bash
# Mostra sezioni fallite
python -m ingestion.ingest --recovery-report
```

```
SECTION RECOVERY REPORT
============================================================
Documents with failed sections (1):
  ✗ documents_test/01-Thoracic Pain.docx (toracico)
    Failed sections: 1 at positions [3]
```

#### **Cleanup selettivo:**

```bash
# Cleanup solo sezioni failed
python -m ingestion.ingest --cleanup-failed-sections
```

**Cosa fa la funzione `cleanup_failed_sections()`:**

1. **Rimuove chunks** solo delle sezioni failed
2. **Preserva chunks** delle sezioni completed
3. **Reset status** sezioni failed → 'pending'
4. **Mantiene tracking** per re-processing intelligente

#### **Re-processing targeted:**

```bash
# Re-run ingestione
python -m ingestion.ingest --documents documents_test --verbose
```

**Sistema intelligente:**

- ✅ **Salta** sezioni completed (già elaborate)
- 🔄 **Re-processa** solo sezioni pending/failed
- ⚡ **Performance**: Solo lavoro necessario

---

## 💡 **BENEFICI ARCHITETTURA**

### **🎯 Efficienza risorse:**

- **File 14MB con 1 sezione fallita**: Re-processa solo quella sezione
- **Nessuna duplicazione**: Chunks esistenti preservati
- **API calls ottimizzate**: Solo processing necessario

### **🔄 Resilienza produzione:**

- **Timeout singola sezione**: Non blocca documento intero
- **Recovery granulare**: Interventi mirati
- **Incrementale completo**: Seconda run solo delta

### **📊 Monitoring avanzato:**

- **Tracking precisio**: Posizione, tipo, timing, errori
- **Analytics performance**: Quali sezioni falliscono più spesso
- **Debugging facilitato**: Error message + content preview

---

## 📁 **FILE UTILIZZATI - SUMMARY**

### **Per deployment production:**

1. **`schema_with_auth.sql`** → Deploy su Neon (PRINCIPALE)
2. **`section_tracking_schema.sql`** → Estensione recovery (OPZIONALE)
3. **Neo4j**: Auto-gestito da `graph_builder.py`

### **Per testing/sviluppo:**

- **`schema.sql`** → Setup base locale senza Django

### **Per migrazione:**

- **`SCHEMA_MIGRATION_GUIDE.md`** → Procedura step-by-step

**Il sistema è progettato per essere robusto, scalabile e resiliente a fallimenti parziali.**
