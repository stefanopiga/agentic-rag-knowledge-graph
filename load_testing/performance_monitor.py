"""
Performance monitoring and metrics collection for FisioRAG load testing.
Real-time system metrics, database performance, and application health tracking.
"""

import asyncio
import time
import psutil
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import asyncpg
import redis
from neo4j import GraphDatabase
import httpx

from config import LoadTestConfig, DATABASE_QUERIES, SYSTEM_METRICS, APP_METRICS


@dataclass
class PerformanceMetrics:
    """Container for performance metrics at a point in time."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_sent: int
    network_recv: int
    postgres_connections: int
    neo4j_connections: int
    redis_connections: int
    response_times: Dict[str, float]
    throughput: float
    error_rate: float
    active_users: int


class PerformanceMonitor:
    """
    Advanced performance monitoring for load testing.
    Tracks system resources, database performance, and application metrics.
    """
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.is_monitoring = False
        self.metrics_history: List[PerformanceMetrics] = []
        self.logger = logging.getLogger(__name__)
        
        # Initialize database connections
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.neo4j_driver = None
        self.redis_client = None
        
        # HTTP client for API monitoring
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Performance tracking
        self.start_time = None
        self.last_network_stats = None
        self.last_disk_stats = None
    
    async def initialize(self):
        """Initialize monitoring connections and baseline metrics."""
        try:
            # PostgreSQL connection pool
            if self.config.postgres_url:
                self.postgres_pool = await asyncpg.create_pool(
                    self.config.postgres_url,
                    min_size=2,
                    max_size=5
                )
            
            # Neo4j connection
            if self.config.neo4j_uri:
                from neo4j import GraphDatabase
                self.neo4j_driver = GraphDatabase.driver(
                    self.config.neo4j_uri,
                    auth=(
                        os.getenv("NEO4J_USER", "neo4j"),
                        os.getenv("NEO4J_PASSWORD", "password")
                    )
                )
            
            # Redis connection
            if self.config.redis_url:
                self.redis_client = redis.from_url(self.config.redis_url)
            
            self.logger.info("Performance monitor initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize performance monitor: {e}")
            raise
    
    async def start_monitoring(self, interval: int = 5):
        """Start continuous performance monitoring."""
        self.is_monitoring = True
        self.start_time = datetime.now()
        
        # Initialize baseline network and disk stats
        self.last_network_stats = psutil.net_io_counters()
        self.last_disk_stats = psutil.disk_io_counters()
        
        self.logger.info(f"Started performance monitoring (interval: {interval}s)")
        
        while self.is_monitoring:
            try:
                metrics = await self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Log critical metrics
                self.logger.debug(
                    f"Metrics: CPU={metrics.cpu_percent:.1f}% "
                    f"Memory={metrics.memory_percent:.1f}% "
                    f"Throughput={metrics.throughput:.1f}rps "
                    f"ErrorRate={metrics.error_rate:.2%}"
                )
                
                # Check for performance alerts
                await self.check_performance_alerts(metrics)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval)
    
    async def collect_metrics(self) -> PerformanceMetrics:
        """Collect comprehensive performance metrics."""
        timestamp = datetime.now()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Network I/O delta
        current_network = psutil.net_io_counters()
        network_sent = current_network.bytes_sent - self.last_network_stats.bytes_sent
        network_recv = current_network.bytes_recv - self.last_network_stats.bytes_recv
        self.last_network_stats = current_network
        
        # Disk I/O delta
        current_disk = psutil.disk_io_counters()
        disk_read = current_disk.read_bytes - self.last_disk_stats.read_bytes
        disk_write = current_disk.write_bytes - self.last_disk_stats.write_bytes
        self.last_disk_stats = current_disk
        
        # Database connections
        postgres_connections = await self.get_postgres_connections()
        neo4j_connections = await self.get_neo4j_connections()
        redis_connections = await self.get_redis_connections()
        
        # API performance metrics
        response_times = await self.measure_api_response_times()
        throughput = await self.calculate_throughput()
        error_rate = await self.calculate_error_rate()
        
        # Active users (from Locust or application metrics)
        active_users = await self.get_active_users()
        
        return PerformanceMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_io_read=disk_read,
            disk_io_write=disk_write,
            network_sent=network_sent,
            network_recv=network_recv,
            postgres_connections=postgres_connections,
            neo4j_connections=neo4j_connections,
            redis_connections=redis_connections,
            response_times=response_times,
            throughput=throughput,
            error_rate=error_rate,
            active_users=active_users
        )
    
    async def get_postgres_connections(self) -> int:
        """Get current PostgreSQL connection count."""
        if not self.postgres_pool:
            return 0
        
        try:
            async with self.postgres_pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                )
                return result or 0
        except Exception as e:
            self.logger.error(f"PostgreSQL connection check failed: {e}")
            return -1
    
    async def get_neo4j_connections(self) -> int:
        """Get current Neo4j connection count."""
        if not self.neo4j_driver:
            return 0
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("CALL dbms.listConnections()")
                connections = list(result)
                return len(connections)
        except Exception as e:
            self.logger.error(f"Neo4j connection check failed: {e}")
            return -1
    
    async def get_redis_connections(self) -> int:
        """Get current Redis connection count."""
        if not self.redis_client:
            return 0
        
        try:
            info = self.redis_client.info()
            return info.get('connected_clients', 0)
        except Exception as e:
            self.logger.error(f"Redis connection check failed: {e}")
            return -1
    
    async def measure_api_response_times(self) -> Dict[str, float]:
        """Measure response times for critical API endpoints."""
        response_times = {}
        
        endpoints = [
            ("/health", "GET"),
            ("/chat", "POST"),
            ("/status/database", "GET")
        ]
        
        for endpoint, method in endpoints:
            try:
                start_time = time.time()
                
                if method == "GET":
                    response = await self.http_client.get(
                        f"{self.config.api_base_url}{endpoint}"
                    )
                else:  # POST
                    test_data = {
                        "message": "Test query for performance monitoring",
                        "user_id": "perf_monitor",
                        "tenant_slug": "default"
                    }
                    response = await self.http_client.post(
                        f"{self.config.api_base_url}{endpoint}",
                        json=test_data
                    )
                
                response_time = time.time() - start_time
                response_times[f"{method}_{endpoint}"] = response_time
                
            except Exception as e:
                self.logger.error(f"API response time check failed for {endpoint}: {e}")
                response_times[f"{method}_{endpoint}"] = -1
        
        return response_times
    
    async def calculate_throughput(self) -> float:
        """Calculate current API throughput (requests per second)."""
        try:
            # Query Prometheus for throughput metrics
            query = 'rate(http_requests_total[1m])'
            response = await self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": query}
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', {}).get('result', [])
                
                if results:
                    # Sum all request rates
                    total_rate = sum(
                        float(result['value'][1]) 
                        for result in results
                    )
                    return total_rate
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Throughput calculation failed: {e}")
            return -1.0
    
    async def calculate_error_rate(self) -> float:
        """Calculate current API error rate."""
        try:
            # Query Prometheus for error rate
            error_query = 'rate(http_requests_total{status=~"4..|5.."}[1m])'
            total_query = 'rate(http_requests_total[1m])'
            
            error_response = await self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": error_query}
            )
            
            total_response = await self.http_client.get(
                f"{self.config.prometheus_url}/api/v1/query",
                params={"query": total_query}
            )
            
            if error_response.status_code == 200 and total_response.status_code == 200:
                error_data = error_response.json()
                total_data = total_response.json()
                
                error_results = error_data.get('data', {}).get('result', [])
                total_results = total_data.get('data', {}).get('result', [])
                
                total_errors = sum(
                    float(result['value'][1]) 
                    for result in error_results
                )
                
                total_requests = sum(
                    float(result['value'][1]) 
                    for result in total_results
                )
                
                if total_requests > 0:
                    return total_errors / total_requests
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error rate calculation failed: {e}")
            return -1.0
    
    async def get_active_users(self) -> int:
        """Get number of active users from application metrics."""
        try:
            # This would typically come from your application metrics
            # For now, we'll estimate based on recent session activity
            if self.postgres_pool:
                async with self.postgres_pool.acquire() as conn:
                    recent_time = datetime.now() - timedelta(minutes=5)
                    result = await conn.fetchval(
                        """
                        SELECT COUNT(DISTINCT user_id) 
                        FROM conversations 
                        WHERE updated_at > $1
                        """,
                        recent_time
                    )
                    return result or 0
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Active users calculation failed: {e}")
            return -1
    
    async def check_performance_alerts(self, metrics: PerformanceMetrics):
        """Check for performance threshold violations and log alerts."""
        alerts = []
        
        # CPU threshold
        if metrics.cpu_percent > 80:
            alerts.append(f"HIGH CPU: {metrics.cpu_percent:.1f}%")
        
        # Memory threshold
        if metrics.memory_percent > 85:
            alerts.append(f"HIGH MEMORY: {metrics.memory_percent:.1f}%")
        
        # Response time threshold
        for endpoint, response_time in metrics.response_times.items():
            if response_time > self.config.response_time_p95_threshold:
                alerts.append(f"SLOW RESPONSE {endpoint}: {response_time:.2f}s")
        
        # Error rate threshold
        if metrics.error_rate > self.config.error_rate_threshold:
            alerts.append(f"HIGH ERROR RATE: {metrics.error_rate:.2%}")
        
        # Throughput drop alert
        if metrics.throughput < self.config.throughput_threshold * 0.5:
            alerts.append(f"LOW THROUGHPUT: {metrics.throughput:.1f}rps")
        
        # Database connection alerts
        if metrics.postgres_connections > 50:
            alerts.append(f"HIGH PG CONNECTIONS: {metrics.postgres_connections}")
        
        if alerts:
            self.logger.warning(f"PERFORMANCE ALERTS: {' | '.join(alerts)}")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.is_monitoring = False
        self.logger.info("Performance monitoring stopped")
    
    async def cleanup(self):
        """Clean up monitoring resources."""
        if self.postgres_pool:
            await self.postgres_pool.close()
        
        if self.neo4j_driver:
            self.neo4j_driver.close()
        
        if self.redis_client:
            self.redis_client.close()
        
        await self.http_client.aclose()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Generate performance summary from collected metrics."""
        if not self.metrics_history:
            return {"error": "No metrics collected"}
        
        # Calculate aggregated statistics
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        memory_values = [m.memory_percent for m in self.metrics_history]
        throughput_values = [m.throughput for m in self.metrics_history if m.throughput >= 0]
        error_rates = [m.error_rate for m in self.metrics_history if m.error_rate >= 0]
        
        # Response time aggregation
        response_time_summary = {}
        for metrics in self.metrics_history:
            for endpoint, rt in metrics.response_times.items():
                if rt >= 0:  # Valid response time
                    if endpoint not in response_time_summary:
                        response_time_summary[endpoint] = []
                    response_time_summary[endpoint].append(rt)
        
        # Calculate percentiles
        def percentile(data: List[float], p: float) -> float:
            if not data:
                return 0.0
            sorted_data = sorted(data)
            index = int(len(sorted_data) * p / 100)
            return sorted_data[min(index, len(sorted_data) - 1)]
        
        summary = {
            "test_duration": str(datetime.now() - self.start_time) if self.start_time else "0",
            "total_samples": len(self.metrics_history),
            "system_performance": {
                "cpu_avg": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "cpu_max": max(cpu_values) if cpu_values else 0,
                "memory_avg": sum(memory_values) / len(memory_values) if memory_values else 0,
                "memory_max": max(memory_values) if memory_values else 0
            },
            "api_performance": {
                "throughput_avg": sum(throughput_values) / len(throughput_values) if throughput_values else 0,
                "throughput_max": max(throughput_values) if throughput_values else 0,
                "error_rate_avg": sum(error_rates) / len(error_rates) if error_rates else 0,
                "error_rate_max": max(error_rates) if error_rates else 0
            },
            "response_times": {
                endpoint: {
                    "avg": sum(times) / len(times),
                    "p50": percentile(times, 50),
                    "p95": percentile(times, 95),
                    "p99": percentile(times, 99),
                    "max": max(times)
                }
                for endpoint, times in response_time_summary.items()
                if times
            }
        }
        
        return summary
    
    def export_metrics(self, filename: str):
        """Export collected metrics to JSON file."""
        export_data = {
            "test_config": asdict(self.config),
            "performance_summary": self.get_performance_summary(),
            "raw_metrics": [
                asdict(metrics) 
                for metrics in self.metrics_history
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.logger.info(f"Performance metrics exported to {filename}")


# Utility functions for standalone monitoring
async def run_monitoring_session(
    config: LoadTestConfig,
    duration_minutes: int = 30,
    interval_seconds: int = 5
):
    """Run a standalone monitoring session."""
    monitor = PerformanceMonitor(config)
    
    try:
        await monitor.initialize()
        
        # Start monitoring in background
        monitoring_task = asyncio.create_task(
            monitor.start_monitoring(interval_seconds)
        )
        
        # Wait for specified duration
        await asyncio.sleep(duration_minutes * 60)
        
        # Stop monitoring
        monitor.stop_monitoring()
        await monitoring_task
        
        # Generate report
        summary = monitor.get_performance_summary()
        print(json.dumps(summary, indent=2))
        
        # Export metrics
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_metrics_{timestamp}.json"
        monitor.export_metrics(filename)
        
    finally:
        await monitor.cleanup()


if __name__ == "__main__":
    import sys
    import os
    
    # Add current directory to path for imports
    sys.path.append(os.path.dirname(__file__))
    
    # Run monitoring session
    config = LoadTestConfig()
    asyncio.run(run_monitoring_session(config, duration_minutes=10))
