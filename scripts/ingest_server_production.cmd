@echo off
REM Centralized ingestion runner for production server (loads .env.production)
setlocal ENABLEDELAYEDEXPANSION

SET DOCS_DIR=%~1
IF "%DOCS_DIR%"=="" SET DOCS_DIR=documents

SET TENANT=%~2
IF "%TENANT%"=="" SET TENANT=default

echo Ingestion avviata. DOCS_DIR=%DOCS_DIR% TENANT=%TENANT%

uv run python scripts\run_ingestion_with_env.py --env-file .env.production --docs "%DOCS_DIR%" --tenant "%TENANT%"

ENDLOCAL

