# Spec Tasks

## Tasks

- [x] 1. Implementare real database connection monitoring
  - [x] 1.1 Scrivere unit tests per update_connection_metrics con mock connection pools
  - [x] 1.2 Identificare e accedere a PostgreSQL asyncpg connection pool existente
  - [x] 1.3 Interrogare Neo4j driver per active session/connection count
  - [x] 1.4 Accedere a Redis connection pool statistics se disponibile
  - [x] 1.5 Sostituire valori fissi con connection counts reali
  - [x] 1.6 Aggiungere error handling per connection pools non disponibili
  - [x] 1.7 Verificare che tutti i test passino

- [ ] 2. Implementare system metrics collection
  - [ ] 2.1 Scrivere unit tests per get_system_metrics function
  - [ ] 2.2 Aggiungere psutil dependency per system resource monitoring
  - [ ] 2.3 Implementare active sessions count da database query
  - [ ] 2.4 Implementare total queries today counter da Prometheus metrics
  - [ ] 2.5 Calcolare average response time da Summary metrics
  - [ ] 2.6 Implementare memory e CPU usage tracking con psutil
  - [ ] 2.7 Verificare che tutti i test passino

- [ ] 3. Implementare performance instrumentation
  - [ ] 3.1 Scrivere tests per monitor_performance decorator
  - [ ] 3.2 Creare decorator per timing operations con Summary metrics
  - [ ] 3.3 Aggiungere error counting con Counter metrics
  - [ ] 3.4 Applicare decorator alle funzioni RAG critiche
  - [ ] 3.5 Applicare decorator alle operazioni database principali
  - [ ] 3.6 Configurare performance thresholds e warnings
  - [ ] 3.7 Verificare che tutti i test passino

- [ ] 4. Enhancere health endpoint con real metrics
  - [ ] 4.1 Scrivere integration tests per enhanced health endpoint
  - [ ] 4.2 Integrare get_system_metrics nel health endpoint
  - [ ] 4.3 Sostituire placeholder strings con valori calcolati
  - [ ] 4.4 Aggiungere database connection status checks reali
  - [ ] 4.5 Implementare uptime calculation accurato
  - [ ] 4.6 Formattare response JSON con schema enhanced
  - [ ] 4.7 Verificare che tutti i test passino

- [ ] 5. Implementare cache statistics tracking
  - [ ] 5.1 Scrivere tests per cache hit/miss tracking
  - [ ] 5.2 Identificare cache layer esistente (Redis/in-memory)
  - [ ] 5.3 Implementare cache operations counter
  - [ ] 5.4 Calcolare cache hit rate percentage
  - [ ] 5.5 Integrare cache stats nel health endpoint
  - [ ] 5.6 Esporre cache metrics via Prometheus
  - [ ] 5.7 Verificare che tutti i test passino
