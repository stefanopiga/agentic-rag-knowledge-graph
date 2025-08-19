# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-18-api-db-alignment/spec.md

## Endpoints

Nessuna modifica agli endpoints REST. Le modifiche sono limitate alle funzioni interne del database layer.

## Controllers

### Database Utils Functions (agent/db_utils.py)

**Updated Function Signatures:**

```python
async def create_session(
    tenant_id: UUID,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timeout_minutes: Optional[int] = None,
    title: str = "New Chat"
) -> str
```

**Purpose:** Creare sessione con tenant isolation
**Parameters:** tenant_id (UUID, required), user_id, metadata, timeout_minutes, title
**Response:** session_id (str)
**Errors:** ValueError per tenant_id invalido, DatabaseError per fallimenti INSERT

```python
async def get_session(session_id: str, tenant_id: UUID) -> Optional[Dict[str, Any]]
```

**Purpose:** Recuperare sessione specifica per tenant
**Parameters:** session_id (str), tenant_id (UUID)
**Response:** session dict o None se non trovata
**Errors:** ValueError per parametri invalidi

```python
async def add_message(
    session_id: str,
    tenant_id: UUID,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str
```

**Purpose:** Aggiungere messaggio con tenant isolation
**Parameters:** session_id, tenant_id, role, content, metadata
**Response:** message_id (str)
**Errors:** ValueError per role invalido o tenant_id malformato

```python
async def get_session_messages(
    session_id: str,
    tenant_id: UUID,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]
```

**Purpose:** Recuperare messaggi sessione per tenant specifico
**Parameters:** session_id, tenant_id, limit
**Response:** lista di message dict
**Errors:** ValueError per parametri invalidi

```python
async def match_chunks(
    tenant_id: UUID,
    embedding: List[float],
    limit: int = 10
) -> List[Dict[str, Any]]
```

**Purpose:** Semantic search con tenant isolation
**Parameters:** tenant_id, embedding vector, limit
**Response:** lista di chunk matches
**Errors:** DatabaseError per stored procedure failures

```python
async def hybrid_search(
    tenant_id: UUID,
    embedding: List[float],
    query_text: str,
    limit: int = 10,
    text_weight: float = 0.3
) -> List[Dict[str, Any]]
```

**Purpose:** Hybrid search con tenant isolation
**Parameters:** tenant_id, embedding, query_text, limit, text_weight
**Response:** lista di search results
**Errors:** DatabaseError per stored procedure failures