#!/usr/bin/env python3
"""
Esegue ingestion caricando un file .env specificato senza sovrascrivere l'env di processo.

Uso:
  uv run python scripts/run_ingestion_with_env.py --env-file .env.production --docs documents --tenant default [--clean]
"""
import os
import sys
from pathlib import Path
from argparse import ArgumentParser

from dotenv import load_dotenv


def load_environment(env_file: Path) -> None:
    if not env_file.exists():
        raise FileNotFoundError(f"Env file not found: {env_file}")
    load_dotenv(env_file.as_posix(), override=False)


def main(argv: list[str]) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = ArgumentParser(description="Run ingestion with environment loaded from a .env file", add_help=True)
    parser.add_argument("--env-file", default=str(repo_root / ".env.production"))
    parser.add_argument("--docs", default="documents")
    parser.add_argument("--tenant", default="default")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args(argv)

    env_path = Path(args.env_file)
    if not env_path.is_absolute():
        env_path = (repo_root / env_path).resolve()

    load_environment(env_path)

    # Forza comportamento produzione richiesto dalla spec
    os.environ.setdefault("APP_ENV", "production")
    os.environ["ALWAYS_BUILD_GRAPH"] = "1"
    os.environ.setdefault("EMBEDDINGS_OFFLINE", "0")

    # Importa ed esegue pipeline
    sys.path.insert(0, str(repo_root))
    from ingestion.ingest import DocumentIngestionPipeline
    from agent.models import IngestionConfig
    import asyncio

    async def run() -> None:
        pipeline = DocumentIngestionPipeline(
            config=IngestionConfig(skip_graph_building=False),
            documents_folder=args.docs,
            clean_before_ingest=args.clean,
        )
        await pipeline.ingest_documents(tenant_slug=args.tenant)
        await pipeline.close()

    asyncio.run(run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


