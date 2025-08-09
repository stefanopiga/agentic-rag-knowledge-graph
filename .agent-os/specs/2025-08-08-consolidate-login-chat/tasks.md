# Spec Tasks: Consolidate branches + bring up platform (login + chat)

## Parent Task A: Consolidate branches into main

Links PR:
- #7 docker-modernization → main
- #8 scalability-testing → main
- #9 security-hardening → main

- [x] Create PR docker-modernization → main (PR #7)
- [x] Create PR scalability-testing → main (PR #8)
- [x] Create PR security-hardening → main (PR #9)
- [ ] Ensure rulesets pass (reviews, checks, signed commits) ⚠️ GitHub PR non accessibili da ambiente locale; collegare repository per verifiche
- [ ] Merge in order: docker → scalability → security
- [ ] Tag release v1.0.0-prod-ready

## Parent Task B: Bring up platform (login + chat)

- [ ] Start DB stack (Docker): postgres, neo4j, redis ⚠️ Docker Desktop non in esecuzione su Windows (errore pipe dockerDesktopLinuxEngine)
- [ ] Start backend FastAPI (docker compose app) o `uv run python run_backend.py` ⚠️ Bloccato: Docker non avviato; env `DATABASE_URL` usa schema `postgresql+asyncpg` non supportato da asyncpg; Neo4j/Redis non disponibili
- [ ] Start frontend (pnpm dev) with VITE_API_URL ⚠️ Dipende dall'API disponibile su 8000
- [ ] Verify /health and /health/detailed
- [ ] Verify UI: login page accessible
- [ ] Verify chat screen loads after auth

## Parent Task C: Wire auth endpoints if missing

- [x] Confirm /auth/login backend route exists (stub implementato in `agent/api.py`)
- [x] If missing, implement minimal FastAPI auth: /auth/login, /auth/me (stub di sviluppo)
- [ ] Connect frontend auth store to real backend
- [ ] Seed one test user in Postgres

## Parent Task D: Developer UX

- [ ] Add dev script: `pnpm dev` (runs FE+BE)
- [ ] Add `.env.example` with all required vars
- [ ] Update README quick start
- [x] Compose: usa named volume `app_venv` per evitare shadowing del venv
- [x] Entrypoint: inizializza `/app/.venv` da snapshot se volume vuoto
