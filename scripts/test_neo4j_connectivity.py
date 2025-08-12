import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(override=True)
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687").strip().strip('"').strip("'")
user = os.getenv("NEO4J_USER", "neo4j").strip().strip('"').strip("'")
password = os.getenv("NEO4J_PASSWORD", "").strip().strip('"').strip("'")

print(f"URI={uri} USER={user} PW_LEN={len(password)}")

driver = GraphDatabase.driver(uri, auth=(user, password))
try:
    with driver.session() as session:
        val = session.run("RETURN 1 AS ok").single()["ok"]
        print(f"OK={val}")
except Exception as e:
    print(f"ERR={e}")
finally:
    driver.close()
