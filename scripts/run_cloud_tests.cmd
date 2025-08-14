@echo off
setlocal

REM Sposta working directory alla root del repository
cd /d "%~dp0\.."

REM Forza UTF-8 per output coerente su Windows
set PYTHONIOENCODING=utf-8

if not exist ".env.production" (
  echo [WARN] .env.production non trovato nel root del repository. Il runner potrebbe fallire nel caricamento delle variabili.
)

python -X utf8 scripts\run_tests_with_env.py --env-file .\.env.production %*
set EXITCODE=%ERRORLEVEL%

endlocal & exit /b %EXITCODE%
