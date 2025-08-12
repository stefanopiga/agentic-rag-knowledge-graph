# Spec Tasks

## Tasks

- [x] 1. Backend Productionization
  - [x] 1.1 Aggiungere profilo `.env` production (Neon/Aura), CORS e logging
  - [x] 1.2 Aggiornare health endpoints e monitoring per ambiente cloud
  - [x] 1.3 Verifica con `tests/system/test_api_health_endpoints.py` contro istanza cloud
  - [x] 1.4 Tutti i test readiness passano

- [ ] 2. Database Managed Setup
  - [x] 2.1 Provision Neon e deploy schema con `scripts/verify_neon_schema.py`
  - [x] 2.2 Configurare Neo4j Aura, creare indice `Episode(tenant_id)` se necessario
  - [x] 2.3 Test `tests/comprehensive/test_database_connections.py` puntando a Neon/Aura
  - [x] 2.4 Tutti i test DB/Graph passano contro cloud

- [ ] 3. Centralized Ingestion
  - [ ] 3.1 Script/CLI ingestion su server con `--documents-dir` e `skip_graph_building=false`
  - [ ] 3.2 Eseguire ingestion di un documento di esempio e validare `documents/chunks` e episodi grafo
  - [ ] 3.3 Tutti i test E2E passano

- [ ] 4. Frontend Integration
  - [ ] 4.1 Build `pnpm build` e deploy statico
  - [ ] 4.2 Configurare `VITE_API_URL` al backend e CORS
  - [ ] 4.3 Smoke test UI
