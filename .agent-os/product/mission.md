# Product Mission

## Pitch

FisioRAG è una piattaforma RAG multi‑tenant per il dominio clinico/fisioterapico che aiuta cliniche e terapisti a recuperare conoscenza affidabile dai propri documenti fornendo risposte con citazioni, grafo conoscenza e UX chat.

## Users

### Primary Customers

- Cliniche di fisioterapia: supporto decisionale rapido su protocolli e contenuti clinici
- Terapisti e staff clinico: consultazione puntuale di linee guida e casi

### User Personas

**Terapista** (25-55 anni)
- **Role:** Fisioterapista in clinica multi-sede
- **Context:** Consulto al letto o in ambulatorio, poco tempo, dispositivi eterogenei
- **Pain Points:** ricercabilità scarsa, fonti frammentate
- **Goals:** risposte affidabili con fonti, velocità

**Responsabile di struttura** (30-60 anni)
- **Role:** Coordinatore clinico/operativo
- **Context:** standardizzazione protocolli, audit qualità
- **Pain Points:** governance contenuti, variabilità
- **Goals:** controllo versioni, multi-tenant isolato

## The Problem

### Scarsa reperibilità di conoscenza clinica interna
Documenti disomogenei e repository multipli riducono la reperibilità (tempo perso, errori).
**Our Solution:** ingestion strutturata + RAG con citazioni.

### Mancanza di isolamento per tenant
Il rischio di fuga dati tra strutture richiede isolamenti chiari.
**Our Solution:** multi‑tenancy su grafo con indice `Episode(tenant_id)` e policy lato API.

### Affidabilità e verificabilità
Le risposte LLM necessitano di fonti e tracciabilità.
**Our Solution:** citazioni sorgente e pipeline E2E verificata in CI.

## Differentiators

### Grafo conoscenza + RAG
Oltre al solo RAG, forniamo relazione tra fatti e timeline.

### CI cloud per qualità
Workflow GitHub Actions con smoke test frontend e suite health/system.

## Key Features

### Core Features
- **Ingestion documentale multi‑tenant:** indicizzazione con metadati e isolamento
- **Chat RAG con citazioni:** UX chat con streaming e sorgenti
- **Grafo conoscenza (Neo4j):** ricerca per fatti/relazioni/temporalità

### Operatività
- **Health & Observability:** endpoint, script verifica schema Neon
- **CI Cloud:** workflow su main e smoke test API
- **Auth & Sessions:** gestione token, sessioni chat
