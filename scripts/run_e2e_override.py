import os
import sys
from dotenv import load_dotenv

# Carica .env.production con override esplicito
load_dotenv(".env.production", override=True)

# Esegui pytest con gli argomenti passati o default al test E2E grafico
try:
	import pytest  # type: ignore
except Exception as e:
	print(f"pytest non disponibile: {e}")
	sys.exit(2)

args = sys.argv[1:] or ["tests/system/test_end_to_end_graph_pipeline.py", "-q"]
sys.exit(pytest.main(args))