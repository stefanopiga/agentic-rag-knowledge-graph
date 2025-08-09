# Agent OS – Stato Corrente (2025-08-09)

## Stack runtime locale (Windows)
- Backend: `uv run python run_backend.py` → http://localhost:8000
- Frontend: `$env:VITE_API_URL='http://localhost:8000'; pnpm --filter ./frontend dev` → http://localhost:3000
- DB: Neon Postgres (`DATABASE_URL=postgresql://…neon.tech…`), Neo4j Docker (`bolt://localhost:7687`), Redis Docker (`redis://localhost:6379/0`)

## Endpoints chiave
- Health: `GET /health`, `GET /health/detailed`
- Auth (stub): `POST /auth/login`, `GET /auth/me`
- Chat: `POST /chat`, `POST /chat/stream` (SSE)

## Comandi rapidi (PowerShell)
- Health: `powershell -NoProfile -Command "(iwr -UseBasicParsing http://localhost:8000/health).Content"`
- Login: `powershell -NoProfile -Command "$b = @{ email='test@example.com'; password='x' } | ConvertTo-Json; irm -Method Post -ContentType 'application/json' -Body $b -Uri http://localhost:8000/auth/login | ConvertTo-Json -Depth 6"`
- Apri UI: `start http://localhost:3000/`
- Apri Swagger: `start http://localhost:8000/docs`

## Stato funzionale
- Backend: healthy (Neon+Neo4j+Redis OK)
- Frontend: login→chat UI carica; invio messaggi da adeguare a `/chat` o `/chat/stream` (niente WS)

## Task aperti
- FE: disabilitare WebSocket e usare SSE/HTTP in `services/chat.ts` + `chatStore.ts`
- Aggiornare `tasks.md` al completamento FE chat
