# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-18-monitoring-metrics-real/spec.md

## Technical Requirements

- **Connection Pool Monitoring**: Interrogare asyncpg connection pool per PostgreSQL (.get_size(), .get_idle_size()), neo4j driver session pool, redis connection pool stats
- **Database Query Metrics**: Implementare COUNT queries per active sessions da DB, total queries today da logs/counters, calcolare response times da timing decorators
- **Performance Instrumentation**: Aggiungere @timer decorators alle funzioni critiche (RAG search, DB operations), utilizzare prometheus_client Summary/Histogram metrics
- **Cache Statistics**: Implementare cache hit/miss tracking se Redis cache abilitato, calcolare hit_rate = hits/(hits+misses)
- **Uptime Calculation**: Tracciare application start time, calcolare uptime = current_time - start_time in seconds
- **Error Rate Monitoring**: Aggiungere error counters con labels per endpoint/operation, calcolare error_rate per time windows
- **Memory/Resource Usage**: Utilizzare psutil per memory usage, CPU usage del processo Python
- **Thread Safety**: Assicurare che metric updates siano thread-safe, utilizzare atomic operations per counters
- **Performance Impact**: Minimizzare overhead di monitoring, utilizzare sampling per expensive metrics se necessario