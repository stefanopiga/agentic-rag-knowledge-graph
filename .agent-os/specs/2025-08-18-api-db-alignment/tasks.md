# Spec Tasks

## Tasks

- [x] 1. Aggiornare funzioni gestione sessioni per tenant support
  - [x] 1.1 Scrivere unit tests per create_session con tenant_id
  - [x] 1.2 Modificare signature create_session per accettare tenant_id come primo parametro
  - [x] 1.3 Aggiornare SQL INSERT in create_session per includere tenant_id
  - [x] 1.4 Modificare signature get_session per accettare tenant_id
  - [x] 1.5 Aggiungere WHERE tenant_id filter in get_session query
  - [x] 1.6 Aggiornare chiamate API per passare tenant_id a funzioni sessioni
  - [x] 1.7 Verificare che tutti i test passino

- [x] 2. Implementare tenant isolation per gestione messaggi
  - [x] 2.1 Scrivere unit tests per add_message e get_session_messages con tenant_id
  - [x] 2.2 Modificare signature add_message per includere tenant_id parameter
  - [x] 2.3 Aggiornare INSERT query in add_message per tenant_id
  - [x] 2.4 Modificare signature get_session_messages per tenant_id support
  - [x] 2.5 Aggiungere JOIN con sessions table per tenant filtering in get_session_messages
  - [x] 2.6 Aggiornare tutte le chiamate API che invocano add_message e get_session_messages
  - [x] 2.7 Verificare che tutti i test passino

- [x] 3. Allineare funzioni RAG con schema multi-tenant
  - [x] 3.1 Scrivere integration tests per match_chunks e hybrid_search con tenant_id
  - [x] 3.2 Modificare signature match_chunks per accettare tenant_id come primo parametro
  - [x] 3.3 Aggiornare chiamata stored procedure match_chunks con p_tenant_id
  - [x] 3.4 Modificare signature hybrid_search per tenant_id support
  - [x] 3.5 Aggiornare chiamata stored procedure hybrid_search con p_tenant_id
  - [x] 3.6 Aggiornare chiamate RAG in agent/api.py per passare tenant_id
  - [x] 3.7 Verificare che tutti i test passino

- [x] 4. Implementare error handling e validazione
  - [x] 4.1 Scrivere tests per error cases (tenant_id malformato, mancante)
  - [x] 4.2 Aggiungere validazione UUID per tenant_id in tutte le funzioni
  - [x] 4.3 Implementare fallback a DEV_TENANT_UUID per ambiente development
  - [x] 4.4 Aggiungere logging per operazioni tenant-aware
  - [x] 4.5 Verificare che tutti i test passino
