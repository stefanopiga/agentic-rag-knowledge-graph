# Spec Tasks

## Tasks

- [x] 1. Implementare match_chunks con tenant isolation
  - [x] 1.1 Scrivere unit tests per match_chunks con tenant_id validation
  - [x] 1.2 Modificare signature match_chunks per accettare tenant_id come primo parametro
  - [x] 1.3 Implementare validazione UUID per tenant_id con error handling
  - [x] 1.4 Convertire embedding format per compatibilità PostgreSQL vector
  - [x] 1.5 Sostituire query legacy con chiamata stored procedure multi-tenant
  - [x] 1.6 Aggiungere logging appropriato per operazioni tenant-aware
  - [x] 1.7 Verificare che tutti i test passino

- [x] 2. Implementare hybrid_search con tenant isolation
  - [x] 2.1 Scrivere unit tests per hybrid_search con tenant_id e parametri completi
  - [x] 2.2 Modificare signature hybrid_search per tenant_id come primo parametro
  - [x] 2.3 Implementare validazione parametri (tenant_id, text_weight range)
  - [x] 2.4 Convertire embedding e preparare parametri per stored procedure
  - [x] 2.5 Sostituire query legacy con stored procedure hybrid_search multi-tenant
  - [x] 2.6 Aggiungere error handling per stored procedure failures
  - [x] 2.7 Verificare che tutti i test passino

- [x] 3. Aggiornare chiamate RAG nel layer API
  - [x] 3.1 Scrivere integration tests per chiamate RAG da agent/api.py
  - [x] 3.2 Identificare tutte le chiamate a match_chunks nel codebase
  - [x] 3.3 Aggiornare chiamate per passare tenant_id correttamente
  - [x] 3.4 Identificare tutte le chiamate a hybrid_search nel codebase
  - [x] 3.5 Aggiornare chiamate hybrid_search per nuova signature
  - [x] 3.6 Testare end-to-end flow con tenant isolation
  - [x] 3.7 Verificare che tutti i test passino

- [x] 4. Implementare fallback e monitoring
  - [x] 4.1 Scrivere tests per scenari stored procedure non disponibili
  - [x] 4.2 Implementare fallback sicuro (empty results + warning)
  - [x] 4.3 Aggiungere metrics per tracking RAG operations per tenant
  - [x] 4.4 Implementare logging dettagliato per debugging tenant isolation
  - [x] 4.5 Verificare che tutti i test passino
