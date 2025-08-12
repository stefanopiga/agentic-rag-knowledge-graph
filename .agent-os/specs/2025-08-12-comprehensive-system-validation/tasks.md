# Spec Tasks

## Tasks

- [ ] 1. System Readiness & Health
  - [x] 1.1 Verificare connessioni e credenziali (Postgres/Neo4j/Redis) e health endpoints API
  - [x] 1.2 Eseguire test connessioni DB/Graph e health-check pool (pgvector/funzioni)
  - [x] 1.3 Eseguire verifica schema Neon (`scripts/verify_neon_schema.py`) con assert principali
  - [x] 1.4 Verificare che tutti i test readiness passino

- [ ] 2. Embeddings & Agent Tools
  - [x] 2.1 Forzare `EMBEDDINGS_OFFLINE=1` e testare embedder (singolo/batch) e dimensione vettori
  - [x] 2.2 Testare `vector_search`/`hybrid_search` contro schema funzioni
  - [x] 2.3 Testare `search_knowledge_graph` per tenant
  - [x] 2.4 Verificare che tutti i test embeddings/tools passino

- [ ] 3. Ingestion E2E
  - [x] 3.1 Ingestione di un DOCX di esempio (tenant `default`) e assert su `documents`/`chunks`
  - [x] 3.2 (Condizionale) Attivare `skip_graph_building=false` e verificare episodi `Episode(tenant_id)`
  - [x] 3.3 Verificare che tutti i test E2E passino

- [ ] 4. Frontend Chat Smoke (Condizionale)
  - [ ] 4.1 Avvio Vite dev con `VITE_API_URL` puntato al backend
  - [ ] 4.2 Verifica routing `/chat` e input messaggi (smoke)
  - [ ] 4.3 Verificare che gli smoke test passino
