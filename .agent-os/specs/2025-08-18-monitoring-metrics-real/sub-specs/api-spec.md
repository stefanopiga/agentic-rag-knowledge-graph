# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-18-monitoring-metrics-real/spec.md

## Endpoints

### Enhanced Health Endpoint

**GET /health**

**Purpose:** Health check con metriche reali del sistema
**Response Format:** JSON con metriche calcolate accurate
**Enhanced Response Schema:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2025-08-18T10:30:00Z",
  "databases": {
    "postgresql": {"status": "connected", "active_connections": 3, "pool_size": 10},
    "neo4j": {"status": "connected", "active_sessions": 1, "pool_size": 5},
    "redis": {"status": "connected", "active_connections": 2}
  },
  "metrics": {
    "active_sessions": 15,           // COUNT(*) FROM sessions WHERE expires_at > NOW()
    "total_queries_today": 1247,    // Counter dalle metrics Prometheus
    "avg_response_time": 0.245,     // Media da Summary metric (ms)
    "cache_hit_rate": 0.87,         // cache_hits / (cache_hits + cache_misses)
    "memory_usage_mb": 156.3,       // psutil.Process().memory_info().rss / 1024 / 1024
    "cpu_usage_percent": 12.5       // psutil.Process().cpu_percent()
  },
  "version": "0.1.0",
  "uptime_seconds": 86420          // time.time() - app_start_time
}
```

## Controllers

### Enhanced Monitoring Functions (agent/monitoring.py)

**Updated Function:**

```python
def update_connection_metrics() -> None
```

**Purpose:** Aggiornare Prometheus metrics con valori reali da connection pools
**Implementation:**
- PostgreSQL: `db_connections_active.labels(database_type="postgresql").set(pg_pool.get_size() - pg_pool.get_idle_size())`
- Neo4j: `db_connections_active.labels(database_type="neo4j").set(neo4j_driver._pool.in_use_connection_count)`
- Redis: `db_connections_active.labels(database_type="redis").set(redis_pool.created_connections - redis_pool.available_connections)`
**Errors:** ConnectionError se pool non disponibili, log warning e skip update

**New Function:**

```python
async def get_system_metrics() -> Dict[str, Any]
```

**Purpose:** Calcolare metriche sistema per health endpoint
**Response:** Dict con active_sessions, total_queries_today, avg_response_time, cache_hit_rate, memory_usage, cpu_usage
**Implementation:**
- Query database per active sessions count
- Recuperare counter values da Prometheus metrics
- Calcolare averages da Summary/Histogram metrics
- Utilizzare psutil per system resource usage
**Errors:** DatabaseError, psutil.Error con fallback values

**New Decorator:**

```python
def monitor_performance(operation_name: str)
```

**Purpose:** Decorator per timing e error tracking delle operazioni
**Usage:** `@monitor_performance("rag_search")` su funzioni critiche
**Implementation:**
- Incrementare operation counter
- Misurare execution time con Summary metric
- Tracciare errors con error counter
- Log performance warnings se tempo > threshold

## Prometheus Metrics Extensions

**New Metrics:**

```python
# Response time tracking
operation_duration = Summary('operation_duration_seconds', 'Time spent on operations', ['operation_name'])

# Error rate tracking  
operation_errors = Counter('operation_errors_total', 'Total operation errors', ['operation_name', 'error_type'])

# Cache performance
cache_operations = Counter('cache_operations_total', 'Cache operations', ['operation_type'])

# System resource usage
system_memory_usage = Gauge('system_memory_usage_bytes', 'Process memory usage')
system_cpu_usage = Gauge('system_cpu_usage_percent', 'Process CPU usage percentage')
```