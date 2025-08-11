# FisioRAG - Agentic RAG Multi-Tenant per la Riabilitazione Medica

## 📋 **Agent OS - Guida Navigazione Documentazione**

**Per sviluppatori e Agent OS**: La documentazione del progetto è organizzata strategicamente. Leggi questi files nell'ordine indicato per comprendere lo stato completo del progetto:

### 🎯 **Files Prioritari da Leggere**

PR aperti verso `main`:
- #7 docker-modernization → main
- #8 scalability-testing → main
- #9 security-hardening → main

1. **`.agent-os/project-status.md`** → **STATUS CORRENTE COMPLETO**

   - Milestone progress (3/4 completate)
   - Issues identificati (backend dependencies)
   - Next steps prioritari

2. **`.agent-os/product/ROADMAP.md`** → **ROADMAP E MILESTONE**

   - Fasi completate e in corso
   - Timeline sviluppo
   - Features implementate

3. **`.agent-os/product/UI_FRONTEND_SPECIFICATION.md`** → **FRONTEND ARCHITECTURE**

   - Specifiche React 19 + TypeScript
   - State management Zustand
   - Component structure completa

4. **`.agent-os/product/MEDICAL_RAG_SYSTEM_SPECIFICATION.md`** → **BACKEND ARCHITECTURE**
   - Sistema RAG agentico
   - Multi-tenancy design
   - Knowledge graph + Vector search

### 🔧 **Files Troubleshooting**

- **`.agent-os/instructions/project/frontend-troubleshooting.md`** → Risoluzione problemi frontend
- **`.agent-os/instructions/project/python-environment.md`** → Setup ambiente Python

---

## 🚀 **Status Progetto Corrente**

⚠️ **MILESTONE 4 IN CORSO** - Integration & Deployment con issues backend identificati

| Componente      | Status             | Note                                 |
| --------------- | ------------------ | ------------------------------------ |
| **Frontend**    | ✅ **FUNZIONANTE** | React app su `localhost:3000`        |
| **Backend**     | ❌ **ISSUES**      | Redis connection refused, dipendenze |
| **Databases**   | ⚠️ **PARZIALE**    | PostgreSQL + Neo4j OK, Redis KO      |
| **Integration** | ⏳ **PENDING**     | Bloccata da backend issues           |

---

## 🏗️ **Panoramica Architettura**

Sistema RAG (Retrieval-Augmented Generation) agentico, multi-tenant e basato su knowledge graph, specializzato per l'ambito medico-riabilitativo. Combina ricerca vettoriale con knowledge graph per fornire insight clinici con alta precisione contestuale.

**Stack Tecnologico**:

### Frontend ✅ **COMPLETAMENTE FUNZIONALE**

- **Framework**: React 19 + TypeScript + Vite
- **Styling**: Tailwind CSS 3.4.0
- **State**: Zustand stores
- **Routing**: React Router 7.x
- **Build**: Production ready (278.72 kB)

### Backend ⚠️ **ISSUES DEPENDENCIES**

- **AI Engine**: Pydantic AI + Graphiti
- **API**: FastAPI (async)
- **Databases**: PostgreSQL (pgvector) + Neo4j + Redis
- **SaaS**: Django multi-tenant

### Issues Correnti 🔧

1. **Redis connection refused** - Server non avviato
2. **aioredis compatibility** - Python 3.12+ conflicts
3. **Neo4j/Graphiti setup** - Configuration dependencies

---

## 🚀 **Quick Start** (Modernizzato con UV + PNPM + BUN)

### **Setup Automatico Ultra-Rapido**

```bash
# Setup completo con un comando
pnpm setup
# O con Bun (ancora più veloce)
bun install && uv sync
```

### **1. Frontend** (React + TypeScript con PNPM/BUN)

```bash
# Con PNPM (default)
pnpm dev:frontend
# ➜ Local: http://localhost:3000/

# Con BUN (ultra-veloce)
pnpm dev:bun
# O direttamente: bun run frontend/src/main.tsx
```

### **2. Backend** (Python con UV)

```bash
# Con UV (10-100x più veloce di pip)
pnpm dev:backend
# O direttamente: uv run python run_backend.py

# Setup ambiente automatico
uv sync  # Crea .venv e installa tutto automaticamente
```

### **3. Full-Stack Development**

```bash
# Avvia frontend + backend simultaneamente
pnpm dev

# Build production per entrambi
pnpm build

# Test completi
pnpm test
```

### 3. **Database Setup**

```powershell
# Reset completo DB (Windows)
./scripts/reset_db_windows.cmd

# Avvio servizi
docker compose up -d

# Verifica health API
curl http://localhost:8000/health
```

Note Compose:
- `docker-compose.yml` imposta per `app`:
  - `OPENAI_API_KEY=${LLM_API_KEY}`
  - `NEO4J_URI=bolt://neo4j:7687`
  - `REDIS_URL=redis://redis:6379/0`

---

## 📁 **Struttura Progetto**

```
agentic-rag-knowledge-graph/
├── .agent-os/                    # 📋 DOCUMENTAZIONE AGENT OS
│   ├── project-status.md         # → STATUS CORRENTE COMPLETO
│   ├── product/                  # → SPECIFICATIONS & ROADMAP
│   └── instructions/project/     # → TROUBLESHOOTING GUIDES
│
├── frontend/                     # ✅ REACT APP FUNZIONANTE
│   ├── src/components/           # → 25+ componenti UI
│   ├── src/services/            # → API integration layers
│   ├── src/stores/              # → Zustand state management
│   └── dist/                    # → Production build ready
│
├── agent/                       # ⚠️ BACKEND AI AGENT (issues)
│   ├── api.py                   # → FastAPI endpoints
│   ├── agent.py                 # → Pydantic AI agent
│   └── tools.py                 # → RAG tools (vector + graph)
│
├── ingestion/                   # 📥 DOCUMENT PROCESSING
├── fisio_rag_saas/             # 🏢 DJANGO SAAS APP
├── sql/                        # 🗄️ DATABASE SCHEMAS
└── tests/                      # 🧪 COMPREHENSIVE TEST SUITE
```

---

## 🎯 **Per Agent OS: Prossimi Steps**

1. **PRIORITÀ**: Risolvere backend dependencies (Redis + aioredis)
2. **Integration**: Collegare frontend funzionante con backend
3. **Testing**: End-to-end integration testing
4. **Deployment**: Production deployment pipeline

**Tempo stimato**: 2-3 giorni per risoluzione completa

---

## 🛠️ **Installazione Ambiente Modernizzata**

### **Prerequisiti Moderni**

- **Python 3.11+** con **UV** (gestisce automaticamente versioni e virtual envs)
- **Node.js 18+** con **PNPM/BUN** (package manager ultra-performanti)
- **PostgreSQL** con pgvector
- **Neo4j** 
- **Redis** server
- **OpenAI** API key

### **Setup Ultra-Rapido (Auto-Configurato)**

```bash
# 1. Installa tool moderni (una volta sola)
curl -LsSf https://astral.sh/uv/install.sh | sh  # UV
npm install -g pnpm  # PNPM
curl -fsSL https://bun.sh/install | bash  # BUN (opzionale)

# 2. Setup progetto completo
git clone <repo>
cd agentic-rag-knowledge-graph
pnpm setup  # Installa tutto automaticamente

# 3. Avvia development
pnpm dev  # Frontend + Backend + Hot reload

# File .env configurato automaticamente
```

### **Performance Comparison** ⚡

| Tool     | Speed vs Standard | Disk Usage | Features                    |
|----------|-------------------|------------|-----------------------------|
| **UV**   | 10-100x vs pip    | -80%      | Auto venv, inline scripts  |
| **PNPM** | 2-3x vs npm       | -70%      | Workspaces, symlinks       |
| **BUN**  | 2-4x vs Node      | -50%      | Built-in bundler, TypeScript|

---

## 📊 **Metrics & Performance**

- **Frontend**: 6,300+ righe TypeScript/React
- **Backend**: 15,000+ righe Python
- **Components**: 25+ React components
- **Dependencies**: 40+ frontend packages, 98 Python packages
- **Build time**: 8.47s (frontend production)
- **Bundle size**: 278.72 kB (ottimizzato)

---

## 🚨 **Issues Tracking**

### Milestone 4 - Integration & Deployment

| Issue                           | Status | Priorità |
| ------------------------------- | ------ | -------- |
| Redis connection refused        | ❌     | HIGH     |
| aioredis TimeoutError duplicate | ❌     | HIGH     |
| Backend startup sequence        | ❌     | HIGH     |
| Frontend-Backend API testing    | ⏳     | MEDIUM   |

**Vedi `.agent-os/project-status.md` per details completi**

---

## 🎓 **Dominio Applicativo**

**Target**: Studenti fisioterapia e professionisti medici

**Features Mediche**:

- Analisi documenti riabilitativi
- Knowledge graph anatomico-patologico
- Ricerca semantica specializzata
- Multi-tenancy per istituzioni
- Supporto DOCX/PDF processing

**Caso d'uso**: "Quali sono le implicazioni del danno neurogeno sulla riabilitazione dell'anca?"

---

_Documentazione aggiornata: 2025-01-19 - Milestone 4 in corso_

---

## 🚀 Quick Start (Aggiornato 2025-08-08)

### 0) Ambiente (.env)
- Usa il tuo `env.txt` come base per `.env`
- Se lavori con Docker Compose, adatta solo gli host:
  - `DATABASE_URL=postgresql+asyncpg://rag_user:rag_password@postgres:5432/rag_db`
  - `NEO4J_URI=bolt://neo4j:7687`
  - `REDIS_URL=redis://redis:6379/0`
- Mantieni tutte le altre variabili (LLM, chunking, ecc.)

### 1) Avvio backend + DB (Compose)
```powershell
docker compose up -d
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
```

### 2) Avvio UI (Vite)
```powershell
$env:VITE_API_BASE_URL='http://localhost:8000'
pnpm --filter frontend dev
# UI: http://localhost:3000
```

Note
- Il container `app` espone l’API FastAPI su `http://localhost:8000`
- La UI in dev gira su `http://localhost:3000` e usa `VITE_API_BASE_URL`
- `.env.example` è solo un template; `.env` contiene i tuoi segreti
