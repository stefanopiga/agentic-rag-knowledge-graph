# Active Context - Agentic RAG with Knowledge Graph

## Current Project State

**Status**: ✅ **PRODUCTION READY** - Sistema completo e funzionante

### Completion Summary

- ✅ **All Core Functionality**: Ingestion pipeline → Vector storage → Knowledge graph → Agent → API → CLI
- ✅ **Testing Coverage**: 58/58 tests passing con comprehensive mocking
- ✅ **Documentation**: README completo, installation guide, troubleshooting
- ✅ **Flexible Architecture**: Support multipli provider LLM e embedding
- ✅ **Agent Transparency**: CLI con visibility completa dei tool utilizzati

## Recent Implementation Focus

### Memory Bank Initialization (In Progress)

- **Task**: Creazione documentazione strutturata memory bank
- **Purpose**: Comprensione profonda progetto per future development sessions
- **Files Created**:
  - projectbrief.md ✅
  - productContext.md ✅
  - systemPatterns.md ✅
  - techContext.md ✅
  - activeContext.md ✅ (current)
  - progress.md (next)

### Key Architecture Decisions Made

#### 1. Agent Tool Selection Strategy

- **Vector Search**: Semantic similarity queries ("What AI research is Google doing?")
- **Graph Search**: Relationship exploration ("How are Microsoft and OpenAI connected?")
- **Hybrid Search**: Complex analysis requiring both approaches
- **Control**: System prompt in `agent/prompts.py` definisce selection logic

#### 2. Database Schema Optimization

- **Vector Storage**: PostgreSQL con pgvector (1536 dimensions default)
- **Graph Storage**: Neo4j via Graphiti con temporal episodes
- **Functions**: Custom PostgreSQL functions per match_chunks, hybrid_search
- **Indexes**: Optimized per vector similarity e text search

#### 3. Provider Flexibility Implementation

- **LLM Providers**: OpenAI, Ollama, OpenRouter, Gemini support
- **Embedding Providers**: OpenAI, Ollama con automatic client creation
- **Configuration**: Environment-based switching senza code changes

## Current Work Focus

### Immediate Tasks

1. **Complete Memory Bank**: Finish progress.md file
2. **Project Understanding**: Deep comprehension di ogni component
3. **Setup Documentation**: Ensure installation process è crystal clear

### Next Session Preparation

- **Memory Bank**: Complete documentation structure per future sessions
- **Known Issues**: Document any technical debt or areas for improvement
- **Enhancement Opportunities**: Identify potential upgrades or extensions

## Active Development Notes

### Critical Configuration Points

```env
# Embedding dimensions MUST match model choice
# Lines to update in sql/schema.sql: 31, 67, 100
vector(1536)  # OpenAI text-embedding-3-small
vector(768)   # Ollama nomic-embed-text
```

### Performance Considerations

- **Knowledge Graph Building**: Può richiedere 30+ minutes per full document set
- **Token Limits**: Large chunks automatically truncated per Graphiti constraints
- **Batch Processing**: Optimized per avoid API rate limits

### User Experience Features

- **CLI Transparency**: Real-time tool usage visibility
- **Streaming Responses**: Server-Sent Events per immediate feedback
- **Session Management**: Persistent conversation context
- **Error Recovery**: Graceful handling di API failures

## Development Environment Status

### Working Setup

- **Python 3.11+**: ✅ Confirmed compatible
- **Dependencies**: ✅ All installed via requirements.txt
- **Database Schema**: ✅ PostgreSQL con pgvector ready
- **Neo4j**: ✅ Available via multiple setup options
- **Testing**: ✅ 58/58 tests passing con proper mocking

### Key Files Understood

- **Agent Core**: `agent/agent.py`, `agent/tools.py`, `agent/prompts.py`
- **Database**: `sql/schema.sql`, `agent/db_utils.py`, `agent/graph_utils.py`
- **Ingestion**: `ingestion/ingest.py`, `ingestion/chunker.py`, `ingestion/graph_builder.py`
- **API**: `agent/api.py`, `cli.py`
- **Config**: `requirements.txt`, `.env` setup

### Architecture Understanding

- **Data Flow**: Documents → Chunking → Embeddings → PostgreSQL + Neo4j → Agent Tools → User
- **Tool Selection**: Agent intelligently sceglie vector vs graph vs hybrid based on query type
- **Streaming**: Real-time responses con tool transparency per user understanding
