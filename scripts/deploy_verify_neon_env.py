import os
from dotenv import load_dotenv

load_dotenv()

from deploy_neon_schema import deploy_schema
import scripts.verify_neon_schema as verify


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL non impostato in .env")
    ok = deploy_schema(database_url)
    if not ok:
        raise SystemExit("Deploy schema Neon fallito")
    verifier = verify.NeonSchemaVerifier(database_url)
    verifier.run_verification()

if __name__ == "__main__":
    main()
