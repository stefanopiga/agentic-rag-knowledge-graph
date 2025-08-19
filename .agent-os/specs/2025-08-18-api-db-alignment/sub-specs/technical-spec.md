# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-18-api-db-alignment/spec.md

## Technical Requirements

- **Parameter Consistency**: Aggiornare signatures di `create_session(tenant_id, user_id, metadata, timeout_minutes, title)`, `get_session(session_id, tenant_id)`, `add_message(session_id, tenant_id, role, content, metadata)`, `get_session_messages(session_id, tenant_id, limit)`
- **SQL Query Updates**: Modificare INSERT in create_session per includere tenant_id, aggiungere WHERE tenant_id = $n ai filtri in get_session e get_session_messages
- **RAG Function Alignment**: Aggiornare `match_chunks` e `hybrid_search` per chiamare stored procedures multi-tenant con p_tenant_id come primo parametro
- **Error Handling**: Aggiungere validazione UUID per tenant_id, raise ValueError per tenant_id malformati o mancanti
- **Backward Compatibility**: Mantenere fallback per chiamate senza tenant_id in ambiente development (usando DEV_TENANT_UUID)
- **Type Safety**: Aggiungere type hints UUID per tenant_id parameters, importare UUID da typing
- **Database Connection**: Utilizzare connection pool esistente, nessuna modifica al connection management
- **Logging**: Aggiungere log statements per operazioni tenant-aware per debugging multi-tenant