@echo off
setlocal

cd /d "%~dp0\.."
set PYTHONIOENCODING=utf-8

if not exist ".env.production" (
  echo [WARN] .env.production non trovato nel root del repository. Il runner usera' i valori di ambiente correnti.
)

REM Forza modalita' cloud-shared
set APP_ENV=production
set ALWAYS_BUILD_GRAPH=1

python -X utf8 scripts\run_ingestion_with_env.py --env-file .\.env.production %*
set EXITCODE=%ERRORLEVEL%

endlocal & exit /b %EXITCODE%
