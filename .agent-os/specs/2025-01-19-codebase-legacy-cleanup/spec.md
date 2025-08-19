# Spec Requirements Document

> Spec: Codebase Legacy Cleanup
> Created: 2025-01-19
> Status: Planning

## Overview

Eliminare codice legacy e incongruenze architetturali identificate per semplificare il codebase FisioRAG, migliorare la manutenibilità e allineare documentazione con implementazione reale. Questa pulizia rimuoverà ~150 files obsoleti (-30% codebase) e risolverà disconnessioni tra frontend/backend.

## User Stories

### Legacy Code Removal

As a **developer**, I want to **remove all legacy Django components and obsolete files**, so that **the codebase reflects only the active FastAPI + React architecture and reduces confusion**.

**Detailed Workflow**: Developer identifies legacy components (Django SaaS app già rimossa, requirements duplicati, Socket.io client senza server, documentazione obsoleta), crea branch di pulizia, rimuove sistematicamente files obsoleti, aggiorna documentazione per riflettere architettura semplificata, testa che sistema continui a funzionare dopo ogni rimozione.

### Architecture Documentation Alignment

As a **new team member**, I want to **read documentation that matches the actual implementation**, so that **I can understand and contribute to the system without confusion about phantom components**.

**Detailed Workflow**: Team member legge documentazione Agent OS, trova architettura descritta allineata con codice reale (FastAPI + React, no Django, WebSocket via SSE only), requirements file unico e consistente, setup instructions che funzionano senza riferimenti a componenti inesistenti.

### Frontend WebSocket Cleanup

As a **frontend developer**, I want to **use only working communication methods with the backend**, so that **real-time features work reliably without fallback to phantom WebSocket implementations**.

**Detailed Workflow**: Developer rimuove Socket.io client code, aggiorna servizi frontend per utilizzare solo SSE streaming disponibile, aggiorna documentazione tecnica, test di integrazione verificano comunicazione frontend-backend funzionante.

## Spec Scope

1. **Legacy Files Removal** - Eliminazione files obsoleti: requirements duplicati, documentazione root ridondante, test per componenti inesistenti
2. **Requirements Consolidation** - Standardizzazione su pyproject.toml + requirements.txt aggiornato, rimozione inconsistenze
3. **WebSocket Cleanup** - Rimozione client Socket.io frontend, documentazione uso esclusivo SSE
4. **Documentation Update** - Aggiornamento .agent-os/product/ per riflettere architettura semplificata FastAPI-only
5. **Test Suite Alignment** - Rimozione test per componenti legacy, mantenimento solo test per codice attivo

## Out of Scope

- Implementazione nuove funzionalità o miglioramenti performance
- Fix di bug non correlati alla pulizia legacy
- Aggiunta WebSocket server Socket.io (fase successiva)
- Creazione docker-compose.yml mancante (spec separata)
- Deploy production o configurazione cloud
- Refactoring code style o ottimizzazioni

## Expected Deliverable

1. **Codebase ridotto del 30%** con ~150 files legacy eliminati e zero riferimenti a componenti Django
2. **Requirements consolidati** con file unico consistente allineato a pyproject.toml dependencies
3. **Frontend comunicazione funzionante** solo via SSE senza client Socket.io obsoleto
4. **Documentazione accurata** in .agent-os/product/ che riflette architettura FastAPI + React reale
5. **Test suite allineata** che testa solo componenti attivi senza failures per codice inesistente
