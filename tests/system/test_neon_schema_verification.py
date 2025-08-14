"""
Test di integrazione controllata per `scripts/verify_neon_schema.py`.

Esegue il verificatore contro il DATABASE_URL corrente (locale o Neon) e
valida che i test critici passino senza errori bloccanti.
"""

import os
import json
import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_verify_neon_schema_runs_and_reports_success(tmp_path):
    # Richiede un DATABASE_URL valido nell'ambiente di test
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL non impostato per la verifica Neon")

    # Esegui lo script in-process importando la classe per evitare sottoprocessi
    from scripts.verify_neon_schema import NeonSchemaVerifier

    verifier = NeonSchemaVerifier(db_url)
    results = verifier.run_verification()

    # Salva un file di output temporaneo per coerenza con lo script
    out_file = tmp_path / f"neon_verification_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_file.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

    # Assert di base: struttura presente e almeno un test eseguito
    assert isinstance(results, dict)
    assert "summary" in results and "tests" in results
    assert results["summary"]["total_tests"] > 0

    # Requisiti minimi: extensions e funzioni chiave presenti
    assert results["tests"].get("extensions", {}).get("passed", False) is True
    assert results["tests"].get("functions", {}).get("passed", False) is True

    # Gli indici critici e RLS dovrebbero essere almeno valutati (pass/fail/warning consentiti)
    assert "indexes" in results["tests"]
    assert "rls_enabled" in results["tests"]

