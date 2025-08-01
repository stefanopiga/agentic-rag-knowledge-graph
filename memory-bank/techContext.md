# Technical Context - Agentic RAG with Knowledge Graph

## Technology Stack

### Core Framework

- **Python 3.11+**: Primary language con modern typing support
- **Pydantic AI**: Agent framework con type safety e dependency injection
- **FastAPI**: Async web framework con automatic OpenAPI docs
- **asyncio/asyncpg**: Async-first architecture per performance

### Database Technologies

- **PostgreSQL 15+**: Primary database con JSON support
- **pgvector Extension**: Vector similarity search (cosine distance)
- **Neo4j 5.x**: Graph database engine
- **Graphiti**: Temporal knowledge graph library

### AI/ML Providers

```env
# Flexible LLM Provider Support
LLM_PROVIDER=openai|ollama|openrouter|gemini
LLM_BASE_URL=https://api.openai.com/v1
LLM_CHOICE=gpt-4o-mini|qwen2.5:14b-instruct|claude-3-5-sonnet

# Embedding Providers
EMBEDDING_PROVIDER=openai|ollama
EMBEDDING_MODEL=text-embedding-3-small|nomic-embed-text
```

## Environment Setup

### Prerequisites Installation

```bash
# Python environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Dependencies
pip install -r requirements.txt
```

### Database Setup Sequence

1. **PostgreSQL Configuration**:

   ```bash
   # Execute schema creation
   psql -d "$DATABASE_URL" -f sql/schema.sql

   # Verify pgvector extension
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

2. **Neo4j Setup Options**:
   - **Option A**: Local-AI-Packaged (Recommended)
   - **Option B**: Neo4j Desktop
   - **Connection**: `bolt://localhost:7687`

### Environment Variables

```env
# Database Configuration
DATABASE_URL=postgresql://user:pass@host:5432/db
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# LLM Configuration (OpenAI example)
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key
LLM_CHOICE=gpt-4o-mini

# Embedding Configuration
EMBEDDING_PROVIDER=openai
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=sk-your-key
EMBEDDING_MODEL=text-embedding-3-small

# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
APP_PORT=8058
```

## Development Workflow

### 1. Document Preparation

```bash
# Sample documents available
cp -r big_tech_docs/* documents/
# 21 detailed markdown files about tech companies
```

### 2. Database Schema Setup

```bash
# Creates tables: documents, chunks, sessions, messages
# Includes vector indexes and search functions
# ⚠️ Note: Drops existing tables (adjust embedding dimensions first)
```

### 3. Document Ingestion

```bash
# Full ingestion pipeline
python -m ingestion.ingest

# Options:
--clean           # Clean existing data first
--chunk-size 800  # Custom chunk size
--no-semantic     # Disable LLM chunking
--fast           # Skip knowledge graph building
--verbose        # Detailed logging
```

### 4. API Server Launch

```bash
# Terminal 1: Start API server
python -m agent.api
# Server available at http://localhost:8058

# Terminal 2: Interactive CLI
python cli.py
# Real-time streaming + tool visibility
```

## Technical Constraints & Limits

### Vector Dimensions

- **OpenAI text-embedding-3-small**: 1536 dimensions
- **Ollama nomic-embed-text**: 768 dimensions
- **Schema Update Required**: Modify sql/schema.sql lines 31, 67, 100

### Graphiti Limitations

- **Token Limits**: Large chunks truncated to 6000 chars
- **Processing Time**: Knowledge graph building può richiedere 30+ minuti
- **Batch Size**: Max 3 chunks per batch per evitare rate limits

### Performance Considerations

- **Vector Search**: Sub-second response con proper indexing
- **Graph Queries**: Più lente ma ricche di relationships
- **Hybrid Search**: Bilanciamento tra speed e completeness

## Development Tools

### Testing Framework

```bash
# Run all tests (58/58 passing)
pytest

# With coverage
pytest --cov=agent --cov=ingestion --cov-report=html

# Specific test categories
pytest tests/agent/
pytest tests/ingestion/
```

### Code Quality

```bash
# Formatting & linting
black .
ruff check .

# Type checking
mypy agent/ ingestion/
```

### Monitoring & Debugging

- **Logging**: Configurable levels (DEBUG, INFO, WARNING, ERROR)
- **API Docs**: http://localhost:8058/docs (automatic OpenAPI)
- **Health Check**: http://localhost:8058/health
- **Tool Transparency**: CLI shows agent reasoning process

## Deployment Considerations

### Database Requirements

- **PostgreSQL**: Necessario pgvector extension
- **Neo4j**: Accessible via bolt:// protocol
- **Connection Pooling**: asyncpg per PostgreSQL connections

### Scalability Notes

- **Embedding Cache**: In-memory caching per repeated queries
- **Batch Processing**: Parallel document ingestion
- **Graph Optimization**: Entity deduplication e relationship merging

### Security Best Practices

- **API Keys**: Environment variables only, mai hardcoded
- **Database Access**: Connection strings in .env
- **CORS Configuration**: `allow_origins=["*"]` per development only
