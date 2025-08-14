# Spec Requirements Document

> Spec: cloud-shared-test-suite
> Created: 2025-08-14
> Status: Planning

## Overview

Adattare la suite di test per riflettere l'architettura cloud-shared: backend centrale su Neon/Aura con health/monitoring, ingestion centralizzata, frontend puntato al backend. Eliminare assunzioni di servizi locali e rendere i test eseguibili contro ambienti cloud.

## User Stories

### Coach QA – Verifica cloud condiviso

As a QA engineer, I want to run tests contro servizi gestiti (Neon/Aura/backend) così da validare l’ambiente condiviso senza avviare servizi locali.

- Eseguire test DB/Graph verso Neon/Aura
- Health-check backend centrale
- Ingestion centralizzata validata

### Studente – Usa solo browser

As a student, I want the UI to work con backend remoto così da non richiedere setup locale.

- UI raggiungibile e funzionante
- CORS correttamente configurati

## Spec Scope

1. **Test Cloud DB/Graph** - Puntare test a Neon/Aura usando `.env.production`
2. **E2E Pipeline (Cloud)** - Eseguire scenari E2E senza servizi locali, con `ALWAYS_BUILD_GRAPH=1`
3. **Health/Monitoring** - Verifica `/health`, `/health/detailed`, `/status/database`
4. **Frontend Integration** - `VITE_API_URL` e smoke test remoto

## Out of Scope

- Provisioning infrastrutturale (Neon/Aura) fuori dal perimetro della suite
- Performance/load tests avanzati

## Expected Deliverable

1. Test suite eseguibile contro ambiente cloud con 100% pass rate
2. Script runner che carica `.env.production` e non avvia servizi locali
