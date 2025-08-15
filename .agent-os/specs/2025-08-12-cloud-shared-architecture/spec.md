# Spec Requirements Document

> Spec: cloud-shared-architecture
> Created: 2025-08-12
> Status: Planning

## Overview

Rifattorizzazione del progetto per esecuzione “Cloud condivisa”: backend FastAPI centralizzato su VPS/PaaS, database gestiti (Neo4j Aura obbligatorio, Postgres Neon), frontend servito come statico o con `VITE_API_URL` verso il backend. Obiettivo: zero setup client, segreti centralizzati, costo basso.

## User Stories

### Docente – Eroga ambiente condiviso

As a teacher, I want to host a single backend and managed databases so that students can use the tool from the browser without local setup.

- Deploy backend su server
- Configurazione env per Aura/Neon
- CORS/HTTPS configurati
- Ingestion centralizzata

### Studente – Usa solo il browser

As a student, I want to access the app via an URL so that I can study i documenti medici con l’LLM senza installazioni.

- Accesso UI
- Query/Chat funzionanti

## Spec Scope

1. **Configurazione Backend Cloud** - `.env.production` production, CORS, HTTPS, logging, monitoring
2. **DB Gestiti** - Connessioni Neo4j Aura e Neon; migrazione schema
3. **Ingestion Centralizzata** - Script/CLI per ingest su server
4. **Frontend** - Build static e configurazione `VITE_API_URL`
5. **CI/CD** - Workflow build, deploy, smoke test

## Out of Scope

- Billing avanzato
- SSO/IdP enterprise

## Expected Deliverable

1. Backend deployabile su server con `.env.production` production; health ok
2. Frontend raggiungibile e integrato; ingestion centralizzata funzionante

## Decisioni Architetturali (ADR)

- Backend centralizzato (FastAPI) con database gestiti: Postgres Neon e Neo4j Aura.
- Schema Postgres utilizzato: `sql/schema_with_auth.sql` (RAG + Auth + Multi‑tenancy + Quiz + Analytics).
- Funzioni SQL richieste e verificate: `match_chunks`, `hybrid_search`, `get_document_chunks`, `update_updated_at_column`.
- Estensioni richieste: `vector`, `uuid-ossp`, `pg_trgm`, `btree_gin`.
- Indice Neo4j obbligatorio per multi‑tenant: `:Episode(tenant_id)`; creato da `scripts/prepare_neo4j_aura.py` e garantito a runtime in `agent/graph_utils.py`.
- Politica embeddings: in produzione l’embedder è sempre attivo (`EMBEDDINGS_OFFLINE=0`) e le risposte usano ricerca ibrida (vettoriale + testo) come percorso predefinito.
- Politica ingestion: in produzione il grafo deve essere costruito sempre (`ALWAYS_BUILD_GRAPH=1`) oppure automaticamente quando `APP_ENV=production`.
- Sicurezza connessioni: `DATABASE_URL` con `sslmode=require` (Neon), `NEO4J_URI` con `neo4j+s://` (Aura TLS).
- Segreti: usare solo `.env.production` a runtime; non stampare né commitare i valori.

## Ambiente di Produzione (`.env.production`)

Variabili chiave:

- App: `APP_ENV=production`, `APP_HOST`, `APP_PORT`, `LOG_LEVEL`, `ENABLE_METRICS`.
- CORS: `CORS_ALLOWED_ORIGINS` (valori espliciti in produzione).
- Postgres (Neon): `DATABASE_URL` con `sslmode=require`.
- Neo4j (Aura): `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`.
- Redis: `REDIS_URL`, `REDIS_MAX_MEMORY`,`REDIS_EVICTION_POLICY`
- LLM/Embeddings: `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_CHOICE`, `EMBEDDING_PROVIDER`, `EMBEDDING_BASE_URL`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL`, `VECTOR_DIMENSION`, `MAX_SEARCH_RESULTS`.
- Ingestion/Grafo: `ALWAYS_BUILD_GRAPH=1`, `EMBEDDINGS_OFFLINE=0`, `DISABLE_DB_PERSISTENCE=false`.
- Timeouts/Ritenti: `OPENAI_TIMEOUT`, `OPENAI_MAX_RETRY`, `OPENAI_RETRY_DELAY`.
- Chunking Configuration (optimized for Graphiti token limits): `CHUNK_SIZE`, `CHUNK_OVERLAP`, `MAX_CHUNK_SIZE`
- Session Configuration: `SESSION_TIMEOUT_MINUTES`, `MAX_MESSAGES_PER_SESSION`
- Rate Limiting: `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`
- File Processing: `MAX_FILE_SIZE_MB`, `ALLOWED_FILE_EXTENSIONS`
- Debug Configuration: `DEBUG_MODE`, `ENABLE_PROFILING`


Nota: usare esclusivamente `.env.production` nei run operativi e nelle pipeline CI/CD che interagiscono con i servizi cloud. (se tenterai di verificare l'esistenza del .env o .env.production, l'esito sarà sempre negativo perchè non hai accesso a questo tipo di file, il file esiste ma tu non lo puoi vedere)

## Runbook Operativo (Cloud). 

Accertarsi che il codice di test e il codice sorgente convergano per logica. 
Strutturare tutti i file di test con solida logica di debug in modo che restituiscano abbondanti e utili logs da leggere per individuare l'errore e correggerlo in modo mirato. 

1. Deploy schema su Neon

```bash
python deploy_neon_schema.py "$DATABASE_URL"
```

2. Verifica schema Neon (genera JSON di report)

```bash
python scripts/verify_neon_schema.py
# artefatto: neon_verification_YYYYMMDD_HHMMSS.json
```

3. Preparazione Neo4j Aura (indice per tenant)

```bash
python scripts/prepare_neo4j_aura.py
```

4. Connettività rapida Neo4j

```bash
python scripts/test_neo4j_connectivity.py
```

5. Ingestion centralizzata (produzione)

```bash
set ALWAYS_BUILD_GRAPH=1
python -m ingestion.ingest --documents-dir documents --tenant-slug default
```

## Convalida Cloud

- Test DB/Graph (Neon/Aura):

```bash
pytest -q tests/comprehensive/test_database_connections.py
```

- Pipeline ingestion (DB only per verifica base):

```bash
pytest -q tests/comprehensive/test_ingestion_pipeline.py
```

- Query vettoriali/ibride (embedder online):

```bash
pytest -q tests/comprehensive/test_query_operations.py
```

Esito atteso: tutti i test passano contro le istanze cloud; eventuale warning ammesso: assenza admin Django (creato in fase applicativa).

## Osservabilità e Health

- Endpoint: `/health`, `/health/detailed`, `/status/database`.
- Metriche: `ENABLE_METRICS=true` abilita esporter Prometheus (configurazione monitoring separata).

## Sicurezza e Compliance

- Non loggare né stampare variabili di `.env.production`.
- Verificare `sslmode=require` su Postgres e `neo4j+s://` su Aura.
- CORS con whitelist domini di frontend.
