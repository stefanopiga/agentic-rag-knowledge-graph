# Product Roadmap

## Phase 1: Core MVP

**Goal:** RAG multi-tenant con pipeline ingestion e chat affidabile
**Success Criteria:** Health endpoints verdi, ingestion base ok, chat streaming stabile

### Features
- [ ] Deploy staging backend + API_BASE_URL definito `[M]`
- [ ] Seed dataset minimo per E2E cloud `[S]`
- [ ] Test comprehensive verdi in CI `[M]`

### Dependencies
- Secrets cloud, Neon/Neo4j credenziali

## Phase 2: Differenziatori

**Goal:** Grafo conoscenza e analytics base
**Success Criteria:** Query relazioni/tempi; report basici

### Features
- [ ] Relazioni timeline su Neo4j `[M]`
- [ ] Endpoint analytics chat `[S]`
- [ ] Export sessione (pdf/docx/txt) `[S]`

### Dependencies
- Ingestion arricchita

## Phase 3: Scalabilità e Polishing

**Goal:** Osservabilità e hardening
**Success Criteria:** Alerting basico, policy sicurezza

### Features
- [ ] OpenTelemetry + exporter `[M]`
- [ ] Rate limiting e CORS tightening `[S]`
- [ ] Hardening auth/sessioni `[M]`

### Dependencies
- Hosting prod
