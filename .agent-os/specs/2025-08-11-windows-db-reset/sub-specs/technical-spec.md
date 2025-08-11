# Technical Specification

Riferimento: `.agent-os/specs/2025-08-11-windows-db-reset/spec.md`

## Requisiti Tecnici

- Docker Desktop installato e in esecuzione.
- Uso di `docker-compose.yml` del progetto; Postgres monta `sql/schema_with_auth.sql` su `docker-entrypoint-initdb.d` (inizializza al primo bootstrap volume).
- Volumi: `postgres_data`, `neo4j_data`, `redis_data` definiti nello `docker-compose.yml`.

## Sequenza Comandi (Windows cmd)

1) Arresto e rimozione container orfani

```
cd /d C:\Users\user\Desktop\D\_MCPserver\mcp\grafo+LLM\agentic-rag-knowledge-graph
docker compose down --remove-orphans
```

2) Rimozione volumi dati (reset definitivo)

```
docker volume rm agentic-rag-knowledge-graph_postgres_data agentic-rag-knowledge-graph_neo4j_data agentic-rag-knowledge-graph_redis_data 2>nul
```

3) Ricostruzione e riavvio solo database

```
docker compose up -d --build postgres neo4j redis
```

4) Verifica avvio Postgres e estensione vector

```
docker compose exec -T postgres psql -U rag_user -d rag_db -c "SELECT 1;"
docker compose exec -T postgres psql -U rag_user -d rag_db -c "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';"
```

5) Avvio applicazione (opzionale)

```
docker compose up -d app
```

## Script Batch

Percorso: `scripts\\reset_db_windows.cmd`

Contenuto minimale:

```
@echo off
setlocal enableextensions enabledelayedexpansion
pushd %~dp0\..

docker compose down --remove-orphans
for %%V in (postgres_data neo4j_data redis_data) do docker volume rm agentic-rag-knowledge-graph_%%V 2>nul

docker compose up -d --build postgres neo4j redis

echo Waiting for Postgres...
:waitpg
for /f "tokens=*" %%i in ('docker compose exec -T postgres pg_isready -U rag_user -d rag_db ^| find /i "accepting"') do set READY=1
if not defined READY (timeout /t 2 >nul & goto waitpg)

Docker compose exec -T postgres psql -U rag_user -d rag_db -c "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';"

echo Done.
popd
endlocal
```

Note: la prima inizializzazione schema avviene automaticamente grazie al bind `./sql/schema_with_auth.sql:/docker-entrypoint-initdb.d/init.sql` quando il volume `postgres_data` è nuovo.
