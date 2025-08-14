#!/usr/bin/env python3
"""
Setup Neo4j Aura: verifica connettività e crea indice Episode(tenant_id).
Usa le variabili d'ambiente:
  - NEO4J_URI (es. neo4j+s://<id>.databases.neo4j.io)
  - NEO4J_USER
  - NEO4J_PASSWORD

Esecuzione:
  uv run python scripts/prepare_neo4j_aura.py
"""
import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase


def get_env(name: str, default: str | None = None) -> str:
    val = os.getenv(name, default)
    if val is None or not str(val).strip():
        raise RuntimeError(f"Missing required env var: {name}")
    return str(val).strip().strip('"').strip("'")


def main() -> int:
    load_dotenv(override=True)

    uri = get_env("NEO4J_URI", "")
    user = get_env("NEO4J_USER", "neo4j")
    password = get_env("NEO4J_PASSWORD", "")

    print(f"Connecting to Neo4j: uri={uri}")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        # Verifica connettività (TLS gestito da neo4j+s)
        driver.verify_connectivity()
        print("Connectivity: OK")

        # Crea indice per tenant se non esiste
        create_index_cypher = (
            "CREATE INDEX episode_tenant_id_index IF NOT EXISTS "
            "FOR (n:Episode) ON (n.tenant_id)"
        )
        with driver.session() as session:
            session.run(create_index_cypher).consume()
            print("Index ensured: episode_tenant_id_index ON :Episode(tenant_id)")

        # Verifica presenza indice
        check_query = (
            "SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties "
            "WHERE name = 'episode_tenant_id_index' RETURN name, labelsOrTypes, properties"
        )
        with driver.session() as session:
            rec = session.run(check_query).single()
            if rec:
                print(
                    "Index present:",
                    rec["name"],
                    rec["labelsOrTypes"],
                    rec["properties"],
                )
            else:
                print("Warning: index not visible via SHOW INDEXES")

        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    finally:
        driver.close()


if __name__ == "__main__":
    sys.exit(main())
