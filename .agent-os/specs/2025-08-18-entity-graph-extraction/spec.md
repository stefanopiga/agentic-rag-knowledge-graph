# Spec Requirements Document

> Spec: Entity Extraction and Related Entities Graph Implementation
> Created: 2025-08-18
> Status: Planning

## Overview

Implementare l'estrazione di entità dai chunks di documenti e la costruzione di relazioni nel knowledge graph sostituendo i placeholder esistenti con funzionalità complete. Questo abilita ricerche semantiche arricchite e navigation attraverso entità correlate nel sistema RAG multi-tenant.

## User Stories

### Story 1: Entity Extraction da Document Chunks

Come sistema di ingestion, voglio estrarre automaticamente entità mediche/domain-specific dai chunks di documenti durante il processo di ingestion, così che il knowledge graph sia popolato con entità strutturate che migliorano la qualità delle ricerche RAG.

Il sistema deve utilizzare NLP models per identificare entità (persone, luoghi, concetti medici, organizzazioni) dai chunks e salvarle con metadata appropriati nel Neo4j graph database con isolamento tenant.

### Story 2: Knowledge Graph Navigation via Entità Correlate

Come utente del sistema RAG, voglio che le query possano navigare attraverso entità correlate nel knowledge graph, così che le risposte includano informazioni contestuali da documenti collegati attraverso entità comuni.

Il sistema deve implementare traversal di relazioni nel graph Neo4j per trovare entità correlate con tenant isolation, supportando query come "trova documenti correlati a questa entità" con profondità configurabile.

### Story 3: Tenant-Isolated Entity Management

Come sistema multi-tenant, voglio che ogni tenant abbia il proprio namespace di entità nel knowledge graph, così che le entità e relazioni di un tenant non siano visibili o accessibili da altri tenant.

Il sistema deve utilizzare tenant_id come property nelle entità Neo4j e filtrare tutte le query graph per garantire isolamento completo tra tenant.

## Spec Scope

1. **Entity Extraction Implementation** - Sostituire placeholder in `extract_entities_from_chunks` con NLP-based entity extraction usando spaCy o simili
2. **Graph Entity Storage** - Implementare storage di entità estratte in Neo4j con tenant isolation e metadata appropriati
3. **Entity Relationship Building** - Creare relazioni tra entità basate su co-occurrence nei documenti e semantic similarity
4. **Related Entities Query** - Implementare `get_related_entities` per traversal tenant-aware del knowledge graph
5. **Integration con RAG Pipeline** - Integrare entity extraction nel flusso di ingestion esistente con error handling

## Out of Scope

- Training di custom NLP models per entity extraction
- Implementazione entity resolution/deduplication avanzata  
- Performance optimization per large-scale graph operations
- Advanced graph analytics o machine learning su graph
- Entity linking a knowledge bases esterni (DBpedia, Wikidata)
- Real-time entity extraction per streaming data

## Expected Deliverable

1. Funzione `extract_entities_from_chunks` estrae entità reali da chunks usando NLP processing
2. Entità estratte sono salvate in Neo4j con tenant isolation e metadata completi
3. Funzione `get_related_entities` implementa traversal tenant-aware del knowledge graph con profondità configurabile