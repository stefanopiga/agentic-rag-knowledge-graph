#!/usr/bin/env python3
"""
Helper per eseguire la verifica Neon caricando le variabili da env.txt
senza esporre i segreti in riga di comando.

Uso:
  uv run python scripts/run_verify_neon_env.py
"""
import os
import sys
import subprocess
from pathlib import Path

try:
    from dotenv import dotenv_values  # type: ignore
except Exception:
    dotenv_values = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "env.txt"
VERIFY_SCRIPT = ROOT / "scripts" / "verify_neon_schema.py"


def main() -> int:
    # Carica DATABASE_URL da env.txt se presente
    database_url = os.environ.get("DATABASE_URL")
    if not database_url and dotenv_values and ENV_FILE.exists():
        vals = dotenv_values(str(ENV_FILE))
        database_url = vals.get("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL non disponibile (env.txt o variabile d'ambiente)")
        return 1

    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    # Forza UTF-8 per evitare errori emoji su Windows/cp1252
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    # Esegue lo script ufficiale di verifica con l'env valorizzato
    proc = subprocess.run([sys.executable, "-X", "utf8", str(VERIFY_SCRIPT)], env=env)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
