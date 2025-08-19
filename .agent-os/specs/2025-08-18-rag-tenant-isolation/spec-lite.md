# Spec Summary (Lite)

Implementare isolamento tenant nelle funzioni RAG `match_chunks` e `hybrid_search` sostituendo fallback legacy con stored procedures multi-tenant esistenti. Garantire che ogni tenant acceda solo ai propri chunks eliminando data leaks, con validazione tenant_id e error handling appropriato per stored procedure failures.