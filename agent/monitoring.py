"""
Performance monitoring and metrics for FisioRAG application.
Provides Prometheus metrics, structured logging, and custom business metrics.
"""

import time
import asyncio
import logging
import structlog
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime
import os
import psutil

from prometheus_client import (
    Counter, Histogram, Gauge, Info, 
    CollectorRegistry, multiprocess, generate_latest
)
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from fastapi import FastAPI, Request, Response
try:
    # FastAPI >=0.115 moved BaseHTTPMiddleware import path in Starlette
    from starlette.middleware.base import BaseHTTPMiddleware
except Exception:  # pragma: no cover
    from fastapi.middleware.base import BaseHTTPMiddleware

# Initialize structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if os.getenv("APP_ENV") == "production" else structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# ==============================================================================
# PROMETHEUS METRICS DEFINITIONS
# ==============================================================================

# Application Info
fisiorag_info = Info(
    'fisiorag_application_info',
    'Information about the FisioRAG application',
    ['version', 'environment', 'startup_time']
)

# Business Metrics - RAG Operations
rag_queries_total = Counter(
    'fisiorag_rag_queries_total',
    'Total number of RAG queries processed',
    ['query_type', 'status', 'tenant_id']
)

rag_query_duration = Histogram(
    'fisiorag_rag_query_duration_seconds',
    'Time spent processing RAG queries',
    ['query_type', 'tenant_id'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)

# Vector Search Metrics
vector_search_total = Counter(
    'fisiorag_vector_search_total',
    'Total vector similarity searches performed',
    ['status', 'tenant_id']
)

vector_search_duration = Histogram(
    'fisiorag_vector_search_duration_seconds',
    'Duration of vector similarity searches',
    ['tenant_id'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

vector_search_results = Histogram(
    'fisiorag_vector_search_results_count',
    'Number of results returned by vector searches',
    ['tenant_id'],
    buckets=[1, 5, 10, 20, 50, 100, 200]
)

# Knowledge Graph Metrics
graph_queries_total = Counter(
    'fisiorag_graph_queries_total',
    'Total knowledge graph queries executed',
    ['query_type', 'status', 'tenant_id']
)

graph_query_duration = Histogram(
    'fisiorag_graph_query_duration_seconds',
    'Duration of knowledge graph queries',
    ['query_type', 'tenant_id'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# LLM API Metrics
llm_requests_total = Counter(
    'fisiorag_llm_requests_total',
    'Total LLM API requests made',
    ['provider', 'model', 'status', 'tenant_id']
)

llm_request_duration = Histogram(
    'fisiorag_llm_request_duration_seconds',
    'Duration of LLM API requests',
    ['provider', 'model', 'tenant_id'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0]
)

llm_tokens_total = Counter(
    'fisiorag_llm_tokens_total',
    'Total tokens processed by LLM',
    ['provider', 'model', 'token_type', 'tenant_id']  # token_type: input, output
)

# Database Connection Metrics
db_connections_active = Gauge(
    'fisiorag_db_connections_active',
    'Number of active database connections',
    ['database_type']  # postgresql, neo4j, redis
)

db_query_duration = Histogram(
    'fisiorag_db_query_duration_seconds',
    'Duration of database queries',
    ['database_type', 'operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

db_queries_total = Counter(
    'fisiorag_db_queries_total',
    'Total database queries executed',
    ['database_type', 'operation', 'status']
)

# Session Management Metrics
sessions_active = Gauge(
    'fisiorag_sessions_active',
    'Number of currently active chat sessions',
    ['tenant_id']
)

sessions_total = Counter(
    'fisiorag_sessions_total',
    'Total chat sessions created',
    ['tenant_id']
)

session_duration = Histogram(
    'fisiorag_session_duration_seconds',
    'Duration of chat sessions',
    ['tenant_id'],
    buckets=[60, 300, 600, 1800, 3600, 7200, 14400]  # 1min to 4h
)

# Document Processing Metrics
documents_processed_total = Counter(
    'fisiorag_documents_processed_total',
    'Total documents processed for ingestion',
    ['document_type', 'status', 'tenant_id']  # status: success, failed
)

document_processing_duration = Histogram(
    'fisiorag_document_processing_duration_seconds',
    'Time spent processing documents',
    ['document_type', 'tenant_id'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1200]
)

documents_ingested_size_bytes = Histogram(
    'fisiorag_documents_ingested_size_bytes',
    'Size of ingested documents in bytes',
    ['document_type', 'tenant_id'],
    buckets=[1000, 10000, 100000, 1000000, 10000000, 100000000]
)

# Cache Metrics
cache_operations_total = Counter(
    'fisiorag_cache_operations_total',
    'Total cache operations',
    ['operation', 'result']  # operation: get, set, delete; result: hit, miss, success, error
)

cache_operation_duration = Histogram(
    'fisiorag_cache_operation_duration_seconds',
    'Duration of cache operations',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5]
)

# Performance Monitoring Metrics
operation_duration = Histogram(
    'fisiorag_operation_duration_seconds',
    'Time spent on operations',
    ['operation_name'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

operation_errors = Counter(
    'fisiorag_operation_errors_total',
    'Total operation errors',
    ['operation_name', 'error_type']
)

operation_total = Counter(
    'fisiorag_operation_total',
    'Total operations executed',
    ['operation_name', 'status']  # status: success, error
)

# Knowledge Graph Node/Relationship Metrics
graph_nodes_total = Gauge(
    'fisiorag_graph_nodes_total',
    'Total nodes in the knowledge graph',
    ['node_type', 'tenant_id']
)

graph_relationships_total = Gauge(
    'fisiorag_graph_relationships_total',
    'Total relationships in the knowledge graph',
    ['relationship_type', 'tenant_id']
)

# Medical Domain Specific Metrics
medical_entities_extracted_total = Counter(
    'fisiorag_medical_entities_extracted_total',
    'Total medical entities extracted',
    ['entity_type', 'tenant_id']  # anatomical, pathological, treatment, device
)

medical_concepts_linked_total = Counter(
    'fisiorag_medical_concepts_linked_total',
    'Total medical concepts linked in knowledge graph',
    ['concept_type', 'tenant_id']
)

# ==============================================================================
# MONITORING DECORATORS AND UTILITIES
# ==============================================================================

def track_rag_query(query_type: str = "hybrid", tenant_id: str = "default"):
    """Decorator to track RAG query metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error("RAG query failed", error=str(e), query_type=query_type)
                raise
            finally:
                duration = time.time() - start_time
                rag_queries_total.labels(
                    query_type=query_type,
                    status=status,
                    tenant_id=tenant_id
                ).inc()
                rag_query_duration.labels(
                    query_type=query_type,
                    tenant_id=tenant_id
                ).observe(duration)
                
                logger.info(
                    "RAG query completed",
                    query_type=query_type,
                    status=status,
                    duration=duration,
                    tenant_id=tenant_id
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error("RAG query failed", error=str(e), query_type=query_type)
                raise
            finally:
                duration = time.time() - start_time
                rag_queries_total.labels(
                    query_type=query_type,
                    status=status,
                    tenant_id=tenant_id
                ).inc()
                rag_query_duration.labels(
                    query_type=query_type,
                    tenant_id=tenant_id
                ).observe(duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def track_vector_search(tenant_id: str = "default"):
    """Decorator to track vector search metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            result_count = 0
            
            try:
                result = await func(*args, **kwargs)
                result_count = len(result) if isinstance(result, list) else 1
                return result
            except Exception as e:
                status = "error"
                logger.error("Vector search failed", error=str(e))
                raise
            finally:
                duration = time.time() - start_time
                vector_search_total.labels(status=status, tenant_id=tenant_id).inc()
                vector_search_duration.labels(tenant_id=tenant_id).observe(duration)
                if status == "success":
                    vector_search_results.labels(tenant_id=tenant_id).observe(result_count)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else func
    return decorator


def track_graph_query(query_type: str = "cypher", tenant_id: str = "default"):
    """Decorator to track knowledge graph query metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error("Graph query failed", error=str(e), query_type=query_type)
                raise
            finally:
                duration = time.time() - start_time
                graph_queries_total.labels(
                    query_type=query_type,
                    status=status,
                    tenant_id=tenant_id
                ).inc()
                graph_query_duration.labels(
                    query_type=query_type,
                    tenant_id=tenant_id
                ).observe(duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else func
    return decorator


def track_llm_request(provider: str = "openai", model: str = "gpt-4o-mini", tenant_id: str = "default"):
    """Decorator to track LLM API request metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                
                # Try to extract token usage if available
                if hasattr(result, 'usage'):
                    usage = result.usage
                    if hasattr(usage, 'prompt_tokens'):
                        llm_tokens_total.labels(
                            provider=provider,
                            model=model,
                            token_type="input",
                            tenant_id=tenant_id
                        ).inc(usage.prompt_tokens)
                    if hasattr(usage, 'completion_tokens'):
                        llm_tokens_total.labels(
                            provider=provider,
                            model=model,
                            token_type="output",
                            tenant_id=tenant_id
                        ).inc(usage.completion_tokens)
                
                return result
            except Exception as e:
                status = "error"
                logger.error("LLM request failed", error=str(e), provider=provider, model=model)
                raise
            finally:
                duration = time.time() - start_time
                llm_requests_total.labels(
                    provider=provider,
                    model=model,
                    status=status,
                    tenant_id=tenant_id
                ).inc()
                llm_request_duration.labels(
                    provider=provider,
                    model=model,
                    tenant_id=tenant_id
                ).observe(duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else func
    return decorator


def track_db_operation(database_type: str, operation: str):
    """Decorator to track database operation metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error("Database operation failed", 
                           error=str(e), 
                           database_type=database_type, 
                           operation=operation)
                raise
            finally:
                duration = time.time() - start_time
                db_queries_total.labels(
                    database_type=database_type,
                    operation=operation,
                    status=status
                ).inc()
                db_query_duration.labels(
                    database_type=database_type,
                    operation=operation
                ).observe(duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else func
    return decorator


def monitor_performance(operation_name: str, warning_threshold: float = 1.0):
    """
    Decorator for timing operations and error tracking with performance monitoring.
    
    Args:
        operation_name: Name of the operation for metrics labeling
        warning_threshold: Duration in seconds above which to log warning (default: 1.0s)
    
    Returns:
        Decorated function with performance monitoring
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            error_type = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                error_type = type(e).__name__
                
                # Record error metrics
                operation_errors.labels(
                    operation_name=operation_name,
                    error_type=error_type
                ).inc()
                
                logger.error(
                    "Operation failed",
                    operation=operation_name,
                    error=str(e),
                    error_type=error_type
                )
                raise
            finally:
                duration = time.time() - start_time
                
                # Record operation metrics
                operation_total.labels(
                    operation_name=operation_name,
                    status=status
                ).inc()
                
                operation_duration.labels(
                    operation_name=operation_name
                ).observe(duration)
                
                # Log performance info/warning
                if duration > warning_threshold:
                    logger.warning(
                        "Slow operation detected",
                        operation=operation_name,
                        duration=duration,
                        threshold=warning_threshold,
                        status=status
                    )
                else:
                    logger.info(
                        "Operation completed",
                        operation=operation_name,
                        duration=duration,
                        status=status
                    )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            error_type = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                error_type = type(e).__name__
                
                # Record error metrics
                operation_errors.labels(
                    operation_name=operation_name,
                    error_type=error_type
                ).inc()
                
                logger.error(
                    "Operation failed",
                    operation=operation_name,
                    error=str(e),
                    error_type=error_type
                )
                raise
            finally:
                duration = time.time() - start_time
                
                # Record operation metrics
                operation_total.labels(
                    operation_name=operation_name,
                    status=status
                ).inc()
                
                operation_duration.labels(
                    operation_name=operation_name
                ).observe(duration)
                
                # Log performance info/warning
                if duration > warning_threshold:
                    logger.warning(
                        "Slow operation detected",
                        operation=operation_name,
                        duration=duration,
                        threshold=warning_threshold,
                        status=status
                    )
                else:
                    logger.info(
                        "Operation completed",
                        operation=operation_name,
                        duration=duration,
                        status=status
                    )
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# ==============================================================================
# MONITORING MIDDLEWARE
# ==============================================================================

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Custom middleware for additional monitoring capabilities."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request start
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        response = await call_next(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log request completion
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration=duration
        )
        
        return response


# ==============================================================================
# MONITORING INITIALIZATION
# ==============================================================================

def setup_monitoring(app: FastAPI, enable_metrics: bool = True) -> Optional[Instrumentator]:
    """
    Setup comprehensive monitoring for FastAPI application.
    
    Args:
        app: FastAPI application instance
        enable_metrics: Whether to enable Prometheus metrics
    
    Returns:
        Instrumentator instance if metrics enabled, None otherwise
    """
    if not enable_metrics:
        logger.info("Metrics collection disabled")
        return None
    
    # Initialize FastAPI instrumentator
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="fisiorag_requests_inprogress",
        inprogress_labels=True,
    )
    
    # Add standard metrics
    instrumentator.add(
        metrics.request_size(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
            metric_name="fisiorag_request_size_bytes"
        )
    ).add(
        metrics.response_size(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
            metric_name="fisiorag_response_size_bytes"
        )
    ).add(
        metrics.latency(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
            metric_name="fisiorag_request_duration_seconds"
        )
    ).add(
        metrics.requests(
            should_include_handler=True,
            should_include_method=True,
            should_include_status=True,
            metric_name="fisiorag_requests_total"
        )
    )
    
    # Instrument the app
    instrumentator.instrument(app)
    
    # Set application info
    try:
        fisiorag_info.info({
            'version': '0.1.0',
            'environment': os.getenv('APP_ENV', 'development'),
            'startup_time': datetime.now().isoformat()
        })
    except Exception:
        # Best-effort: skip Info if client incompatible
        pass
    
    logger.info("Monitoring setup completed", metrics_enabled=True)
    
    return instrumentator


def update_connection_metrics():
    """Update database connection metrics with real values from connection pools."""
    try:
        # Import global pool instances
        from .db_utils import db_pool
        from .graph_utils import graph_client  
        from .cache_manager import cache_manager
        
        # PostgreSQL connection metrics
        pg_active_connections = 0
        if db_pool.pool is not None:
            try:
                total_connections = db_pool.pool.get_size()
                idle_connections = db_pool.pool.get_idle_size()
                pg_active_connections = total_connections - idle_connections
            except Exception as e:
                logger.warning(f"Failed to get PostgreSQL pool stats: {e}")
                pg_active_connections = 0
        else:
            logger.warning("PostgreSQL pool not initialized")
            
        db_connections_active.labels(database_type="postgresql").set(pg_active_connections)
        
        # Neo4j connection metrics
        neo4j_active_connections = 0
        if (graph_client._initialized and 
            graph_client.graphiti is not None and 
            hasattr(graph_client.graphiti, 'driver')):
            try:
                # Access Neo4j driver connection pool statistics
                driver = graph_client.graphiti.driver
                if hasattr(driver, '_pool') and hasattr(driver._pool, 'in_use'):
                    neo4j_active_connections = driver._pool.in_use
                else:
                    # Fallback: try to get active connections count
                    neo4j_active_connections = getattr(driver._pool, 'active_connections', 0)
            except Exception as e:
                logger.warning(f"Failed to get Neo4j pool stats: {e}")
                neo4j_active_connections = 0
        else:
            logger.warning("Neo4j client not initialized or unavailable")
            
        db_connections_active.labels(database_type="neo4j").set(neo4j_active_connections)
        
        # Redis connection metrics
        redis_active_connections = 0
        if cache_manager.redis is not None:
            try:
                # For Redis metrics in sync context, use a simplified approach
                # since we can't reliably call async methods from sync context
                # Set default to 1 for active Redis connection
                redis_active_connections = 1  # Default for active Redis connection
            except Exception as e:
                logger.warning(f"Failed to get Redis connection stats: {e}")
                redis_active_connections = 0
        else:
            logger.warning("Redis cache manager not initialized")
            
        db_connections_active.labels(database_type="redis").set(redis_active_connections)
        
    except Exception as e:
        logger.error("Failed to update connection metrics", error=str(e))


async def update_knowledge_graph_metrics(tenant_id: str = "default"):
    """Update knowledge graph size metrics."""
    try:
        # These would query actual Neo4j for node/relationship counts
        # Placeholder implementation
        graph_nodes_total.labels(node_type="Document", tenant_id=tenant_id).set(1000)
        graph_nodes_total.labels(node_type="Entity", tenant_id=tenant_id).set(5000)
        graph_nodes_total.labels(node_type="Concept", tenant_id=tenant_id).set(2500)
        
        graph_relationships_total.labels(relationship_type="MENTIONS", tenant_id=tenant_id).set(15000)
        graph_relationships_total.labels(relationship_type="RELATES_TO", tenant_id=tenant_id).set(8000)
        graph_relationships_total.labels(relationship_type="IS_TYPE_OF", tenant_id=tenant_id).set(3000)
        
    except Exception as e:
        logger.error("Failed to update knowledge graph metrics", error=str(e))


# ==============================================================================
# SYSTEM METRICS COLLECTION
# ==============================================================================

async def get_system_metrics() -> Dict[str, Any]:
    """
    Calculate system metrics for health endpoint.
    
    Returns:
        Dict with active_sessions, total_queries_today, avg_response_time, 
        cache_hit_rate, memory_usage_mb, cpu_usage_percent
    """
    metrics = {
        'active_sessions': 0,
        'total_queries_today': 0,
        'avg_response_time': 0.0,
        'cache_hit_rate': 0.0,
        'memory_usage_mb': 0.0,
        'cpu_usage_percent': 0.0
    }
    
    try:
        # 2.3 - Implementare active sessions count da database query
        from .db_utils import db_pool
        
        if db_pool.pool is not None:
            try:
                async with db_pool.acquire() as conn:
                    # Query to count active sessions (assuming sessions table exists)
                    # Adjust query based on actual schema
                    result = await conn.fetchrow("""
                        SELECT COUNT(*) as count 
                        FROM sessions 
                        WHERE expires_at > NOW() OR expires_at IS NULL
                    """)
                    if result:
                        metrics['active_sessions'] = result['count']
            except Exception as e:
                logger.warning(f"Failed to get active sessions count: {e}")
        else:
            logger.warning("Database pool not initialized for session count")
            
    except Exception as e:
        logger.warning(f"Failed to access database for session metrics: {e}")
    
    try:
        # 2.4 - Implementare total queries today counter da Prometheus metrics
        # Get total RAG queries count (all time, as we don't have daily reset)
        if hasattr(rag_queries_total, '_value') and hasattr(rag_queries_total._value, '_value'):
            metrics['total_queries_today'] = rag_queries_total._value._value
        else:
            # Fallback: try to access metric value differently
            try:
                # Access metric samples to get current value
                samples = list(rag_queries_total.collect())[0].samples
                if samples:
                    metrics['total_queries_today'] = int(samples[0].value)
            except Exception:
                metrics['total_queries_today'] = 0
                
    except Exception as e:
        logger.warning(f"Failed to get query count metrics: {e}")
    
    try:
        # 2.5 - Calcolare average response time da Summary metrics  
        if (hasattr(rag_query_duration, '_sum') and hasattr(rag_query_duration, '_count') and
            hasattr(rag_query_duration._sum, '_value') and hasattr(rag_query_duration._count, '_value')):
            
            total_time = rag_query_duration._sum._value
            total_count = rag_query_duration._count._value
            
            if total_count > 0:
                metrics['avg_response_time'] = total_time / total_count
            else:
                metrics['avg_response_time'] = 0.0
        else:
            # Fallback: try to access metric samples
            try:
                samples = list(rag_query_duration.collect())[0].samples
                sum_value = 0
                count_value = 0
                
                for sample in samples:
                    if sample.name.endswith('_sum'):
                        sum_value = sample.value
                    elif sample.name.endswith('_count'):
                        count_value = sample.value
                        
                if count_value > 0:
                    metrics['avg_response_time'] = sum_value / count_value
                    
            except Exception:
                metrics['avg_response_time'] = 0.0
                
    except Exception as e:
        logger.warning(f"Failed to calculate average response time: {e}")
    
    try:
        # Calculate cache hit rate from cache operations metrics
        cache_hits = 0
        cache_misses = 0
        
        try:
            # Get cache hit metric
            hit_metric = cache_operations_total.labels(operation='get', result='hit')
            if hasattr(hit_metric, '_value') and hasattr(hit_metric._value, '_value'):
                cache_hits = hit_metric._value._value
                
            # Get cache miss metric  
            miss_metric = cache_operations_total.labels(operation='get', result='miss')
            if hasattr(miss_metric, '_value') and hasattr(miss_metric._value, '_value'):
                cache_misses = miss_metric._value._value
                
        except Exception:
            # Fallback: access through metric collection
            try:
                samples = list(cache_operations_total.collect())[0].samples
                for sample in samples:
                    labels = sample.labels
                    if labels.get('operation') == 'get':
                        if labels.get('result') == 'hit':
                            cache_hits = sample.value
                        elif labels.get('result') == 'miss':
                            cache_misses = sample.value
            except Exception:
                pass
        
        # Calculate hit rate
        total_cache_ops = cache_hits + cache_misses
        if total_cache_ops > 0:
            metrics['cache_hit_rate'] = cache_hits / total_cache_ops
        else:
            metrics['cache_hit_rate'] = 0.0
            
    except Exception as e:
        logger.warning(f"Failed to calculate cache hit rate: {e}")
    
    try:
        # 2.6 - Implementare memory e CPU usage tracking con psutil
        process = psutil.Process()
        
        # Memory usage in MB
        memory_info = process.memory_info()
        metrics['memory_usage_mb'] = memory_info.rss / 1024 / 1024
        
        # CPU usage percentage
        metrics['cpu_usage_percent'] = process.cpu_percent()
        
    except Exception as e:
        logger.warning(f"Failed to get system resource usage: {e}")
    
    return metrics


# ==============================================================================
# HEALTH CHECK ENHANCEMENTS
# ==============================================================================

async def get_connection_metrics() -> Dict[str, Any]:
    """Get real connection metrics from database pools."""
    connections = {}
    
    try:
        # PostgreSQL connection metrics
        from .db_utils import db_pool
        if db_pool.pool is not None:
            try:
                total_connections = db_pool.pool.get_size()
                idle_connections = db_pool.pool.get_idle_size()
                active_connections = total_connections - idle_connections
                connections["postgresql"] = {
                    "status": "connected",
                    "active_connections": active_connections,
                    "pool_size": total_connections
                }
            except Exception as e:
                logger.warning(f"Failed to get PostgreSQL metrics: {e}")
                connections["postgresql"] = {
                    "status": "error",
                    "active_connections": 0,
                    "pool_size": 0
                }
        else:
            connections["postgresql"] = {
                "status": "not_initialized",
                "active_connections": 0,
                "pool_size": 0
            }
    except Exception as e:
        logger.warning(f"Failed to access PostgreSQL pool: {e}")
        connections["postgresql"] = {
            "status": "error",
            "active_connections": 0,
            "pool_size": 0
        }
    
    try:
        # Neo4j connection metrics
        from .graph_utils import graph_client
        if (graph_client._initialized and 
            graph_client.graphiti is not None and 
            hasattr(graph_client.graphiti, 'driver')):
            try:
                driver = graph_client.graphiti.driver
                # Try to get active session count
                active_sessions = 0
                if hasattr(driver, '_pool'):
                    if hasattr(driver._pool, 'in_use'):
                        active_sessions = driver._pool.in_use
                    elif hasattr(driver._pool, 'active_connections'):
                        active_sessions = driver._pool.active_connections
                
                connections["neo4j"] = {
                    "status": "connected",
                    "active_sessions": active_sessions,
                    "pool_size": getattr(driver._pool, 'max_connection_pool_size', 5)
                }
            except Exception as e:
                logger.warning(f"Failed to get Neo4j metrics: {e}")
                connections["neo4j"] = {
                    "status": "error",
                    "active_sessions": 0,
                    "pool_size": 0
                }
        else:
            connections["neo4j"] = {
                "status": "not_initialized", 
                "active_sessions": 0,
                "pool_size": 0
            }
    except Exception as e:
        logger.warning(f"Failed to access Neo4j client: {e}")
        connections["neo4j"] = {
            "status": "error",
            "active_sessions": 0,
            "pool_size": 0
        }
    
    try:
        # Redis connection metrics
        from .cache_manager import cache_manager
        if cache_manager.redis is not None:
            try:
                connections["redis"] = {
                    "status": "connected",
                    "active_connections": 1  # Simplified: 1 if Redis is connected
                }
            except Exception as e:
                logger.warning(f"Failed to get Redis metrics: {e}")
                connections["redis"] = {
                    "status": "error",
                    "active_connections": 0
                }
        else:
            connections["redis"] = {
                "status": "not_initialized",
                "active_connections": 0
            }
    except Exception as e:
        logger.warning(f"Failed to access Redis cache: {e}")
        connections["redis"] = {
            "status": "error",
            "active_connections": 0
        }
    
    return connections


async def get_enhanced_health_status(app_start_time: float) -> Dict[str, Any]:
    """Get enhanced health status with real metrics and connection info."""
    try:
        # Get basic connection statuses
        from .db_utils import test_connection
        from .graph_utils import test_graph_connection
        from .cache_manager import cache_manager
        
        db_status = await test_connection()
        graph_status = await test_graph_connection() 
        cache_health = await cache_manager.health_check()
        cache_status = cache_health.get("status") == "healthy"
        
        # Determine overall status
        if db_status and graph_status and cache_status:
            status = "healthy"
        elif (db_status and graph_status) or (db_status and cache_status) or (graph_status and cache_status):
            status = "degraded"
        else:
            status = "unhealthy"
            
        # Get real metrics
        system_metrics = await get_system_metrics()
        connection_metrics = await get_connection_metrics()
        
        # Calculate uptime
        uptime_seconds = time.time() - app_start_time
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "databases": connection_metrics,
            "metrics": system_metrics,
            "version": "0.1.0",
            "uptime_seconds": uptime_seconds
        }
        
    except Exception as e:
        logger.error(f"Failed to get enhanced health status: {e}")
        # Fallback to basic status
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "databases": {},
            "metrics": {
                "active_sessions": 0,
                "total_queries_today": 0,
                "avg_response_time": 0.0,
                "cache_hit_rate": 0.0,
                "memory_usage_mb": 0.0,
                "cpu_usage_percent": 0.0
            },
            "version": "0.1.0",
            "uptime_seconds": 0.0
        }


async def get_detailed_health_status() -> Dict[str, Any]:
    """Get detailed health status including metrics (legacy format)."""
    system_metrics = await get_system_metrics()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "healthy",
            "database": "healthy", 
            "graph_database": "healthy",
            "cache": "healthy",
            "llm_provider": "healthy"
        },
        "metrics": system_metrics,
        "version": "0.1.0",
        "uptime_seconds": time.time() - getattr(get_detailed_health_status, '_start_time', time.time())
    }
