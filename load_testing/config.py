"""
Configuration for FisioRAG Load Testing Suite.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class TestScenario(Enum):
    """Load testing scenarios for different use cases."""
    BASELINE = "baseline"           # Normal user load
    PEAK_HOURS = "peak_hours"      # University exam periods
    STRESS_TEST = "stress_test"    # Breaking point testing
    SPIKE_TEST = "spike_test"      # Sudden traffic increases
    VOLUME_TEST = "volume_test"    # Large data processing
    ENDURANCE = "endurance"        # Long-running stability


@dataclass
class LoadTestConfig:
    """Configuration for load testing parameters."""
    
    # API Configuration
    api_base_url: str = os.getenv("LOAD_TEST_API_URL", "http://localhost:8000")
    api_timeout: int = 30
    
    # Test User Configuration
    concurrent_users: int = 10
    spawn_rate: float = 1.0  # users per second
    test_duration: str = "5m"
    
    # Test Data Configuration
    sample_queries: List[str] = None
    test_tenants: List[str] = None
    
    # Database Configuration
    postgres_url: str = os.getenv("DATABASE_URL", "")
    neo4j_uri: str = os.getenv("NEO4J_URI", "")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Monitoring Configuration
    prometheus_url: str = "http://localhost:9090"
    grafana_url: str = "http://localhost:3001"
    
    # Performance Thresholds
    response_time_p95_threshold: float = 2.0  # seconds
    response_time_p99_threshold: float = 5.0  # seconds
    error_rate_threshold: float = 0.01  # 1%
    throughput_threshold: float = 100.0  # requests/second

    def __post_init__(self):
        """Initialize default values after object creation."""
        if self.sample_queries is None:
            self.sample_queries = [
                "Quali sono i principali esercizi per la riabilitazione del ginocchio?",
                "Come si tratta una distorsione alla caviglia?",
                "Protocolli di fisioterapia per lesioni al menisco",
                "Tecniche di mobilizzazione spinale per lombalgia",
                "Esercizi propriocettivi per instabilità di spalla",
                "Riabilitazione post-operatoria legamento crociato anteriore",
                "Trattamento conservativo per ernia del disco",
                "Elettroterapia per dolore cronico",
                "Stretching per sindrome del tunnel carpale",
                "Idroterapia per artrite reumatoide"
            ]
        
        if self.test_tenants is None:
            self.test_tenants = ["default", "test-university", "clinic-demo"]


# Predefined configurations for different scenarios
SCENARIO_CONFIGS: Dict[TestScenario, LoadTestConfig] = {
    TestScenario.BASELINE: LoadTestConfig(
        concurrent_users=10,
        spawn_rate=1.0,
        test_duration="5m",
        response_time_p95_threshold=2.0,
        error_rate_threshold=0.01
    ),
    
    TestScenario.PEAK_HOURS: LoadTestConfig(
        concurrent_users=50,
        spawn_rate=5.0,
        test_duration="15m",
        response_time_p95_threshold=3.0,
        error_rate_threshold=0.02
    ),
    
    TestScenario.STRESS_TEST: LoadTestConfig(
        concurrent_users=200,
        spawn_rate=10.0,
        test_duration="30m",
        response_time_p95_threshold=5.0,
        error_rate_threshold=0.05
    ),
    
    TestScenario.SPIKE_TEST: LoadTestConfig(
        concurrent_users=100,
        spawn_rate=50.0,  # Rapid spike
        test_duration="10m",
        response_time_p95_threshold=4.0,
        error_rate_threshold=0.03
    ),
    
    TestScenario.VOLUME_TEST: LoadTestConfig(
        concurrent_users=25,
        spawn_rate=2.0,
        test_duration="60m",  # Long duration
        response_time_p95_threshold=3.0,
        error_rate_threshold=0.02
    ),
    
    TestScenario.ENDURANCE: LoadTestConfig(
        concurrent_users=30,
        spawn_rate=1.0,
        test_duration="4h",  # Very long duration
        response_time_p95_threshold=2.5,
        error_rate_threshold=0.015
    )
}


class TestEnvironment:
    """Environment-specific configurations."""
    
    DEVELOPMENT = LoadTestConfig(
        api_base_url="http://localhost:8000",
        concurrent_users=5,
        test_duration="2m"
    )
    
    STAGING = LoadTestConfig(
        api_base_url="https://staging.fisiorag.com",
        concurrent_users=25,
        test_duration="10m"
    )
    
    PRODUCTION = LoadTestConfig(
        api_base_url="https://api.fisiorag.com",
        concurrent_users=100,
        test_duration="30m",
        response_time_p95_threshold=1.5,
        error_rate_threshold=0.005
    )


# Health check endpoints for monitoring
HEALTH_ENDPOINTS = [
    "/health",
    "/health/detailed",
    "/status/database",
    "/metrics"
]

# Critical API endpoints to test
API_ENDPOINTS = [
    "/chat",
    "/chat/stream",
    "/search/vector",
    "/search/graph",
    "/search/hybrid"
]

# Database performance queries
DATABASE_QUERIES = {
    "postgres": [
        "SELECT COUNT(*) FROM documents",
        "SELECT COUNT(*) FROM embeddings",
        "SELECT COUNT(*) FROM conversations",
        "SELECT AVG(LENGTH(content)) FROM documents"
    ],
    "neo4j": [
        "MATCH (n) RETURN COUNT(n)",
        "MATCH ()-[r]->() RETURN COUNT(r)",
        "MATCH (d:Document) RETURN COUNT(d)",
        "MATCH (c:Concept) RETURN COUNT(c)"
    ],
    "redis": [
        "INFO memory",
        "DBSIZE",
        "INFO stats"
    ]
}

# System metrics to monitor
SYSTEM_METRICS = [
    "cpu_usage_percent",
    "memory_usage_percent", 
    "disk_io_read_bytes",
    "disk_io_write_bytes",
    "network_sent_bytes",
    "network_recv_bytes"
]

# Application metrics from Prometheus
APP_METRICS = [
    "http_requests_total",
    "http_request_duration_seconds",
    "postgres_connections_active",
    "neo4j_connections_active", 
    "redis_connections_active",
    "rag_queries_total",
    "vector_searches_total",
    "graph_queries_total"
]
