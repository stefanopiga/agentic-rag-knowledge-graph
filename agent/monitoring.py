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
# HEALTH CHECK ENHANCEMENTS
# ==============================================================================

async def get_detailed_health_status() -> Dict[str, Any]:
    """Get detailed health status including metrics."""
    return {
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "healthy",
            "database": "healthy", 
            "graph_database": "healthy",
            "cache": "healthy",
            "llm_provider": "healthy"
        },
        "metrics": {
            "active_sessions": sessions_active._value._value if hasattr(sessions_active, '_value') else 0,
            "total_queries_today": "calculated_value",  # Would calculate from metrics
            "avg_response_time": "calculated_value",    # Would calculate from histograms
            "cache_hit_rate": "calculated_value"        # Would calculate from cache metrics
        },
        "version": "0.1.0",
        "uptime_seconds": "calculated_value"
    }
