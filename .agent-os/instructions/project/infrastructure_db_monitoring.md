## Guida Infrastruttura, Database e Monitoring (Agent OS)

### Scopo

Riferimento operativo per Agent OS su: cartelle infrastrutturali (`monitoring`, `load_testing`, `security`, `pg-vector`, `htmlcov`), architettura database con Docker/Neon, variabili chiave e flag.

### Cartelle infrastrutturali

- monitoring: stack Prometheus/Grafana/Alertmanager opzionale per osservabilità. L'API espone `/metrics` quando `ENABLE_METRICS=true`. Avvio:

  ```cmd
  docker network create fisiorag 2>nul
  docker compose -f monitoring/docker-compose.monitoring.yml up -d
  ```

  Note: il compose di monitoring assume la rete Docker esterna `fisiorag` per raggiungere `app`, `postgres`, `redis`, `neo4j`.

- load_testing: suite di test di carico (Locust + orchestratore). Opzionale, utile per validazione performance.

  ```cmd
  uv run python load_testing\run_scalability_tests.py --quick
  :: oppure Locust
  uv run locust -f load_testing\locustfile.py --host http://localhost:8000
  ```

- security: middleware di sicurezza e audit (GDPR/HIPAA/SOC2). Non abilitato di default in `agent/api.py`. Audit completo:

  ```cmd
  uv run python security\run_security_audit.py --comprehensive --environment production
  ```

  Integrazione middleware (quando necessario): usare `setup_security_middleware(app, SecurityLevel.HEALTHCARE)`.

- pg-vector: risorse per installare l'estensione `vector` su PostgreSQL Windows locale. Non necessaria in Docker (immagine `pgvector/pgvector`) né su Neon se l'estensione è disponibile lato cloud.

- htmlcov: report di coverage generato dai test. Artefatto di debug, non richiesto per il run.

### Database: Docker locale vs Neon

- Compose locale: di default l'app usa PostgreSQL del compose.
  - `docker-compose.yml` imposta per `app`:
    - `DATABASE_URL=postgresql://rag_user:rag_password@postgres:5432/rag_db`
    - `NEO4J_URI=bolt://neo4j:7687`
    - `REDIS_URL=redis://redis:6379/0`
  - Lo schema è applicato montando `sql/schema_with_auth.sql` sul container `postgres`.

- Architettura multi-tenant: un solo database condiviso con isolamento per `tenant_id` (tutte le tabelle chiave includono `tenant_id`). Non è previsto “un DB per utente”.

- Selezione del database: fa fede `DATABASE_URL`. I documenti ingeriti e le query scrivono/leggono dal DB puntato da questa variabile. Se stai usando il compose locale, i dati non finiscono su Neon.

### Uso di Neon PostgreSQL

1. Imposta `DATABASE_URL` al DSN Neon nell'ambiente dell'app e degli strumenti (ingestion/test).
   - `.env` (letta dal compose) deve contenere il DSN Neon; `env.txt` è un template e non è caricato automaticamente dal compose.
2. Deploy schema su Neon:
   ```cmd
   uv run python deploy_neon_schema.py "<DSN_NEON>"
   uv run python scripts\verify_neon_schema.py "<DSN_NEON>"
   ```
3. Esegui ingestion puntando a Neon (stessa `DATABASE_URL`). Verifica che l'estensione `vector` sia disponibile lato Neon (lo schema esegue `CREATE EXTENSION IF NOT EXISTS vector;`).

### Flag e variabili rilevanti

- DISABLE_DB_PERSISTENCE: se `true` (default in `env.txt`) evita la persistenza dei messaggi di chat nelle rotte API. Non influisce sull'ingestion documenti.
- ENABLE_METRICS: abilita `/metrics` Prometheus.
- `.env` vs `env.txt`: il compose legge `.env`. Copia/riporta i valori da `env.txt` in `.env` o esporta le variabili nell'ambiente.

#### Modalità ingestion offline (senza LLM/Neo4j)

- Scopo: validare pipeline e schema Postgres senza dipendenze esterne.
- Requisiti minimi `.env`:
  - `DATABASE_URL=postgresql://rag_user:rag_password@localhost:55432/rag_db`
  - `EMBEDDINGS_OFFLINE=1`
  - Opzionali: `APP_ENV`, `LOG_LEVEL`, `ENABLE_METRICS`, `DISABLE_DB_PERSISTENCE`
- Esecuzione:
  - Avvio DB: `docker compose up -d postgres redis` (Neo4j non necessario)
  - Ingestion: usare `IngestionConfig(skip_graph_building=true)` oppure lo script `scripts/run_ingest_no_graph.py`
  - Test post‑ingestion: `uv run pytest -q tests/post_ingestion/test_postgres_ingestion.py`
- Note implementative:
  - `ingestion/ingest.py` evita la creazione/uso di `GraphBuilder` e la pulizia Neo4j quando `skip_graph_building=True`.
  - Le embedding vengono generate come vettori zero quando `EMBEDDINGS_OFFLINE=1`.
  - Il tenant `default` viene creato automaticamente se assente.

### Ingestion completa (DB + Grafo + LLM)

Prerequisiti:

- `.env` con chiavi reali: `LLM_API_KEY`, `EMBEDDING_API_KEY` (+ eventuali `LLM_BASE_URL`, `EMBEDDING_BASE_URL`, `LLM_CHOICE`, `EMBEDDING_MODEL`).
- Neo4j con credenziali allineate:
  - `docker compose exec -T neo4j printenv NEO4J_AUTH`
  - Assicurati che in `.env` `NEO4J_USER`/`NEO4J_PASSWORD` coincidano.
  - Se necessario, ricrea Neo4j e volume per resettare rate‑limit/auth:
    `cmd
docker compose down
docker volume rm -f agentic-rag-knowledge-graph_neo4j_data
docker compose up -d neo4j
docker compose exec -T neo4j printenv NEO4J_AUTH
    `
- Postgres pronto e schema applicato (locale o Neon):
  ```cmd
  docker compose up -d postgres redis
  docker compose exec -T postgres pg_isready -U rag_user -d rag_db
  docker compose exec -T postgres psql -U rag_user -d rag_db -f /docker-entrypoint-initdb.d/init.sql
  ```

Esecuzione ingestion completa (esempio sottoinsieme):

```cmd
uv run python -m ingestion.ingest --clean --documents-dir documents_total\fisioterapia\master\ginocchio_e_anca --tenant-slug default
```

Verifiche rapide:

```cmd
docker compose exec -T postgres psql -U rag_user -d rag_db -c "SELECT COUNT(*) AS documents FROM documents; SELECT COUNT(*) AS chunks FROM chunks;"
```

Note operative:

- Windows CMD: evitare pipe come `| cat`. Usare comandi diretti o `type` dove necessario.
- Sanitizzazione `DATABASE_URL` (spazi/virgolette) è gestita a codice in `agent/db_utils.py`.

#### Neo4j: host vs container e rate‑limit

- Dentro i container: usare `NEO4J_URI=bolt://neo4j:7687`.
- Da host Windows: usare `NEO4J_URI=bolt://localhost:7687` oppure definire `NEO4J_URI_HOST=bolt://localhost:7687` (il codice preferisce `NEO4J_URI_HOST` quando presente) per evitare la risoluzione del nome `neo4j`.
- Password: deve coincidere con `NEO4J_AUTH` del container (`docker compose exec -T neo4j printenv NEO4J_AUTH`). Esempio: `neo4j/password`.
- Rate‑limit autenticazione: se compare `AuthenticationRateLimit`, riavviare Neo4j e attendere 90–150 secondi prima di riprovare.

### Verifica end‑to‑end (Windows)

Script di verifica rapida locale:

```cmd
scripts\system_e2e_check_windows.cmd
```

Esegue: avvio DB, applicazione schema, health‑check API, test DB, ingestion (se directory documenti presente) e test post‑ingestion.

### Monitoring: integrazione con l'app

L'API include `MonitoringMiddleware` e metriche personalizzate (Prometheus FastAPI Instrumentator). Per avviare lo stack di monitoring locale:

```cmd
docker network create fisiorag 2>nul
docker compose -f monitoring\docker-compose.monitoring.yml up -d
```

Prometheus scrappa `app:8000/metrics`; exporter configurati per Postgres, Redis, Node Exporter e cAdvisor.
