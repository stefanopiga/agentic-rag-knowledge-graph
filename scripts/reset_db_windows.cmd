@echo off
setlocal enableextensions enabledelayedexpansion

rem Spostati nella root del repository (cartella superiore rispetto a scripts)
pushd %~dp0\..

rem Arresta e rimuovi container orfani
docker compose down --remove-orphans

rem Rimuovi volumi dati (ignorando errori se non esistono)
for %%V in (postgres_data neo4j_data redis_data) do docker volume rm agentic-rag-knowledge-graph_%%V 2>nul

rem Ricrea servizi database
docker compose up -d --build postgres neo4j redis

rem Attendi che Postgres sia pronto
echo Attendo Postgres...
:waitpg
docker compose exec -T postgres pg_isready -U rag_user -d postgres 1>nul 2>nul
if errorlevel 1 (timeout /t 2 >nul & goto waitpg)

echo Verifico estensione pgvector...
docker compose exec -T postgres psql -U rag_user -d rag_db -c "SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector';"

echo Reset completato.

popd
endlocal
