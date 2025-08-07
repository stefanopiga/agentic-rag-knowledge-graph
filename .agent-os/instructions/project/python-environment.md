# Python Environment Setup per FisioRAG

## Panoramica

Il progetto FisioRAG richiede un ambiente virtuale Python attivo per tutti i comandi. Questo documento definisce le procedure corrette per l'esecuzione di comandi nel progetto.

## Ambiente Virtuale Richiesto

Il progetto utilizza un ambiente virtuale Python che deve essere attivato prima di eseguire qualsiasi comando Python o npm/Node.js.

### Percorso Ambiente Virtuale

- **Windows**: `venv\Scripts\activate`
- **Linux/macOS**: `source venv/bin/activate`

## Procedure Obbligatorie

### 1. Attivazione Automatica Terminale

**REGOLA CRITICA**: Prima di eseguire qualsiasi comando Python, pip, npm, o comandi di progetto, l'ambiente virtuale DEVE essere attivato.

#### Comando Corretto per Windows:

```cmd
venv\Scripts\activate && [COMANDO_EFFETTIVO]
```

#### Esempi Corretti:

```cmd
# Installazione dipendenze Python
venv\Scripts\activate && pip install -r requirements.txt

# Avvio server API
venv\Scripts\activate && python -m agent.api

# Ingestione documenti
venv\Scripts\activate && python -m ingestion.ingest --documents-dir documents_test --tenant-slug default

# CLI interattiva
venv\Scripts\activate && python cli.py --tenant-slug default

# Test suite
venv\Scripts\activate && python run_comprehensive_tests.py

# Comandi Django
venv\Scripts\activate && cd fisio_rag_saas && python manage.py runserver

# Frontend (dalla directory frontend) - Usa pnpm
venv\Scripts\activate && cd frontend && pnpm install
venv\Scripts\activate && cd frontend && pnpm run dev
venv\Scripts\activate && cd frontend && pnpm run build
venv\Scripts\activate && cd frontend && pnpm run test
```

### 2. Struttura Directory

Il workspace ha questa struttura:

```
agentic-rag-knowledge-graph/           # Root del progetto
├── venv/                              # Ambiente virtuale Python
├── agent/                             # Agente AI e API FastAPI
├── fisio_rag_saas/                    # Applicazione Django SaaS
├── ingestion/                         # Pipeline ingestione documenti
├── frontend/                          # Interfaccia utente React (da creare)
├── sql/                               # Schemi database
├── documents_test/                    # Documenti test
├── tests/                             # Suite test
├── requirements.txt                   # Dipendenze Python
├── .env                               # Variabili ambiente
└── README.md                          # Documentazione
```

### 3. Prerequisiti Sistema

- Python 3.11+
- PostgreSQL con estensione pgvector
- Neo4j database
- Node.js (per frontend)
- pnpm (package manager per frontend)
- API keys per OpenAI

### 4. Variabili d'Ambiente

Il file `.env` deve contenere:

```env
DATABASE_URL=postgresql://user:pass@host:port/db
NEO4J_URI=neo4j+s://host:port
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

LLM_PROVIDER=openai
LLM_API_KEY=sk-your-api-key
EMBEDDING_API_KEY=sk-your-api-key

DJANGO_SECRET_KEY=your-django-secret-key
```

## Errori Comuni da Evitare

### ❌ SCORRETTO:

```cmd
python -m agent.api
pip install package
npm install
```

### ✅ CORRETTO:

```cmd
venv\Scripts\activate && python -m agent.api
venv\Scripts\activate && pip install package
venv\Scripts\activate && cd frontend && npm install
```

## Workflow Sviluppo

### 1. Setup Iniziale

```cmd
# Creare ambiente virtuale (solo prima volta)
python -m venv venv

# Attivare ambiente e installare dipendenze
venv\Scripts\activate && pip install -r requirements.txt
```

### 2. Sviluppo Quotidiano

```cmd
# Terminal 1: Backend API
venv\Scripts\activate && python -m agent.api

# Terminal 2: Django SaaS
venv\Scripts\activate && cd fisio_rag_saas && python manage.py runserver

# Terminal 3: Frontend (già creato) - Usa pnpm
venv\Scripts\activate && cd frontend && pnpm run dev
```

### 3. Test e Sviluppo

```cmd
# Test completi
venv\Scripts\activate && python run_comprehensive_tests.py

# Ingestione documenti
venv\Scripts\activate && python -m ingestion.ingest --documents-dir documents_test --tenant-slug default

# CLI interattiva
venv\Scripts\activate && python cli.py --tenant-slug default
```

## Note per Agent OS

- **SEMPRE** anteporre `venv\Scripts\activate &&` ai comandi Python
- **VERIFICARE** che il working directory sia corretto
- **UTILIZZARE** i path relativi dal root del progetto
- **CONTROLLARE** che le variabili d'ambiente siano configurate

## Troubleshooting

### Ambiente Virtuale Non Attivato

**Sintomo**: `ModuleNotFoundError` o comandi Python falliscono
**Soluzione**: Anteporre `venv\Scripts\activate &&` al comando

### Working Directory Errata

**Sintomo**: File non trovati o path errors
**Soluzione**: Verificare di essere nella root del progetto prima dei comandi

### Dipendenze Mancanti

**Sintomo**: Import errors
**Soluzione**: `venv\Scripts\activate && pip install -r requirements.txt`
