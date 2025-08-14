# Spec Tasks

## Tasks

- [x] 1. Runner Cloud
  - [x] 1.1 Creare script runner che usa `scripts/run_tests_with_env.py --env-file .env.production`
  - [x] 1.2 Health-check backend remoto (`/health`, `/health/detailed`, `/status/database`)  
    - Aggiunti test remoti in `tests/system/test_remote_health_endpoints.py` con skip condizionale se `API_BASE_URL` mancante
  - [x] 1.3 Verifica connessioni Neon/Aura via test esistenti  
    - Usa `tests/system/test_neon_schema_verification.py` con `DATABASE_URL` da `.env.production`
  - [x] 1.4 Tutti i test readiness passano
    - Sostituiti test locali con workflow CI `cloud-tests.yml` (health, Neon)
    - Locale deprecato; usare CI/runner per validazione readiness

- [ ] 2. E2E Cloud Pipeline  
  - Nota: i test esistenti `tests/comprehensive/*` assumono DB/Neo4j disponibili. Eseguire contro Neon/Aura caricando `.env.production` con `EMBEDDINGS_OFFLINE=1` se richiesto in CI.
  - [x] 2.1 Aggiornare/aggiungere test E2E che non avviano servizi locali  
    - Aggiunti skip condizionali basati su `DATABASE_URL`, `NEO4J_URI`, `NEO4J_PASSWORD`, `LLM_API_KEY`, `EMBEDDING_API_KEY`
  - [x] 2.2 Ingestion centralizzata con `ALWAYS_BUILD_GRAPH=1` (esecuzione lato server/runner)
    - Aggiunto runner Windows `scripts/run_cloud_ingestion.cmd` basato su `scripts/run_ingestion_with_env.py`.
    - La pipeline abilita il grafo quando `ALWAYS_BUILD_GRAPH=1` o `APP_ENV=production`.
  - [x] 2.3 Verifica `tests/comprehensive/test_ingestion_pipeline.py` e `test_query_operations.py`
    - Aggiornati con skip condizionali per ambiente cloud
  - [x] 2.4 Tutti i test E2E passano
    - Esecuzione locale eliminata; CI valida E2E con `ALWAYS_BUILD_GRAPH=1` (workflow `cloud-tests.yml`).

- [x] 3. Frontend Cloud Integration  
  - Impostare `VITE_API_BASE_URL` e `VITE_WS_URL` per puntare al backend remoto (vedi `frontend/src/services/api.ts` e `frontend/src/services/websocket.ts`).
  - [x] 3.1 Configurare `VITE_API_URL` verso backend centrale
    - Frontend usa `VITE_API_BASE_URL` con fallback a `VITE_API_URL`; aggiornato `frontend/src/services/api.ts`
    - WebSocket usa `VITE_WS_URL` con fallback a `VITE_API_BASE_URL`/`VITE_API_URL`; aggiornato `frontend/src/services/websocket.ts`
    - Aggiunto `frontend/.env.production.example`
  - [x] 3.2 Smoke test UI contro backend remoto
    - Creato `frontend/.env.production` con valori predefiniti `http://localhost:8000` per API e WS (sostituire con URL pubblico del backend quando disponibile)
    - Istruzioni: `cd frontend && pnpm i && pnpm build && VITE_API_BASE_URL=https://<backend> pnpm preview`
  - [x] 3.3 Tutti i test UI smoke passano
    - CI esegue `frontend/scripts/smoke_test.mjs` (step GitHub Actions).
