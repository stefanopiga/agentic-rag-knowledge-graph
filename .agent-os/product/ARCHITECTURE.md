# Architettura di FisioRAG

## Panoramica

FisioRAG è costruito su un'architettura a microservizi containerizzata, progettata per garantire scalabilità, manutenibilità e robustezza. Ogni componente è disaccoppiato e comunica tramite API definite.

## Stack Tecnologico

- **Servizio Principale**: `Python` con `FastAPI` per un'API asincrona ad alte prestazioni.
- **Database Relazionale e Vettoriale**: `PostgreSQL` con l'estensione `pgvector` per l'archiviazione dei metadati dei documenti e degli embedding vettoriali.
- **Database a Grafo**: `Neo4j` con il plugin `APOC` per la costruzione e l'interrogazione del knowledge graph.
- **Cache**: `Redis` per la cache delle sessioni e delle query frequenti, migliorando la reattività del sistema.
- **Modelli Linguistici (LLM)**: Integrazione esclusiva con i modelli di `OpenAI` per la generazione delle risposte.
- **Containerizzazione**: `Docker` e `Docker Compose` per orchestrare l'ambiente di sviluppo e produzione.
- **Core Agentico**: Libreria `pydantic-ai` per la gestione dell'agente e dei suoi strumenti.

## Flusso dei Dati

1.  **Ingestione**: I documenti (es. articoli scientifici, libri di testo) vengono processati attraverso una pipeline che estrae il testo, lo suddivide in chunk, genera embedding vettoriali (tramite API OpenAI) e costruisce nodi e relazioni nel knowledge graph (Neo4j).
2.  **Query dell'Utente**: Le richieste arrivano all'endpoint dell'API FastAPI.
3.  **Elaborazione Agente**: L'agente AI riceve la query e, in base ad essa, decide quale strumento utilizzare (ricerca vettoriale, ricerca sul grafo, o ibrida).
4.  **Recupero Dati**: Gli strumenti interrogano PostgreSQL/pgvector per la similarità semantica e Neo4j per le relazioni contestuali.
5.  **Generazione Risposta**: I risultati recuperati vengono forniti come contesto al modello OpenAI, che genera una risposta sintetica e coerente.
6.  **Risposta all'Utente**: La risposta finale viene inviata all'utente tramite l'API.

## Problemi di Coerenza Architetturale Rilevati

L'analisi ha rivelato un'incoerenza critica tra la progettazione multi-tenant del sistema e l'implementazione della pipeline di ingestione incrementale.

- **Mancanza di Propagazione del `tenant_id`**: La tabella `document_ingestion_status`, che è fondamentale per la gestione incrementale, richiede un `tenant_id` per ogni record. Tuttavia, le funzioni in `ingestion/incremental_manager.py` che creano e aggiornano questi record non erano state progettate per ricevere e inserire questo `tenant_id`.

- **Causa dell'Errore**: Questo disallineamento causa un errore di `NotNullViolationError` nel database durante l'ingestione, poiché il sistema tenta di creare un record di stato senza specificare a quale tenant appartiene, violando i vincoli di integrità dei dati dell'architettura multi-tenant.

- **Soluzione**: È necessario rifattorizzare le funzioni di gestione dello stato in `incremental_manager.py` e il flusso principale in `ingest.py` per garantire che il `tenant_id` venga passato correttamente e inserito in ogni record di stato. Questo allineerà la logica di ingestione con il resto dell'architettura del sistema.

