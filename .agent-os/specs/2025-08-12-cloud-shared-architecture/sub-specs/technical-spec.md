# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-12-cloud-shared-architecture/spec.md

## Technical Requirements

- Backend Cloud
  - `.env` production (solo variabili cloud): `DATABASE_URL` (Neon, sslmode=require), `NEO4J_URI/USER/PASSWORD` (Aura), `EMBEDDINGS_OFFLINE=1`, `VECTOR_DIMENSION=1536`, `ENABLE_METRICS=true`
  - CORS aperto ai domini frontend; HTTPS dietro reverse proxy (Caddy/Nginx) o PaaS
  - Health endpoints `/health`, `/health/detailed`, `/status/database`
- DB Gestiti
  - Script migrazione: `scripts/verify_neon_schema.py` contro Neon
  - Neo4j Aura: indice `Episode(tenant_id)`, search filtrata per tenant
- Ingestion Centralizzata
  - CLI/server‐side: `uv run python ingestion/ingest.py --documents-dir <path>`
  - Flag/config per `skip_graph_building=false` e gestione errori
- Frontend
  - Build statica con `pnpm build`; `VITE_API_URL` verso backend
  - Abilitare CORS in backend per dominio UI
- CI/CD
  - Workflow build (UV cache, PNPM), push artefatti, step deploy

## External Dependencies (Conditional)

- Nessuna nuova dipendenza obbligatoria; opzionali: reverse proxy/container runtime sul server
