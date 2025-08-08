# Test Suite Completo

Suite di test completa per il sistema RAG con database PostgreSQL e Neo4j.

## Struttura

```
tests/comprehensive/
├── __init__.py                    # Init package
├── conftest.py                    # Configurazione pytest
├── test_database_connections.py   # Test connessioni database
├── test_ingestion_pipeline.py     # Test pipeline ingestion
├── test_query_operations.py       # Test query vettoriali e grafo
├── test_runner.py                 # Runner unificato
└── README.md                      # Documentazione
```

## Test Categories

### 1. Database Connections (`test_database_connections.py`)

#### PostgreSQL Tests

- **TestPostgreSQLConnections**: Test connessioni PostgreSQL base
  - `test_basic_connection`: Connessione base e query semplici
  - `test_database_schema_exists`: Verifica esistenza tabelle
  - `test_pgvector_extension`: Test estensione pgvector
  - `test_connection_pool_management`: Gestione pool connessioni
  - `test_transaction_handling`: Gestione transazioni
  - `test_rollback_handling`: Test rollback
  - `test_vector_operations`: Operazioni vettoriali complete

#### Neo4j Tests

- **TestNeo4jConnections**: Test connessioni Neo4j/Graphiti
  - `test_basic_graph_connection`: Connessione base grafo
  - `test_graph_database_info`: Informazioni database
  - `test_graph_indices_constraints`: Indices e constraints
  - `test_episode_creation`: Creazione episodi
  - `test_graph_search_functionality`: Funzionalità ricerca
  - `test_entity_relationships`: Relazioni entità
  - `test_concurrent_graph_operations`: Operazioni concorrenti

#### Integration Tests

- **TestDatabaseIntegration**: Test integrazione database
  - `test_cross_database_consistency`: Consistenza tra database
  - `test_transaction_coordination`: Coordinamento transazioni

#### Performance Tests

- **TestDatabasePerformance**: Test performance database
  - `test_bulk_insert_performance`: Performance inserimenti bulk
  - `test_vector_search_performance`: Performance ricerca vettoriale
  - `test_connection_pool_performance`: Performance pool connessioni

#### Error Handling Tests

- **TestDatabaseErrorHandling**: Test gestione errori
  - `test_connection_failure_recovery`: Recovery da failure
  - `test_invalid_query_handling`: Gestione query invalide
  - `test_constraint_violation_handling`: Gestione violazioni constraints
  - `test_timeout_handling`: Gestione timeout

### 2. Ingestion Pipeline (`test_ingestion_pipeline.py`)

#### Document Processing

- **TestDocumentProcessing**: Test processing documenti
  - `test_markdown_document_processing`: Processing markdown
  - `test_text_document_processing`: Processing testo
  - `test_metadata_extraction`: Estrazione metadata

#### Chunking Strategies

- **TestChunkingStrategies**: Test strategie chunking
  - `test_fixed_size_chunking`: Chunking dimensione fissa
  - `test_semantic_chunking`: Chunking semantico
  - `test_chunk_overlap`: Test overlap chunks

#### Embedding Generation

- **TestEmbeddingGeneration**: Test generazione embeddings
  - `test_embedding_generation`: Generazione embeddings base
  - `test_embedding_consistency`: Consistenza embeddings
  - `test_batch_embedding`: Embedding batch

#### Full Pipeline

- **TestFullPipeline**: Test pipeline completa
  - `test_complete_pipeline_run`: Esecuzione pipeline completa
  - `test_pipeline_with_graph_building`: Pipeline con grafo
  - `test_incremental_ingestion`: Ingestion incrementale
  - `test_pipeline_error_handling`: Gestione errori pipeline

#### Performance

- **TestPipelinePerformance**: Test performance pipeline
  - `test_large_document_processing`: Processing documenti grandi
  - `test_concurrent_pipeline_operations`: Operazioni concorrenti

### 3. Query Operations (`test_query_operations.py`)

#### Vector Queries

- **TestVectorQueries**: Test query vettoriali
  - `test_basic_vector_search`: Ricerca vettoriale base
  - `test_vector_search_relevance`: Rilevanza risultati
  - `test_hybrid_search`: Ricerca ibrida (vettoriale + testo)
  - `test_vector_search_limits`: Test limiti ricerca
  - `test_empty_vector_search`: Ricerca senza risultati

#### Graph Queries

- **TestGraphQueries**: Test query grafo
  - `test_basic_graph_search`: Ricerca base grafo
  - `test_entity_specific_search`: Ricerca entità specifiche
  - `test_relationship_queries`: Query relazioni
  - `test_temporal_queries`: Query temporali
  - `test_complex_graph_queries`: Query complesse
  - `test_graph_search_performance`: Performance ricerca grafo

#### Hybrid Querying

- **TestHybridQuerying**: Test query ibride
  - `test_combined_vector_graph_search`: Ricerca combinata
  - `test_result_ranking_combination`: Combinazione ranking
  - `test_query_context_enrichment`: Arricchimento contesto

#### Performance

- **TestQueryPerformance**: Test performance query
  - `test_concurrent_vector_searches`: Ricerche concorrenti
  - `test_large_result_set_handling`: Gestione set risultati grandi
  - `test_query_optimization`: Ottimizzazione query

## Utilizzo

### Runner Unificato

```bash
# Esegue tutti i test
python tests/comprehensive/test_runner.py

# Test specifici per tipo
python tests/comprehensive/test_runner.py --type smoke
python tests/comprehensive/test_runner.py --type performance
python tests/comprehensive/test_runner.py --type integration

# Test specifici per modulo
python tests/comprehensive/test_runner.py --module database
python tests/comprehensive/test_runner.py --module pipeline
python tests/comprehensive/test_runner.py --module query

# Con opzioni
python tests/comprehensive/test_runner.py --verbose --fail-fast
python tests/comprehensive/test_runner.py --parallel --type fast

# Genera report
python tests/comprehensive/test_runner.py --report
```

### Pytest Diretto

```bash
# Tutti i test
pytest tests/comprehensive/

# Test specifici
pytest tests/comprehensive/test_database_connections.py
pytest tests/comprehensive/test_ingestion_pipeline.py
pytest tests/comprehensive/test_query_operations.py

# Con marker
pytest tests/comprehensive/ -m "not slow"
pytest tests/comprehensive/ -m "integration"
pytest tests/comprehensive/ -m "unit"

# Con coverage
pytest tests/comprehensive/ --cov=agent --cov=ingestion --cov-report=html
```

## Configurazione

### Variabili Ambiente Richieste

```bash
# Database PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/test_db

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# LLM Provider
LLM_API_KEY=your_openai_key
LLM_CHOICE=gpt-4o-mini
LLM_PROVIDER=openai

# Embedding Provider
EMBEDDING_API_KEY=your_openai_key
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_PROVIDER=openai
```

### Setup Test Environment

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-html pytest-xdist

# Setup test database
createdb test_rag_knowledge_graph

# Run schema migration
python scripts/verify_neon_schema.py
```

## Markers

- `@pytest.mark.unit`: Test unitari veloci
- `@pytest.mark.integration`: Test integrazione
- `@pytest.mark.slow`: Test lenti (>5s)
- `@pytest.mark.asyncio`: Test asincroni

## Coverage

Target coverage: 80%

```bash
pytest tests/comprehensive/ --cov=agent --cov=ingestion --cov-report=html
open htmlcov/index.html
```

## Troubleshooting

### Problemi Comuni

1. **Database Connection Failed**

   - Verifica DATABASE_URL
   - Controlla che PostgreSQL sia in esecuzione
   - Verifica estensione pgvector installata

2. **Neo4j Connection Failed**

   - Verifica NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
   - Controlla che Neo4j sia in esecuzione
   - Verifica timeout configurazione

3. **API Key Errors**

   - Verifica LLM_API_KEY e EMBEDDING_API_KEY
   - Controlla rate limits provider

4. **Test Timeout**
   - Aumenta timeout in pytest.ini
   - Usa marker @pytest.mark.slow per test lunghi
   - Considera skip per test problematici

### Debug

```bash
# Verbose output
pytest tests/comprehensive/ -v -s

# Specific test
pytest tests/comprehensive/test_database_connections.py::TestPostgreSQLConnections::test_basic_connection -v -s

# Debug con PDB
pytest tests/comprehensive/ --pdb

# Log output
pytest tests/comprehensive/ --log-cli-level=DEBUG
```

## Performance

### Benchmark Target

- **Database connections**: < 1s per connessione
- **Vector search**: < 2s per query
- **Graph search**: < 10s per query
- **Pipeline processing**: > 1 chunk/s
- **Concurrent operations**: Scala linealmente

### Monitoring

Test performance automaticamente monitora:

- Tempi esecuzione
- Utilizzo memoria
- Throughput operazioni
- Latenza query

## Continuous Integration

### GitHub Actions Example

```yaml
name: Comprehensive Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: pgvector/pgvector:pg15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      neo4j:
        image: neo4j:5
        env:
          NEO4J_AUTH: neo4j/testpass
        options: >-
          --health-cmd "cypher-shell -u neo4j -p testpass 'RETURN 1'"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run comprehensive tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          NEO4J_URI: bolt://localhost:7687
          NEO4J_USER: neo4j
          NEO4J_PASSWORD: testpass
          LLM_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          EMBEDDING_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python tests/comprehensive/test_runner.py --type fast
```
