# Spec Requirements Document

> Spec: comprehensive-system-validation
> Created: 2025-08-12
> Status: Planning

## Overview

Validazione end-to-end dell'intero sistema (backend API, Postgres/pgvector, Neo4j/Graphiti, pipeline di ingestione, agent tools, frontend chat) con una batteria di test integrati per garantire che tutte le parti siano funzionanti prima dell'ingestione di un documento di esempio.

## User Stories

### Operatore QA – Verifica sistema completo

As a QA operator, I want to run a comprehensive validation suite so that I can ensure all subsystems (DB, graph, embeddings, ingestion, API, chat UI) are healthy and consistent before data ingestion.

- Avvio dei servizi richiesti (o verifica connessioni locali)
- Esecuzione test di connettività DB/Graph/Cache
- Verifica schema e funzioni RAG in Postgres
- Verifica indice `Episode(tenant_id)` e query in Neo4j
- Verifica strumenti dell’agente (vector/hybrid/graph search)
- Verifica pipeline di ingestione in modalità offline embeddings
- Verifica endpoint API /health e interazione chat

## Spec Scope

1. **Database Validation** - Test connessioni, estensioni pgvector, funzioni RAG, RLS e indici critici
2. **Graph Validation** - Test inizializzazione Graphiti, indice `Episode(tenant_id)`, add/search per tenant
3. **Embeddings/Providers** - Test client embeddings offline e retry/backoff
4. **Ingestion Pipeline** - Test end-to-end da DOCX → chunks → embeddings → Postgres → grafo (opzionale)
5. **API & Agent Tools** - Test strumenti `vector_search`, `hybrid_search`, `search_knowledge_graph`, health endpoints
6. **Frontend Chat (Smoke)** - Verifica minima di avvio e basic UI wiring (condizionale)

## Out of Scope

- Ottimizzazioni di performance oltre ai sanity check
- UI/UX dettagliata o refactoring frontend
- Deploy cloud e IaC

## Expected Deliverable

1. Tutti i test di validazione passano al 100% in locale/CI
2. Ingestion di un documento di esempio completata con chunk e (se abilitato) episodi nel grafo
