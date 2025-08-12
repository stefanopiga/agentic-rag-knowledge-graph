# Cloud Shared Architecture - Environment Setup

Questo documento definisce le variabili obbligatorie per il profilo production.

## Variabili obbligatorie

- APP_ENV=production
- DATABASE_URL (Neon, con `sslmode=require`)
- NEO4J_URI (Aura, `neo4j+s://...`)
- NEO4J_USER
- NEO4J_PASSWORD
- ENABLE_METRICS=true
- VECTOR_DIMENSION=1536
- EMBEDDINGS_OFFLINE=1
- CORS_ALLOWED_ORIGINS (lista domini frontend)

## Note

- Non lasciare `CORS_ALLOWED_ORIGINS` vuoto in produzione.
- Impostare le chiavi LLM/Embedding via secrets di runtime.
- Redis consigliato per caching; configurare `REDIS_URL`.
