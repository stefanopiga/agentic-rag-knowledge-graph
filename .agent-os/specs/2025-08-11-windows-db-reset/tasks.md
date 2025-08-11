# Spec Tasks: Windows DB Reset

## Tasks

- [x] 1. Verifica prerequisiti
  - [x] 1.1 Verificare Docker Desktop attivo (`docker info`)
  - [x] 1.2 Verificare spazio disco per volumi
  - [x] 1.3 Verificare variabili `.env` per Postgres (se usate)

- [x] 2. Implementare script reset
  - [x] 2.1 Creare `scripts/reset_db_windows.cmd`
  - [x] 2.2 Gestire rimozione volumi e orfani
  - [x] 2.3 Aggiungere wait-loop `pg_isready`
  - [x] 2.4 Aggiungere check estensione `vector`

- [ ] 3. Documentazione
  - [ ] 3.1 Aggiornare `spec.md`/`spec-lite.md`
  - [ ] 3.2 Aggiungere sezione README con istruzioni Windows

- [x] 4. Test
  - [x] 4.1 Eseguire script e verificare bootstrap schema
  - [ ] 4.2 Eseguire `uv run pytest -q tests/comprehensive/test_database_connections.py`
  - [ ] 4.3 Verificare che `match_chunks` funzioni (query di prova)
