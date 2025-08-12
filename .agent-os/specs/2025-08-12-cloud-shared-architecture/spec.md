# Spec Requirements Document

> Spec: cloud-shared-architecture
> Created: 2025-08-12
> Status: Planning

## Overview

Rifattorizzazione del progetto per esecuzione “Cloud condivisa”: backend FastAPI centralizzato su VPS/PaaS, database gestiti (Neo4j Aura obbligatorio, Postgres Neon), frontend servito come statico o con `VITE_API_URL` verso il backend. Obiettivo: zero setup client, segreti centralizzati, costo basso.

## User Stories

### Docente – Eroga ambiente condiviso

As a teacher, I want to host a single backend and managed databases so that students can use the tool from the browser without local setup.

- Deploy backend su server
- Configurazione env per Aura/Neon
- CORS/HTTPS configurati
- Ingestion centralizzata

### Studente – Usa solo il browser

As a student, I want to access the app via an URL so that I can study i documenti medici con l’LLM senza installazioni.

- Accesso UI
- Query/Chat funzionanti

## Spec Scope

1. **Configurazione Backend Cloud** - `.env` production, CORS, HTTPS, logging, monitoring
2. **DB Gestiti** - Connessioni Neo4j Aura e Neon; migrazione schema
3. **Ingestion Centralizzata** - Script/CLI per ingest su server
4. **Frontend** - Build static e configurazione `VITE_API_URL`
5. **CI/CD** - Workflow build, deploy, smoke test

## Out of Scope

- Billing avanzato
- SSO/IdP enterprise

## Expected Deliverable

1. Backend deployabile su server con `.env` production; health ok
2. Frontend raggiungibile e integrato; ingestion centralizzata funzionante
