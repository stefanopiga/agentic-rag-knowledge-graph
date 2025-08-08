# Sistema di Test Agentic RAG

Sistema completo di testing per il progetto Agentic RAG Knowledge Graph.

## 🎯 Panoramica

Il sistema di test è organizzato in **4 fasi principali** eseguite in sequenza:

1. **🏗️ Infrastructure** - Database e connessioni
2. **⚙️ Pipeline** - Ingestion e processing
3. **🔗 Integration** - AI e Django
4. **🚀 End-to-End** - Workflow completo

## 🚀 Quick Start

### Esecuzione Completa

```bash
# Test completi di tutto il sistema
python tests/system/run_all_tests.py
```

### Modalità Veloce

```bash
# Solo infrastruttura + pipeline (per debug rapido)
python tests/system/run_all_tests.py --fast
```

## 📋 Comandi Disponibili

### Master Runner

```bash
# Test completi
python tests/system/run_all_tests.py

# Modalità veloce (solo infrastruttura + pipeline)
python tests/system/run_all_tests.py --fast

# Skip fasi specifiche
python tests/system/run_all_tests.py --skip-integration
python tests/system/run_all_tests.py --skip-end-to-end

# Output dettagliato
python tests/system/run_all_tests.py --verbose
```

### Test Individuali

```bash
# Singole fasi di test
python tests/system/test_infrastructure.py
python tests/system/test_pipeline.py
python tests/system/test_integration.py
python tests/system/test_end_to_end.py
```

## 📊 Output e Logging

### Log Files

Tutti i risultati vengono salvati in `logs/`:

- `test_session_YYYYMMDD_HHMMSS.log` - Log completo sessione
- `infrastructure.log` - Log test infrastruttura
- `pipeline.log` - Log test pipeline
- `integration.log` - Log test integrazione
- `end_to_end.log` - Log test end-to-end

### Risultati JSON

Risultati strutturati salvati in:

- `logs/infrastructure_results_YYYYMMDD_HHMMSS.json`
- `logs/pipeline_results_YYYYMMDD_HHMMSS.json`
- etc.

## 🔍 Dettaglio Fasi di Test

### 1. 🏗️ Test Infrastructure

**Verifica componenti base del sistema:**

- ✅ Importazioni Python critiche
- ✅ Connessione PostgreSQL + verifica tabelle
- ✅ Connessione Neo4j + conteggio nodi
- ✅ Configurazione Agent
- ✅ Validazione Provider (OpenAI)

**Esecuzione:**

```bash
python tests/system/test_infrastructure.py
```

### 2. ⚙️ Test Pipeline

**Verifica pipeline elaborazione documenti:**

- ✅ Incremental Manager
- ✅ Document Scanning
- ✅ DOCX Processor
- ✅ Chunker
- ✅ Category Recognition (ginocchio_e_anca, ATM, etc.)
- ✅ Medical Entities Extraction

**Esecuzione:**

```bash
python tests/system/test_pipeline.py
```

### 3. 🔗 Test Integration

**Verifica integrazione AI e Django:**

- ✅ OpenAI Integration
- ✅ Django Setup
- ✅ Django Migrations
- ✅ Quiz Models
- ✅ Quiz Generator
- ✅ API Endpoints

**Esecuzione:**

```bash
python tests/system/test_integration.py
```

### 4. 🚀 Test End-to-End

**Verifica workflow completo:**

- ✅ Document Creation (documenti test)
- ✅ Ingestion Workflow
- ✅ Agent Query
- ✅ Quiz Generation
- ✅ Full Pipeline Integration

**Esecuzione:**

```bash
python tests/system/test_end_to_end.py
```

## ⚙️ Configurazione

### Variables d'Ambiente Richieste

```bash
# Database (usa DATABASE_URL se disponibile, altrimenti fallback a parametri separati)
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require
# OPPURE per setup locale:
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=rag_knowledge_graph
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=postgres

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# AI Provider
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-openai-key
LLM_CHOICE=gpt-4-turbo-preview
EMBEDDING_PROVIDER=openai
EMBEDDING_API_KEY=sk-your-openai-key
EMBEDDING_MODEL=text-embedding-3-small
```

### Dipendenze

Tutte le dipendenze sono in `requirements.txt`:

```bash
pip install -r requirements.txt
```

## 📈 Interpretazione Risultati

### Exit Codes

- `0` - Tutti i test superati ✅
- `1` - Warning (≤2 fallimenti) ⚠️
- `2` - Errore critico (>2 fallimenti) ❌

### Status Finali

- **🎉 TUTTI I TEST SUPERATI** - Sistema pronto per produzione
- **⚠️ SISTEMA PRINCIPALMENTE FUNZIONANTE** - Problemi minori da risolvere
- **❌ PROBLEMI CRITICI RILEVATI** - Richiedono intervento immediato

### Raccomandazioni Automatiche

Il sistema genera raccomandazioni automatiche basate sui risultati:

- ✅ **Tutti OK** → Procedere con ingestion documenti reali
- ⚠️ **Warning** → Verificare fallimenti minori
- ❌ **Errori** → Risolvere problemi critici

## 🛠️ Troubleshooting

### Problemi Comuni

#### Database Connection Failed

```bash
# Verifica servizi attivi
# PostgreSQL: verifica che il servizio sia running
# Neo4j: verifica che il servizio sia running
```

#### OpenAI API Error

```bash
# Verifica API key
echo $OPENAI_API_KEY

# Test connessione
python -c "import openai; client = openai.OpenAI(); print('OK')"
```

#### Django Import Error

```bash
# Verifica che fisio-rag-saas sia presente
ls ../fisio-rag-saas/

# Verifica Django installato
pip show django
```

### Debug Modalità

Per debug dettagliato:

1. **Test singola fase:** `python tests/system/test_infrastructure.py`
2. **Check log individuali:** `logs/infrastructure.log`
3. **Modalità verbose:** `--verbose`

## 🔄 Integrazione con CI/CD

### GitHub Actions

Esempio configurazione per CI:

```yaml
- name: Run System Tests
  run: |
    python tests/system/run_all_tests.py --fast

- name: Upload Test Results
  uses: actions/upload-artifact@v3
  with:
    name: test-logs
    path: logs/
```

### Pre-commit Hook

```bash
# Aggiungi a .git/hooks/pre-commit
python tests/system/run_all_tests.py --fast
```

## 📚 Estensibilità

### Aggiungere Nuovi Test

Per aggiungere nuove fasi di test:

1. Crea nuovo file `test_my_feature.py`
2. Eredita da pattern logging esistente
3. Aggiungi al `run_all_tests.py`

### Custom Logger

```python
from tests.system.test_logger import create_logger

logger = create_logger("my_test")
logger.log_test_start("My Test")
logger.log_test_success("My Test", "Details")
```

## 🎯 Best Practices

1. **Esegui sempre test completi** prima di deployment
2. **Modalità fast per debug** durante sviluppo
3. **Controlla log dettagliati** per fallimenti
4. **Mantieni environment variables** aggiornate
5. **Backup database** prima di test distruttivi

---

## 📞 Support

Per problemi con il sistema di test:

1. Controlla `logs/` per dettagli errori
2. Verifica configurazione environment
3. Esegui test singoli per isolare problema
4. Consulta sezione troubleshooting

**Happy Testing! 🚀**
