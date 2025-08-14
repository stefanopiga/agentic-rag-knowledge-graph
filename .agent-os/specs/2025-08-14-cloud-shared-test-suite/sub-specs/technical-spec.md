# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-14-cloud-shared-test-suite/spec.md

## Technical Requirements

- Runner Cloud
  - Usare `scripts/run_tests_with_env.py --env-file .env.production` per caricare variabili cloud
  - Non avviare servizi locali (no docker compose di postgres/neo4j/redis/app)
  - Health check contro backend remoto (`/health`, `/health/detailed`, `/status/database`)
- Configurazione
  - `.env.production`: `DATABASE_URL` (Neon, sslmode=require), `NEO4J_URI` Aura `neo4j+s://`, `NEO4J_USER/PASSWORD`
  - `EMBEDDINGS_OFFLINE=1` per test deterministici in CI; `=0` in staging/prod
  - `ALWAYS_BUILD_GRAPH=1` per ingestion centralizzata nei test E2E
- Suite
  - Aggiornare test per evitare assunzioni su servizi locali
  - Aggiungere skip condizionali se variabili cloud mancanti

## External Dependencies (Conditional)

- Nessuna nuova dipendenza obbligatoria