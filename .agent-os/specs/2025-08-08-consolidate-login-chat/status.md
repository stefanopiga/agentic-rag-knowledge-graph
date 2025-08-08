# Execution Status (Agent OS)

Date: 2025-08-08

## PR & Branches

- Default branch: `docker-modernization`
- Open PRs:
  - #7 docker-modernization → main (open)
  - #8 scalability-testing → main (open)
  - #9 security-hardening → main (open)

## Compose run

- `docker compose up -d` ha pullato le immagini; build app falliva per `.env.example` mancante
- Aggiunti `.env.example` e `.env` base; policy documentata
- Azione: sostituire `.env` con tutte le variabili di `env.txt` adattando hostnames per Compose
- Fix applicati: volume nominato `app_venv` per preservare il venv del container; init del venv da snapshot d'immagine in `docker-entrypoint.sh`; rimosso `version:` obsoleto in Compose
- Comando app aggiornato a `uv run uvicorn ... --port 8000`

## Runbook

- API health: http://localhost:8000/health
- UI dev: `$env:VITE_API_URL='http://localhost:8000'; pnpm --filter frontend dev` → http://localhost:5173

## Risks / TODO

- Endpoint auth non presenti in `agent/api.py` → login potrebbe fallire
- Se necessario: implementare `/auth/login`, `/auth/me` (JWT) e seed utente
- Verificare ora che `fastapi` sia importabile nel container dopo rebuild
