@echo off
setlocal enableextensions enabledelayedexpansion
pushd %~dp0\..

REM Variabili minime
set EMBEDDINGS_OFFLINE=1
if not defined DATABASE_URL set DATABASE_URL=postgresql://rag_user:rag_password@localhost:5432/rag_db
if not defined NEO4J_USER set NEO4J_USER=neo4j
if not defined NEO4J_PASSWORD set NEO4J_PASSWORD=password

REM 0) Rileva tool Python/UV
where uv >nul 2>&1 && (set RUNPYTEST=uv run pytest -q) || (set RUNPYTEST=python -m pytest -q)
where uv >nul 2>&1 && (set RUNPYTHON=uv run python)   || (set RUNPYTHON=python)

REM 1) Avvio servizi DB
call docker compose up -d postgres neo4j redis || goto :fail

REM 2) Attesa Postgres pronto
echo Attendo Postgres...
:waitpg
docker compose exec -T postgres pg_isready -U rag_user -d postgres 1>nul 2>nul
if errorlevel 1 (timeout /t 2 >nul & goto waitpg)

REM 3) Crea rag_db se mancante
for /f "usebackq tokens=*" %%i in (`cmd /c "docker compose exec -T postgres psql -U rag_user -d postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='rag_db'\""`) do set DBEXISTS=%%i
if not defined DBEXISTS (
  echo Creo database rag_db...
  call docker compose exec -T postgres createdb -U rag_user rag_db || goto :fail
)

REM 4) Applica schema
call docker compose exec -T postgres psql -U rag_user -d rag_db -f /docker-entrypoint-initdb.d/init.sql || goto :fail

REM 5) Verifica estensione vector
call docker compose exec -T postgres psql -U rag_user -d rag_db -c "SELECT COUNT(*) FROM pg_extension WHERE extname='vector';" || goto :fail

REM 6) Verifica Neo4j e Redis
call docker compose exec -T redis redis-cli PING || goto :fail
call docker compose exec -T neo4j cypher-shell -u %NEO4J_USER% -p %NEO4J_PASSWORD% "RETURN 1;" || goto :fail

REM 7) Avvio APP e health (solo se porta 8000 libera)
for /f "usebackq tokens=*" %%i in (`cmd /c "netstat -ano | findstr :8000 | findstr LISTENING"`) do set PORTINUSE=1
if defined PORTINUSE (
  echo Porta 8000 occupata: skip avvio app e health-check
) else (
  call docker compose up -d app || goto :fail
  REM Attendi API
  powershell -Command "Start-Sleep -s 5" >nul 2>&1
  curl -s http://localhost:8000/health || goto :fail
)

REM 8) Test DB
call %RUNPYTEST% tests/comprehensive/test_database_connections.py || goto :fail

REM 9) Ingestione documenti (usa cartella totale se presente)
if exist documents_total (
  call %RUNPYTHON% -m ingestion.ingest --clean --documents-dir documents_total\fisioterapia\master --tenant-slug default || goto :fail
) else if exist documents (
  call uv run python -m ingestion.ingest --clean --documents-dir documents --tenant-slug default || goto :fail
)

REM 10) Test post-ingestione
call %RUNPYTEST% tests/post_ingestion/test_postgres_ingestion.py || goto :fail

echo === E2E CHECK COMPLETATO CON SUCCESSO ===
popd
endlocal
exit /b 0

:fail
echo === ERRORE DURANTE E2E CHECK ===
popd
endlocal
exit /b 1
