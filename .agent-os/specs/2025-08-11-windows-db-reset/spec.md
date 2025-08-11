# Spec Requirements Document

> Spec: windows-db-reset
> Created: 2025-08-11
> Status: Planning

## Overview

Definire comandi da riga di comando Windows (cmd) per pulizia/ricreazione dei database del progetto (PostgreSQL + pgvector, Neo4j, Redis) usando Docker Compose, assicurando reset idempotente e inizializzazione schema.

## User Stories

### Reset ambiente DB

Come sviluppatore su Windows, voglio un insieme di comandi da terminale cmd per fermare i servizi, cancellare i volumi, ricreare i container e inizializzare lo schema SQL, così da ottenere un ambiente pulito in modo rapido e ripetibile.

[Workflow] Stop servizi → prune volumi → up database → inizializzazione schema → healthcheck → pronto all'ingestione.

## Spec Scope

1. **Comandi Docker Compose** - arresto e ri-creazione servizi `postgres`, `neo4j`, `redis` con rimozione volumi.
2. **Inizializzazione Schema** - applicazione di `sql/schema_with_auth.sql` al primo avvio Postgres (mount già presente in docker-compose.yml).
3. **Verifiche** - healthcheck connessioni e presenza estensioni `vector`.
4. **Script batch opzionale** - file `.cmd` per automatizzare.

## Out of Scope

- Dati applicativi Django e migrazioni ORM.
- Ingestione documenti.

## Expected Deliverable

1. Sequenza comandi Windows cmd verificata per full reset DB.
2. Script `scripts\reset_db_windows.cmd` creato e funzionante.
3. Documentazione breve in `spec-lite.md` e dettagli tecnici in `technical-spec.md`.
4. Config Compose aggiornata per variabili runtime (`OPENAI_API_KEY`, `NEO4J_URI`, `REDIS_URL`).
