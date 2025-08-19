# Spec Tasks

## Tasks

- [x] 1. Implementare NLP entity extraction
  - [x] 1.1 Scrivere unit tests per extract_entities_from_chunks con mock spaCy
  - [x] 1.2 Aggiungere spaCy dependency a requirements.txt e pyproject.toml
  - [x] 1.3 Implementare spaCy model loading con lazy initialization
  - [x] 1.4 Sostituire placeholder con NLP entity extraction logic
  - [x] 1.5 Arricchire chunk metadata con entities estratte
  - [x] 1.6 Aggiungere error handling per spaCy model failures
  - [x] 1.7 Verificare che tutti i test passino

- [x] 2. Implementare entity storage in Neo4j graph
  - [x] 2.1 Scrivere integration tests per store_entities_in_graph
  - [x] 2.2 Creare nuova funzione store_entities_in_graph in graph_builder
  - [x] 2.3 Implementare Cypher queries per entity creation con MERGE pattern
  - [x] 2.4 Aggiungere tenant_id isolation a tutte le operazioni graph
  - [x] 2.5 Implementare batch entity creation per performance
  - [x] 2.6 Creare indexes Neo4j necessari per entity queries
  - [x] 2.7 Verificare che tutti i test passino

- [x] 3. Implementare entity relationships e co-occurrence
  - [x] 3.1 Scrivere tests per relationship creation tra entità
  - [x] 3.2 Implementare CO_OCCURS relationships tra entità stesso chunk
  - [x] 3.3 Implementare MENTIONED_IN relationships tra entità e chunks
  - [x] 3.4 Aggiungere weight calculation per relationship strength
  - [x] 3.5 Integrare relationship creation nel flusso di ingestion
  - [x] 3.6 Aggiungere metadata appropriati alle relazioni
  - [x] 3.7 Verificare che tutti i test passino

- [x] 4. Implementare get_related_entities graph traversal
  - [x] 4.1 Scrivere integration tests per get_related_entities con tenant isolation
  - [x] 4.2 Sostituire placeholder con Cypher query per entity traversal
  - [x] 4.3 Implementare depth-limited graph navigation (max depth 3)
  - [x] 4.4 Aggiungere tenant_id filtering a tutte le queries Cypher
  - [x] 4.5 Formattare response con related entities e relationship metadata
  - [x] 4.6 Aggiungere error handling per Neo4j connection failures
  - [x] 4.7 Verificare che tutti i test passino

- [x] 5. Integrare entity extraction nel pipeline ingestion
  - [x] 5.1 Scrivere end-to-end tests per ingestion con entity extraction
  - [x] 5.2 Aggiornare ingestion flow per chiamare extract_entities_from_chunks
  - [x] 5.3 Aggiornare ingestion flow per chiamare store_entities_in_graph
  - [x] 5.4 Aggiornare IngestionResult per includere entities statistics
  - [x] 5.5 Aggiungere monitoring per entity extraction performance
  - [x] 5.6 Verificare che tutti i test passino
