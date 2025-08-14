# Local Runbook (Windows) - Neon + Neo4j (Docker) + Redis (Docker)

## Env (.env)
- DATABASE_URL=postgresql://<user>:<password>@<neon-host>/<db>?sslmode=require&channel_binding=require
- NEO4J_URI=bolt://localhost:7687
- NEO4J_USER=neo4j
- NEO4J_PASSWORD=<password>
- REDIS_URL=redis://localhost:6379/0

## Avvio servizi
- Docker: `docker compose up -d neo4j redis`

## Backend
- Avvio: `uv run python run_backend.py`
- Health:
  - `powershell -NoProfile -Command "(iwr -UseBasicParsing http://localhost:8000/health).Content"`
  - `powershell -NoProfile -Command "(iwr -UseBasicParsing http://localhost:8000/health/detailed).Content"`
- Auth stub:
  - `powershell -NoProfile -Command "$b = @{ email='test@example.com'; password='x' } | ConvertTo-Json; irm -Method Post -ContentType 'application/json' -Body $b -Uri http://localhost:8000/auth/login | ConvertTo-Json -Depth 6"`

## Frontend
- Avvio: `powershell -NoProfile -Command "$env:VITE_API_URL='http://localhost:8000'; pnpm --filter ./frontend dev"`
- UI: http://localhost:3000/

## Note
- Schema DSN per Neon: `postgresql://` (non `postgresql+asyncpg`)
- Se il backend gira sull’host, usare `localhost` per Neo4j e Redis (non i nomi di servizio Docker)
