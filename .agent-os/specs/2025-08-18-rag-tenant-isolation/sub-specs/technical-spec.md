# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-18-rag-tenant-isolation/spec.md

## Technical Requirements

- **Stored Procedure Integration**: Sostituire chiamate dirette con stored procedures `match_chunks(p_tenant_id UUID, query_embedding vector(1536), match_count INT)` e `hybrid_search(p_tenant_id UUID, query_embedding vector(1536), query_text TEXT, match_count INT, text_weight FLOAT)`
- **Parameter Validation**: Implementare validazione UUID per tenant_id usando `UUID(str(tenant_id))` con try/catch per ValueError
- **Embedding Format**: Convertire embedding List[float] in formato vector compatibile con PostgreSQL usando `"[" + ",".join(map(str, embedding)) + "]"`
- **Connection Management**: Utilizzare pool di connessioni esistente senza modifiche al connection handling
- **Error Handling**: Gestire asyncpg.PostgreSQLError per stored procedure failures, log errori senza esporre dettagli tenant
- **Type Safety**: Aggiungere type hints UUID per tenant_id, List[float] per embeddings, restituire List[Dict[str, Any]]
- **Fallback Strategy**: Se stored procedure non disponibile, restituire lista vuota con warning log invece di fallback insicuro
- **Performance**: Mantenere existing query timeouts, non aggiungere overhead significativo alle operazioni RAG