# Spec Requirements Document

> Spec: RAG Functions Tenant Isolation Implementation
> Created: 2025-08-18
> Status: Planning

## Overview

Implementare isolamento tenant completo nelle funzioni RAG semantic search sostituendo le chiamate fallback senza tenant con versioni tenant-aware che utilizzano le stored procedures multi-tenant esistenti. Questo garantisce che ogni tenant acceda solo ai propri chunks e risultati di ricerca, eliminando potenziali data leaks tra tenant.

## User Stories

### Story 1: Semantic Search Tenant-Isolated

Come sviluppatore del sistema, voglio che `match_chunks` utilizzi sempre l'isolamento tenant chiamando la stored procedure `match_chunks(p_tenant_id, query_embedding, match_count)`, così che ogni tenant riceva solo risultati dei propri documenti senza accesso a chunks di altri tenant.

La funzione deve validare tenant_id, convertire embedding nel formato corretto e chiamare la stored procedure multi-tenant invece del fallback legacy senza tenant.

### Story 2: Hybrid Search Multi-Tenant Compliant

Come sviluppatore del sistema, voglio che `hybrid_search` supporti completamente l'isolamento tenant utilizzando `hybrid_search(p_tenant_id, query_embedding, query_text, match_count, text_weight)`, così che i risultati ibridi (semantic + text) siano limitati al perimetro del tenant corrente.

La funzione deve accettare tenant_id come parametro obbligatorio e utilizzarlo nella chiamata alla stored procedure, eliminando il fallback legacy che cerca in tutti i tenant.

### Story 3: Error Handling Consistente per RAG

Come sviluppatore del sistema, voglio che le funzioni RAG gestiscano correttamente errori di tenant_id invalido e stored procedure failures, così che il sistema fornisca messaggi di errore chiari e non esponga informazioni di altri tenant in caso di fallimento.

Le funzioni devono validare UUID tenant_id, gestire stored procedure errors e fornire fallback appropriati senza compromettere l'isolamento.

## Spec Scope

1. **Match Chunks Tenant Implementation** - Sostituire chiamata legacy con stored procedure multi-tenant match_chunks(p_tenant_id, query_embedding, match_count)
2. **Hybrid Search Tenant Implementation** - Implementare chiamata stored procedure multi-tenant hybrid_search con tutti i parametri richiesti
3. **Parameter Validation** - Aggiungere validazione UUID per tenant_id e validazione embedding format
4. **Error Handling** - Implementare gestione errori per stored procedure failures e parametri invalidi
5. **Fallback Strategy** - Definire comportamento appropriato quando stored procedures non sono disponibili

## Out of Scope

- Modifica delle stored procedures SQL esistenti (usare quelle in schema_with_auth.sql)
- Implementazione nuove strategie di search o ranking algorithms
- Performance optimization delle stored procedures
- Migrazione dati esistenti tra versioni legacy e multi-tenant
- Caching layer per risultati RAG

## Expected Deliverable

1. Funzione `match_chunks` in agent/db_utils.py utilizza stored procedure multi-tenant con tenant_id obbligatorio
2. Funzione `hybrid_search` implementa isolamento tenant completo tramite stored procedure appropriata
3. Entrambe le funzioni gestiscono correttamente validation errors e stored procedure failures senza compromettere sicurezza tenant