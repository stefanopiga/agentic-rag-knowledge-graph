# Spec Requirements Document

> Spec: Monitoring Metrics Real Values Implementation
> Created: 2025-08-18
> Status: Planning

## Overview

Sostituire i placeholder con valori calcolati reali nel sistema di monitoring per fornire metriche accurate su performance, usage e health del sistema. Questo abilita monitoring operativo efficace e debugging di performance issues attraverso metriche Prometheus precise e health checks informativi.

## User Stories

### Story 1: Database Connection Monitoring Reale

Come operations engineer, voglio vedere il numero reale di connessioni attive per PostgreSQL, Neo4j e Redis invece di valori fissi, così che possa monitorare l'utilizzo delle risorse database e identificare connection leaks o bottlenecks.

Il sistema deve interrogare i connection pools esistenti e restituire count accurate delle connessioni attive, idle e totali per ogni database type.

### Story 2: Health Check Informativo

Come sviluppatore/ops, voglio che l'endpoint /health restituisca metriche calcolate reali (sessioni attive, query giornaliere, tempi di risposta, cache hit rate) invece di placeholder strings, così che possa valutare rapidamente lo stato operativo del sistema.

Il sistema deve calcolare metriche da database queries, session storage, e performance counters per fornire health status accurato.

### Story 3: Performance Metrics Accurate

Come system administrator, voglio che le metriche Prometheus riflettano performance reali del sistema (query response times, cache efficiency, error rates), così che possa configurare alerting appropriato e identificare degradation trends.

Il sistema deve implementare timing measurements, error counting, e cache statistics per alimentare dashboard e alerting systems.

## Spec Scope

1. **Database Connection Metrics** - Sostituire valori fissi in `update_connection_metrics` con query reali ai connection pools
2. **Health Endpoint Enhancement** - Calcolare metriche reali per active_sessions, total_queries_today, avg_response_time, cache_hit_rate, uptime_seconds
3. **Performance Instrumentation** - Aggiungere timing e counting measurements alle operazioni critiche (RAG queries, DB operations)
4. **Cache Statistics** - Implementare tracking di cache hits/misses se caching è abilitato
5. **Error Rate Monitoring** - Aggiungere error counting e rate calculation per endpoints principali

## Out of Scope

- Implementazione nuovi monitoring backends oltre Prometheus
- Advanced analytics o machine learning su metrics
- Custom dashboard creation (solo metric exposure)
- Historical metric storage oltre Prometheus retention
- Real-time alerting configuration (solo metric exposure)
- Detailed profiling o APM integration

## Expected Deliverable

1. Funzione `update_connection_metrics` interroga connection pools reali e aggiorna gauge Prometheus con valori accurate
2. Endpoint /health calcola e restituisce metriche reali invece di placeholder strings
3. Sistema raccoglie timing metrics per operazioni critiche e le espone via Prometheus per monitoring operativo