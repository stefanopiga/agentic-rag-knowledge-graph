# Implementation Notes

- Aggiunto runner Windows `scripts/run_cloud_tests.cmd` per esecuzione test con `.env.production` caricata da `scripts/run_tests_with_env.py`.
- Aggiunti test remoti per health endpoints: `tests/system/test_remote_health_endpoints.py` con skip condizionale su `API_BASE_URL`.
- Verifica Neon via test esistente `tests/system/test_neon_schema_verification.py` (richiede `DATABASE_URL`).
- Esecuzione locale bloccata su questa macchina per assenza `python`/`pytest` nel PATH; usare ambiente con Python installato o venv.
