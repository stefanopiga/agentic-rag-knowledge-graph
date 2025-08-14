#!/usr/bin/env python3
"""
Helper per eseguire il deploy schema su Neon caricando DATABASE_URL da env.txt.

Uso:
  uv run python scripts/run_deploy_neon_env.py
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
DEPLOY_SCRIPT = ROOT / "deploy_neon_schema.py"


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url and dotenv_values and ENV_FILE.exists():
        vals = dotenv_values(str(ENV_FILE))
        database_url = vals.get("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL non disponibile (env.txt o variabile d'ambiente)")
        return 1

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    # Passa DATABASE_URL come argomento (richiesto dallo script)
    proc = subprocess.run([sys.executable, "-X", "utf8", str(DEPLOY_SCRIPT), database_url], env=env)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
