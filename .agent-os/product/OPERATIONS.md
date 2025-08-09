# FisioRAG Operations (Agent OS)

## Branch model & protection

- Default branch attuale: `docker-modernization` (GitHub settings)
- Ruleset attivo (branch protetti):
  - Target: `Default`, `security-hardening`, `scalability-testing`, `docker-modernization`, `production/*`, `release/*`, `hotfix/*`, `feature/security-*`
  - Regole:
    - Require pull request before merging (≥1 approval)
    - Require status checks to pass (CI/CodeQL); require branches up to date
    - Require signed commits
    - Require linear history
    - Block force pushes
    - Restrict deletions
    - Require code scanning results (CodeQL High+)
  - Bypass: Repository administrators

## Pull Requests aperte

- #5 Merge `scalability-testing` → `docker-modernization`
- #6 Merge `security-hardening` → `docker-modernization`
- Nota: i tentativi verso `main` hanno fallito perché il default è `docker-modernization`. Dopo il merge dei due PR, aprire PR finale `docker-modernization` → `main` (o impostare `main` come default).

## Env policy (.env vs docker)

- Template: `.env.example` (senza segreti) è copiato nel container per sbloccare build.
- Esecuzione locale/docker: usare `.env` con TUTTE le variabili richieste.
- Mapping hostnames per Compose:
  - `DATABASE_URL=postgresql+asyncpg://rag_user:rag_password@postgres:5432/rag_db`
  - `NEO4J_URI=bolt://neo4j:7687`
  - `REDIS_URL=redis://redis:6379/0`
- Per esecuzione nativa (senza docker) si possono usare i valori `localhost`.

## Runbook: avvio piattaforma (login + chat)

1. Avvia stack DB + backend (Compose):

```powershell
docker compose up -d
# Windows: usa Invoke-WebRequest (iwr) al posto di curl/cat
powershell -Command "iwr -UseBasicParsing http://localhost:8000/health"
powershell -Command "iwr -UseBasicParsing http://localhost:8000/health/detailed"
```

2. Avvia UI (vite) puntata all'API:

```powershell
$env:VITE_API_URL='http://localhost:8000'
pnpm --filter frontend dev
# apri http://localhost:5173
```

3. Smoke test:

- UI: pagina login raggiungibile
- Chat: schermata caricata dopo auth

## Next steps

- Review/merge PR #5 e #6; poi PR finale `docker-modernization` → `main`
- Se login fallisce: aggiungere endpoints minimi `/auth/login`, `/auth/me` in `agent/api.py` e seed utente test in Postgres
- Aggiornare `README.md` quick start con comandi definitivi

## Troubleshooting Windows

- Per seguire i log senza `cat`:
  - `docker compose logs -f app`
- Per eseguire comandi nella app:
  - `docker compose exec app sh -lc "python -c 'import fastapi,uvicorn; print(\"deps_ok\")'"`
- Se `ModuleNotFoundError: fastapi`:
  - Assicurarsi di ricreare il container dopo queste modifiche:
    - `docker compose build --no-cache app`
    - `docker compose up -d --force-recreate app`
