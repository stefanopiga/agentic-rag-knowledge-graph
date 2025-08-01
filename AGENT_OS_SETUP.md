# Agent OS - Inizializzazione Sistema

## Panoramica

Il sistema Agent OS implementa un'architettura Agentic RAG avanzata che combina:

- **Vector Database** (PostgreSQL + pgvector): Ricerca semantica
- **Knowledge Graph** (Neo4j + Graphiti): Relazioni temporali
- **AI Agent** (Pydantic AI): Selezione automatica tool con transparency completa

## Status Attuale

✅ **PRODUCTION READY**

- 58/58 test passati
- Documentazione completa
- Supporto provider multipli
- CLI con tool transparency
- API streaming funzionale

## Inizializzazione Rapida

### 1. Setup Environment

```cmd
# Creazione virtual environment
python -m venv venv
venv\Scripts\activate

# Installazione dipendenze
pip install -r requirements.txt
```

### 2. Configurazione Database

#### PostgreSQL Setup

```cmd
# Crea database con pgvector
# Esegui sql/schema.sql nel tuo database PostgreSQL

# IMPORTANTE: Aggiorna dimensioni embedding se necessario
# Lines 31, 67, 100 in sql/schema.sql:
# vector(1536) per OpenAI text-embedding-3-small
# vector(768) per Ollama nomic-embed-text
```

#### Neo4j Setup

```cmd
# Opzione A: Neo4j Desktop (Recommended)
# 1. Download Neo4j Desktop
# 2. Crea nuovo DBMS con password
# 3. Annota URI: bolt://localhost:7687

# Opzione B: Local-AI-Packaged
# git clone https://github.com/coleam00/local-ai-packaged
```

### 3. Configurazione Environment

```cmd
# Copia configurazione base
copy .env.example .env

# Modifica .env con le tue credenziali:
# - DATABASE_URL (PostgreSQL)
# - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
# - LLM_API_KEY (OpenAI/Ollama/OpenRouter/Gemini)
```

### 4. Preparazione Documenti

```cmd
# Crea cartella documenti
mkdir documents

# Usa documenti esempio (21 file big tech)
xcopy big_tech_docs\* documents\ /s

# Oppure aggiungi i tuoi file markdown
```

### 5. Ingestion Pipeline

```cmd
# IMPORTANTE: Esegui prima dell'uso dell'agent
python -m ingestion.ingest

# Opzioni avanzate:
# python -m ingestion.ingest --clean     # Pulisce database prima
# python -m ingestion.ingest --verbose   # Output dettagliato

# NOTA: Knowledge graph building richiede 30+ minuti per dataset completo
```

### 6. Avvio Sistemi

#### Terminal 1: API Server

```cmd
python -m agent.api
# Server disponibile su http://localhost:8058
```

#### Terminal 2: CLI Interface

```cmd
python cli.py
# Interfaccia interattiva con tool transparency
```

## Funzionalità Agent OS

### Tool Selection Automatica

L'agent seleziona automaticamente i tool ottimali:

- **Vector Search**: Query semantiche ("What AI research is Google doing?")
- **Graph Search**: Relazioni ("How are Microsoft and OpenAI connected?")
- **Hybrid Search**: Analisi complesse ("Compare FAANG AI strategies")
- **Document Retrieval**: Recupero documenti completi
- **Entity Relationships**: Esplorazione connessioni
- **Timeline Queries**: Evoluzione temporale facts

### Tool Transparency

Il CLI mostra in tempo reale:

```
🛠 Tools Used:
  1. vector_search (query='Microsoft AI initiatives', limit=10)
  2. graph_search (query='Microsoft AI projects')
```

### Provider Flessibilità

Supporto immediato per:

- **OpenAI**: gpt-4o-mini, text-embedding-3-small
- **Ollama**: qwen2.5:14b-instruct, nomic-embed-text
- **OpenRouter**: anthropic/claude-3-5-sonnet
- **Gemini**: gemini-2.0-flash-exp

## Testing & Validazione

```cmd
# Esegui test completi
pytest

# Test con coverage
pytest --cov=agent --cov=ingestion --cov-report=html

# Health check API
curl http://localhost:8058/health
```

## Query Example

```cmd
# Avvia CLI
python cli.py

# Query semantica
You: What are Google's main AI initiatives?
🤖 Assistant: Google has several major AI initiatives including...
🛠 Tools Used: vector_search

# Query relazionale
You: How is Microsoft connected to OpenAI?
🤖 Assistant: Microsoft has a significant strategic partnership...
🛠 Tools Used: graph_search, get_entity_relationships

# Query ibrida
You: Compare AI strategies of FAANG companies
🤖 Assistant: Comparing the AI strategies across FAANG...
🛠 Tools Used: hybrid_search, vector_search, graph_search
```

## Configurazione Provider Multipli

### OpenAI (Default)

```env
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key
LLM_CHOICE=gpt-4o-mini
```

### Ollama (Local)

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_CHOICE=qwen2.5:14b-instruct
```

### OpenRouter

```env
LLM_PROVIDER=openrouter
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=your-openrouter-key
LLM_CHOICE=anthropic/claude-3-5-sonnet
```

## Troubleshooting

### Database Connection

```cmd
# Test PostgreSQL
psql -d "$DATABASE_URL" -c "SELECT 1;"

# Test Neo4j
curl -u neo4j:password http://localhost:7474/db/data/
```

### Agent Non Restituisce Risultati

```cmd
# Verifica ingestion completata
python -m ingestion.ingest --verbose

# Verifica documenti in database
psql -d "$DATABASE_URL" -c "SELECT COUNT(*) FROM documents;"
```

### Embedding Dimensions Mismatch

```cmd
# Aggiorna sql/schema.sql lines 31, 67, 100
# OpenAI: vector(1536)
# Ollama: vector(768)
# Ricreare tabelle dopo modifica
```

## Agent OS Status

**✅ Sistema Completo e Production-Ready**

- Architettura ibrida RAG + Knowledge Graph
- Tool selection intelligente con transparency
- Provider flessibili con switching seamless
- Testing completo e error handling
- Documentazione dettagliata

## Estensioni Future

- Graph visualization web UI
- Multi-tenant support
- Real-time document updates
- Advanced caching layer
- Docker deployment configs
