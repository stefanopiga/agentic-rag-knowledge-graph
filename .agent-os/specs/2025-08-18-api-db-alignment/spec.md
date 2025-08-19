# Spec Requirements Document

> Spec: API/DB Alignment - Tenant Isolation and Parameter Consistency
> Created: 2025-08-18
> Status: Planning

## Overview

Allineare le interfacce API e database per garantire coerenza nei parametri e supporto completo per l'isolamento tenant nelle operazioni di sessione, messaggi e ricerca semantica. Questo risolve le incongruenze identificate nell'analisi del codice che causano fallimenti runtime e problemi di sicurezza multi-tenant.

## User Stories

### Story 1: Gestione Sessioni Multi-Tenant Consistente

Come sviluppatore del sistema, voglio che le funzioni di gestione sessioni accettino e utilizzino correttamente i parametri tenant_id, così che l'isolamento dei dati tra tenant sia garantito e non si verifichino errori per parametri non riconosciuti.

Le funzioni `create_session`, `get_session` devono supportare `tenant_id` come parametro obbligatorio e utilizzarlo per l'inserimento/filtraggio nei database multi-tenant, mantenendo coerenza tra API layer e DB layer.

### Story 2: Persistenza Messaggi con Tenant Isolation

Come sviluppatore del sistema, voglio che `add_message` e `get_session_messages` supportino correttamente il tenant_id, così che i messaggi siano persistiti e recuperati solo per il tenant appropriato senza perdite di isolamento.

Le funzioni devono accettare tenant_id, inserirlo nella tabella messages e filtrare le query per garantire che ogni tenant veda solo i propri messaggi.

### Story 3: Ricerca Semantica Tenant-Aware

Come sviluppatore del sistema, voglio che le funzioni RAG `match_chunks` e `hybrid_search` supportino l'isolamento tenant, così che le ricerche semantiche restituiscano solo risultati appartenenti al tenant corrente.

Le funzioni devono utilizzare i parametri tenant_id per filtrare chunks e risultati di ricerca, allineandosi con lo schema SQL multi-tenant esistente.

## Spec Scope

1. **Parameter Alignment** - Aggiornare signatures di `create_session`, `get_session`, `add_message`, `get_session_messages` per accettare tenant_id
2. **Database Layer Updates** - Modificare query SQL per utilizzare tenant_id nei filtri WHERE e INSERT
3. **RAG Function Tenant Support** - Implementare tenant_id in `match_chunks` e `hybrid_search` con fallback appropriati
4. **Error Handling** - Aggiungere validazione tenant_id e gestione errori per parametri mancanti
5. **API Integration** - Verificare che tutte le chiamate API passino correttamente tenant_id alle funzioni DB

## Out of Scope

- Modifica dello schema database esistente (usa schema_with_auth.sql corrente)
- Implementazione nuove funzionalità tenant management
- Migrazione dati esistenti tra schema legacy e multi-tenant
- Performance optimization delle query multi-tenant

## Expected Deliverable

1. Tutte le funzioni di sessione e messaggi in agent/db_utils.py accettano e utilizzano tenant_id correttamente
2. Le chiamate API in agent/api.py non generano più errori per parametri non riconosciuti 
3. Le funzioni RAG match_chunks e hybrid_search supportano isolamento tenant tramite stored procedures esistenti