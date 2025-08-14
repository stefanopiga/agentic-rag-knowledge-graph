@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Ensure production-like settings for validation
IF NOT DEFINED APP_ENV SET APP_ENV=production
SET ALWAYS_BUILD_GRAPH=1
IF NOT DEFINED EMBEDDINGS_OFFLINE SET EMBEDDINGS_OFFLINE=0

SET DOCS_DIR=documents\_samples
SET TENANT=default

echo Ingestion sample starting... DOCS_DIR=%DOCS_DIR% TENANT=%TENANT%
uv run python -m ingestion.ingest --documents-dir "%DOCS_DIR%" --tenant-slug "%TENANT%"

echo Verifica Postgres/Neo4j...
uv run python scripts\verify_ingestion_status.py

ENDLOCAL

