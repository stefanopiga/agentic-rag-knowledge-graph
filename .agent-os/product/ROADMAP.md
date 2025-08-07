# Roadmap di FisioRAG

## Fase 0: Implementazione Esistente

Le seguenti funzionalità costituiscono il core attuale del sistema:

- [x] **Backend API**: Servizio asincrono basato su FastAPI.
- [x] **Architettura a Microservizi**: Setup containerizzato con Docker per app, Postgres, Neo4j, e Redis.
- [x] **Database a Grafo**: Integrazione con Neo4j per il knowledge graph.
- [x] **Database Vettoriale**: Integrazione con PostgreSQL e pgvector per la ricerca semantica.
- [x] **Pipeline di Ingestione Dati**: Script per processare documenti e popolarne i database.
- [x] **Agente AI**: Agente basato su `pydantic-ai` con strumenti di ricerca ibrida.
- [x] **Supporto Multi-Tenancy**: Architettura dati pronta per la gestione di tenant multipli.

## Fase 1: Verifica e Sviluppo UI ✅ **COMPLETATA** (2025-01-19)

- [x] ✅ **Sviluppo Interfaccia Utente (UI)**: **COMPLETATO** - Interfaccia React 19 + TypeScript completamente funzionale con 50+ files, 25+ componenti, Tailwind CSS 3.4.0, state management Zustand, routing React Router 7.x, production build ottimizzata (278.72 kB).
- [ ] **Verifica delle Connessioni**: Eseguire test completi per assicurare la stabilità e l'affidabilità delle connessioni ai database (Postgres, Neo4j) e alle API esterne (OpenAI).
- [ ] **Validazione del Core System**: Testare end-to-end la pipeline di ingestione e la qualità delle risposte fornite dall'agente RAG.
- [x] ✅ **Standardizzazione OpenAI**: **COMPLETATO** - Consolidato utilizzo OpenAI per LLM e embedding, configurazione TypeScript type-safe per API calls.
- [ ] **Documentazione Utente**: Creare una guida per l'utente finale su come utilizzare al meglio l'applicazione.
- [ ] **Aumento Copertura Test**: Scrivere test di unità e di integrazione per i moduli `agent` e `ingestion` al fine di raggiungere una copertura di almeno l'80%.

## Fase 2: Integration & Deployment 🚀 **IN CORSO**

- [ ] **Frontend-Backend Integration**: Connessione completa tra interfaccia React e API FastAPI
- [ ] **Authentication Flow End-to-End**: Sistema login completo con JWT/session management
- [ ] **WebSocket Real-time Testing**: Chat interface con comunicazione bidirezionale
- [ ] **Document Upload Integration**: Interface caricamento e processamento documenti
- [ ] **Error Handling & Monitoring**: Sistema robusto gestione errori e monitoraggio
- [ ] **Performance Optimization**: Caching, lazy loading, ottimizzazioni bundle
