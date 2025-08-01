# System Patterns - Agentic RAG with Knowledge Graph

## Architecture Pattern: Hybrid RAG + Knowledge Graph

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer                             │
│  ┌─────────────────┐        ┌────────────────────┐     │
│  │   FastAPI       │        │   Streaming SSE    │     │
│  │   Endpoints     │        │   Responses        │     │
│  └────────┬────────┘        └────────────────────┘     │
├───────────┴──────────────────────────────────────────────┤
│                    Agent Layer                           │
│  ┌─────────────────┐        ┌────────────────────┐     │
│  │  Pydantic AI    │        │   Agent Tools      │     │
│  │    Agent        │◄──────►│  - Vector Search   │     │
│  └─────────────────┘        │  - Graph Search    │     │
│                              │  - Hybrid Search   │     │
├──────────────────────────────┴────────────────────┤     │
│                  Storage Layer                           │
│  ┌─────────────────┐        ┌────────────────────┐     │
│  │   PostgreSQL    │        │      Neo4j         │     │
│  │   + pgvector    │        │   (via Graphiti)   │     │
│  └─────────────────┘        └────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Core Design Patterns

### 1. Agent Tool Selection Pattern

```python
# System prompt controls tool selection logic
SYSTEM_PROMPT = """
Use vector search for semantic similarity queries
Use knowledge graph for relationship exploration
Use hybrid search for complex analysis
"""
```

### 2. Dependency Injection Pattern

```python
@dataclass
class AgentDependencies:
    session_id: str
    user_id: Optional[str] = None
    search_preferences: Dict[str, Any] = None
```

### 3. Provider Abstraction Pattern

```python
# Flexible LLM providers
LLM_PROVIDER=openai|ollama|openrouter|gemini
# Automatic client initialization based on provider
```

### 4. Database Function Pattern

```sql
-- PostgreSQL stored functions for complex queries
CREATE OR REPLACE FUNCTION match_chunks(query_embedding vector(1536))
CREATE OR REPLACE FUNCTION hybrid_search(query_embedding, query_text)
```

## Key Component Relationships

### Ingestion Pipeline

1. **Document Reader** → Markdown files from `documents/` or `big_tech_docs/`
2. **Semantic Chunker** → LLM-guided intelligent splitting vs simple rule-based
3. **Embedder** → Flexible provider (OpenAI, Ollama) per chunk embeddings
4. **Graph Builder** → Entity extraction + relationship detection via Graphiti
5. **Database Storage** → PostgreSQL (vector) + Neo4j (graph) parallel storage

### Agent Execution Flow

1. **Query Analysis** → Agent determines optimal tool selection
2. **Tool Execution** → Vector/Graph/Hybrid search execution
3. **Result Merging** → Intelligent combination di multiple sources
4. **Response Generation** → Streaming response con tool transparency

### API Architecture

1. **FastAPI Server** → `/chat`, `/chat/stream`, `/health` endpoints
2. **Session Management** → PostgreSQL-based conversation context
3. **Streaming Protocol** → Server-Sent Events per real-time responses
4. **Error Handling** → Graceful degradation e comprehensive logging

## Data Flow Patterns

### Embedding Storage Pattern

```sql
-- PostgreSQL vector storage
embedding vector(1536)  -- OpenAI text-embedding-3-small default
-- JSON string format: '[1.0,2.0,3.0]' (no spaces)
```

### Graph Episode Pattern

```python
# Graphiti temporal episodes
episode_id = f"{document_source}_{chunk_index}_{timestamp}"
# Automatic entity/relationship extraction per episode
```

### Search Orchestration Pattern

```python
# Tool selection based on query analysis
vector_search()     # Semantic similarity
graph_search()      # Relationship traversal
hybrid_search()     # Combined scoring
```

## Error Handling Patterns

### Database Resilience

- Connection pooling con asyncpg
- Transaction management per data consistency
- Graceful fallback se graph building fails

### LLM Provider Fallback

- Environment-based provider switching
- Retry logic con exponential backoff
- Error logging senza system crash

### Ingestion Robustness

- Single document failure non blocca entire pipeline
- Progress tracking e resumable operations
- Size limits per evitare Graphiti token limits

## Testing Patterns

- **Unit Tests**: Every component isolated con mocked dependencies
- **Integration Tests**: End-to-end workflows con test databases
- **Fixture Strategy**: Reusable test data e database setup
- **Coverage Target**: >80% (currently 58/58 tests passing)
