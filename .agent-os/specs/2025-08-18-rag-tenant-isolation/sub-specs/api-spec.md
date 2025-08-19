# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-18-rag-tenant-isolation/spec.md

## Endpoints

Nessuna modifica agli endpoints REST. Le modifiche sono interne alle funzioni RAG del database layer.

## Controllers

### RAG Database Functions (agent/db_utils.py)

**Updated Function Signatures:**

```python
async def match_chunks(
    tenant_id: UUID,
    embedding: List[float],
    limit: int = 10
) -> List[Dict[str, Any]]
```

**Purpose:** Semantic similarity search con isolamento tenant completo
**Parameters:** 
- tenant_id (UUID, required): Identificatore tenant per isolamento dati
- embedding (List[float], required): Vector embedding per similarity search  
- limit (int, default=10): Numero massimo risultati da restituire
**Response:** Lista di chunk dict con score, content, metadata limitati al tenant
**Errors:** 
- ValueError per tenant_id malformato o embedding invalido
- asyncpg.PostgreSQLError per stored procedure failures
- RuntimeWarning se stored procedure non disponibile

```python
async def hybrid_search(
    tenant_id: UUID,
    embedding: List[float],
    query_text: str,
    limit: int = 10,
    text_weight: float = 0.3
) -> List[Dict[str, Any]]
```

**Purpose:** Hybrid semantic + text search con tenant isolation
**Parameters:**
- tenant_id (UUID, required): Identificatore tenant per isolamento dati
- embedding (List[float], required): Vector embedding per component semantico
- query_text (str, required): Testo query per component full-text search
- limit (int, default=10): Numero massimo risultati
- text_weight (float, default=0.3): Peso component text vs semantic (0.0-1.0)
**Response:** Lista di risultati ranked combinando semantic e text similarity per tenant
**Errors:**
- ValueError per parametri invalidi (tenant_id, text_weight fuori range)
- asyncpg.PostgreSQLError per stored procedure failures  
- RuntimeWarning se stored procedure non disponibile

## Internal Implementation Details

**Stored Procedure Calls:**

```sql
-- match_chunks implementation
SELECT * FROM match_chunks($1::UUID, $2::vector(1536), $3::INT)

-- hybrid_search implementation  
SELECT * FROM hybrid_search($1::UUID, $2::vector(1536), $3::TEXT, $4::INT, $5::FLOAT)
```

**Error Handling Pattern:**
```python
try:
    # Validate tenant_id
    tenant_uuid = UUID(str(tenant_id))
    # Convert embedding to PostgreSQL vector format
    embedding_vector = "[" + ",".join(map(str, embedding)) + "]"
    # Call stored procedure
    results = await conn.fetch(query, tenant_uuid, embedding_vector, ...)
    return [dict(row) for row in results]
except ValueError as e:
    logger.error(f"Invalid parameters for RAG search: {e}")
    raise
except asyncpg.PostgreSQLError as e:
    logger.error(f"Database error in RAG search: {e}")
    raise
```