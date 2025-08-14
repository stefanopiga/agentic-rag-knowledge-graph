import os
import sys
from pathlib import Path
from argparse import ArgumentParser

from dotenv import load_dotenv


def load_environment(env_file: Path) -> None:
    """Load environment variables from the provided .env file without overriding existing process env."""
    if not env_file.exists():
        raise FileNotFoundError(f"Env file not found: {env_file}")
    load_dotenv(env_file.as_posix(), override=False)


def main(argv: list[str]) -> int:
    repo_root = Path(__file__).resolve().parents[1]

    parser = ArgumentParser(description="Run pytest with environment loaded from a .env file", add_help=True)
    parser.add_argument("--env-file", default=str(repo_root / ".env.production"), help="Path to .env file (default: .env.production at repo root)")
    parser.add_argument("pytest_args", nargs="*", help="Arguments passed to pytest after options (e.g., tests/... -q)")

    # Accept unknown args (e.g., -vv) and pass through to pytest
    args, unknown = parser.parse_known_args(argv)

    env_path = Path(args.env_file)
    if not env_path.is_absolute():
        env_path = (repo_root / env_path).resolve()

    load_environment(env_path)

    # Ensure repository root is on sys.path for absolute imports in tests
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    os.environ["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(repo_root), os.environ.get("PYTHONPATH", "")])
    )

    # Compose pytest args: explicit pytest_args + any unknowns; default to health test
    composed_pytest_args = args.pytest_args + unknown
    if not composed_pytest_args:
        composed_pytest_args = ["tests/system/test_api_health_endpoints.py", "-q"]

    try:
        import pytest  # type: ignore
    except Exception as e:
        print(f"pytest non disponibile: {e}")
        return 2

    return pytest.main(composed_pytest_args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
