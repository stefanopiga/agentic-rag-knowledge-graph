# Spec Tasks

## Tasks

- [x] 1. Unifica codice su main
  - [x] 1.1 Checkout main
  - [x] 1.2 Merge senza storia comune
  - [x] 1.3 Push su remoto

- [x] 2. Esegui workflow Cloud Shared Test Suite
  - [x] 2.1 Dispatch workflow su main
  - [x] 2.2 Leggi stato ultimo run
  - [x] 2.3 Ispeziona log del run

- [x] 3. Configura secrets GitHub
  - [x] 3.1 Imposta `DATABASE_URL`
  - [x] 3.2 Imposta `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
  - [x] 3.3 Imposta `LLM_API_KEY`, `EMBEDDING_API_KEY`
  - [x] 3.4 Imposta `API_BASE_URL`

- [ ] 4. Deploy Staging Backend (Railway)
  - [x] 4.1 Aggiungi `Procfile`, `runtime.txt`, `railway.toml`
  - [ ] 4.2 Configura secrets in Railway (DATABASE_URL, NEO4J_*, LLM_*, EMBEDDING_*)
  - [ ] 4.3 Imposta `CORS_ALLOWED_ORIGINS` coerente con frontend staging
  - [ ] 4.4 Verifica `/health` e `/health/detailed`

- [ ] 5. Frontend Staging (Vercel)
  - [ ] 5.1 Configura progetto Vercel su repo `frontend/`
  - [ ] 5.2 Imposta env `VITE_API_BASE_URL` e `VITE_WS_URL` verso staging backend
  - [ ] 5.3 Esegui smoke test contro staging

- [ ] 6. CI: aggiungi job `staging-smoke`
  - [ ] 6.1 Step Node per `frontend/scripts/smoke_test.mjs` con base staging
  - [ ] 6.2 Step Python per ping `/health` backend staging

## Command Reference

```bash
# 4) Deploy Railway
railway up  # oppure deploy GitHub integration

# 6) CI smoke run (node)
node frontend/scripts/smoke_test.mjs
```