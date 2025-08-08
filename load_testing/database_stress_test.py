"""
Database stress testing for FisioRAG PostgreSQL, Neo4j, and Redis.
Comprehensive database performance evaluation under load.
"""

import asyncio
import time
import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncpg
import redis
from neo4j import GraphDatabase
import uuid

from config import LoadTestConfig, DATABASE_QUERIES


@dataclass
class DatabaseTestResult:
    """Results from database stress testing."""
    database_type: str
    test_type: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    max_response_time: float
    operations_per_second: float
    error_rate: float
    test_duration: float


class DatabaseStressTester:
    """
    Comprehensive database stress testing for all FisioRAG databases.
    Tests PostgreSQL, Neo4j, and Redis under various load scenarios.
    """
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Database connections
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.neo4j_driver = None
        self.redis_client = None
        
        # Test results storage
        self.test_results: List[DatabaseTestResult] = []
        
        # Sample data for testing
        self.sample_documents = self._generate_sample_documents()
        self.sample_embeddings = self._generate_sample_embeddings()
        self.sample_graph_data = self._generate_sample_graph_data()
    
    async def initialize(self):
        """Initialize database connections."""
        try:
            # PostgreSQL connection pool
            if self.config.postgres_url:
                self.postgres_pool = await asyncpg.create_pool(
                    self.config.postgres_url,
                    min_size=10,  # Larger pool for stress testing
                    max_size=50,
                    command_timeout=60
                )
                self.logger.info("PostgreSQL pool initialized")
            
            # Neo4j connection
            if self.config.neo4j_uri:
                self.neo4j_driver = GraphDatabase.driver(
                    self.config.neo4j_uri,
                    auth=(
                        os.getenv("NEO4J_USER", "neo4j"),
                        os.getenv("NEO4J_PASSWORD", "password")
                    ),
                    max_connection_lifetime=3600,
                    max_connection_pool_size=50
                )
                self.logger.info("Neo4j driver initialized")
            
            # Redis connection with connection pooling
            if self.config.redis_url:
                self.redis_client = redis.ConnectionPool.from_url(
                    self.config.redis_url,
                    max_connections=50
                )
                self.logger.info("Redis connection pool initialized")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    async def run_full_stress_test(self) -> Dict[str, Any]:
        """Run comprehensive stress test on all databases."""
        self.logger.info("Starting comprehensive database stress test")
        
        # Test scenarios
        test_scenarios = [
            ("read_heavy", {"read_ratio": 0.8, "write_ratio": 0.2}),
            ("write_heavy", {"read_ratio": 0.2, "write_ratio": 0.8}),
            ("balanced", {"read_ratio": 0.5, "write_ratio": 0.5}),
            ("burst_load", {"burst_interval": 30, "burst_intensity": 10})
        ]
        
        for scenario_name, scenario_config in test_scenarios:
            self.logger.info(f"Running {scenario_name} scenario")
            
            # Run tests on all databases concurrently
            tasks = [
                self.test_postgres_performance(scenario_name, scenario_config),
                self.test_neo4j_performance(scenario_name, scenario_config),
                self.test_redis_performance(scenario_name, scenario_config)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Stress test error in {scenario_name}: {result}")
        
        # Generate comprehensive report
        return self.generate_stress_test_report()
    
    async def test_postgres_performance(
        self, 
        scenario: str, 
        config: Dict[str, Any]
    ) -> DatabaseTestResult:
        """Stress test PostgreSQL with various query patterns."""
        if not self.postgres_pool:
            raise ValueError("PostgreSQL pool not initialized")
        
        test_start = time.time()
        response_times = []
        operations = 0
        successful_ops = 0
        failed_ops = 0
        
        # Test duration: 5 minutes
        test_duration = 300
        end_time = test_start + test_duration
        
        self.logger.info(f"Starting PostgreSQL {scenario} test")
        
        try:
            while time.time() < end_time:
                operation_start = time.time()
                
                try:
                    # Choose operation based on scenario
                    if scenario == "read_heavy":
                        await self._postgres_read_operation()
                    elif scenario == "write_heavy":
                        await self._postgres_write_operation()
                    elif scenario == "balanced":
                        if random.random() < 0.5:
                            await self._postgres_read_operation()
                        else:
                            await self._postgres_write_operation()
                    elif scenario == "burst_load":
                        # Simulate burst load
                        tasks = []
                        for _ in range(config.get("burst_intensity", 10)):
                            tasks.append(self._postgres_read_operation())
                        await asyncio.gather(*tasks)
                    
                    operation_time = time.time() - operation_start
                    response_times.append(operation_time)
                    successful_ops += 1
                    
                except Exception as e:
                    self.logger.error(f"PostgreSQL operation failed: {e}")
                    failed_ops += 1
                
                operations += 1
                
                # Small delay to prevent overwhelming
                if scenario != "burst_load":
                    await asyncio.sleep(0.01)
        
        except Exception as e:
            self.logger.error(f"PostgreSQL stress test failed: {e}")
        
        test_time = time.time() - test_start
        
        # Calculate statistics
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        p95_response_time = self._percentile(response_times, 95) if response_times else 0
        p99_response_time = self._percentile(response_times, 99) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        ops_per_second = operations / test_time if test_time > 0 else 0
        error_rate = failed_ops / operations if operations > 0 else 0
        
        result = DatabaseTestResult(
            database_type="PostgreSQL",
            test_type=scenario,
            total_operations=operations,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            max_response_time=max_response_time,
            operations_per_second=ops_per_second,
            error_rate=error_rate,
            test_duration=test_time
        )
        
        self.test_results.append(result)
        return result
    
    async def test_neo4j_performance(
        self,
        scenario: str,
        config: Dict[str, Any]
    ) -> DatabaseTestResult:
        """Stress test Neo4j with graph queries."""
        if not self.neo4j_driver:
            raise ValueError("Neo4j driver not initialized")
        
        test_start = time.time()
        response_times = []
        operations = 0
        successful_ops = 0
        failed_ops = 0
        
        test_duration = 300  # 5 minutes
        end_time = test_start + test_duration
        
        self.logger.info(f"Starting Neo4j {scenario} test")
        
        try:
            while time.time() < end_time:
                operation_start = time.time()
                
                try:
                    # Choose operation based on scenario
                    if scenario == "read_heavy":
                        await self._neo4j_read_operation()
                    elif scenario == "write_heavy":
                        await self._neo4j_write_operation()
                    elif scenario == "balanced":
                        if random.random() < 0.5:
                            await self._neo4j_read_operation()
                        else:
                            await self._neo4j_write_operation()
                    elif scenario == "burst_load":
                        # Burst of read operations
                        for _ in range(config.get("burst_intensity", 5)):
                            await self._neo4j_read_operation()
                    
                    operation_time = time.time() - operation_start
                    response_times.append(operation_time)
                    successful_ops += 1
                    
                except Exception as e:
                    self.logger.error(f"Neo4j operation failed: {e}")
                    failed_ops += 1
                
                operations += 1
                
                if scenario != "burst_load":
                    await asyncio.sleep(0.02)
        
        except Exception as e:
            self.logger.error(f"Neo4j stress test failed: {e}")
        
        test_time = time.time() - test_start
        
        # Calculate statistics
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        p95_response_time = self._percentile(response_times, 95) if response_times else 0
        p99_response_time = self._percentile(response_times, 99) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        ops_per_second = operations / test_time if test_time > 0 else 0
        error_rate = failed_ops / operations if operations > 0 else 0
        
        result = DatabaseTestResult(
            database_type="Neo4j",
            test_type=scenario,
            total_operations=operations,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            max_response_time=max_response_time,
            operations_per_second=ops_per_second,
            error_rate=error_rate,
            test_duration=test_time
        )
        
        self.test_results.append(result)
        return result
    
    async def test_redis_performance(
        self,
        scenario: str,
        config: Dict[str, Any]
    ) -> DatabaseTestResult:
        """Stress test Redis cache operations."""
        if not self.redis_client:
            raise ValueError("Redis client not initialized")
        
        redis_conn = redis.Redis(connection_pool=self.redis_client)
        
        test_start = time.time()
        response_times = []
        operations = 0
        successful_ops = 0
        failed_ops = 0
        
        test_duration = 300  # 5 minutes
        end_time = test_start + test_duration
        
        self.logger.info(f"Starting Redis {scenario} test")
        
        try:
            while time.time() < end_time:
                operation_start = time.time()
                
                try:
                    # Choose operation based on scenario
                    if scenario == "read_heavy":
                        await self._redis_read_operation(redis_conn)
                    elif scenario == "write_heavy":
                        await self._redis_write_operation(redis_conn)
                    elif scenario == "balanced":
                        if random.random() < 0.5:
                            await self._redis_read_operation(redis_conn)
                        else:
                            await self._redis_write_operation(redis_conn)
                    elif scenario == "burst_load":
                        # Burst of cache operations
                        for _ in range(config.get("burst_intensity", 20)):
                            await self._redis_read_operation(redis_conn)
                    
                    operation_time = time.time() - operation_start
                    response_times.append(operation_time)
                    successful_ops += 1
                    
                except Exception as e:
                    self.logger.error(f"Redis operation failed: {e}")
                    failed_ops += 1
                
                operations += 1
                
                if scenario != "burst_load":
                    await asyncio.sleep(0.001)  # Redis is very fast
        
        except Exception as e:
            self.logger.error(f"Redis stress test failed: {e}")
        
        test_time = time.time() - test_start
        
        # Calculate statistics
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        p95_response_time = self._percentile(response_times, 95) if response_times else 0
        p99_response_time = self._percentile(response_times, 99) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        ops_per_second = operations / test_time if test_time > 0 else 0
        error_rate = failed_ops / operations if operations > 0 else 0
        
        result = DatabaseTestResult(
            database_type="Redis",
            test_type=scenario,
            total_operations=operations,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            max_response_time=max_response_time,
            operations_per_second=ops_per_second,
            error_rate=error_rate,
            test_duration=test_time
        )
        
        self.test_results.append(result)
        return result
    
    # Database operation implementations
    async def _postgres_read_operation(self):
        """Simulate realistic PostgreSQL read operations."""
        async with self.postgres_pool.acquire() as conn:
            # Simulate various read patterns
            operations = [
                "SELECT COUNT(*) FROM documents WHERE tenant_id = $1",
                "SELECT * FROM embeddings ORDER BY id DESC LIMIT 10",
                "SELECT d.title, d.content FROM documents d WHERE d.created_at > NOW() - INTERVAL '1 day'",
                """
                SELECT c.*, u.username 
                FROM conversations c 
                JOIN users u ON c.user_id = u.id 
                WHERE c.updated_at > $1 
                LIMIT 50
                """
            ]
            
            query = random.choice(operations)
            
            if "$1" in query:
                if "tenant_id" in query:
                    result = await conn.fetch(query, uuid.uuid4())
                elif "updated_at" in query:
                    result = await conn.fetch(query, datetime.now() - timedelta(hours=1))
                else:
                    result = await conn.fetch(query, uuid.uuid4())
            else:
                result = await conn.fetch(query)
            
            return len(result)
    
    async def _postgres_write_operation(self):
        """Simulate realistic PostgreSQL write operations."""
        async with self.postgres_pool.acquire() as conn:
            # Simulate insert/update operations
            operations = [
                "INSERT INTO test_documents (title, content, tenant_id) VALUES ($1, $2, $3)",
                "UPDATE test_documents SET updated_at = NOW() WHERE id = $1",
                "INSERT INTO test_conversations (user_id, session_id, message) VALUES ($1, $2, $3)"
            ]
            
            operation = random.choice(operations)
            
            if "INSERT INTO test_documents" in operation:
                await conn.execute(
                    operation,
                    f"Test Document {uuid.uuid4().hex[:8]}",
                    "Test content for load testing",
                    uuid.uuid4()
                )
            elif "UPDATE test_documents" in operation:
                await conn.execute(operation, random.randint(1, 1000))
            elif "INSERT INTO test_conversations" in operation:
                await conn.execute(
                    operation,
                    uuid.uuid4(),
                    uuid.uuid4(),
                    "Test message for stress testing"
                )
    
    async def _neo4j_read_operation(self):
        """Simulate realistic Neo4j read operations."""
        with self.neo4j_driver.session() as session:
            queries = [
                "MATCH (n:Document) RETURN COUNT(n)",
                "MATCH (d:Document)-[:CONTAINS]->(c:Concept) RETURN d.title, COUNT(c) AS concepts LIMIT 10",
                "MATCH (c:Concept)-[:RELATED_TO]-(r:Concept) WHERE c.name CONTAINS 'knee' RETURN c, r LIMIT 20",
                "MATCH path = (d:Document)-[:CONTAINS*1..2]->(c:Concept) RETURN path LIMIT 15"
            ]
            
            query = random.choice(queries)
            result = session.run(query)
            return len(list(result))
    
    async def _neo4j_write_operation(self):
        """Simulate realistic Neo4j write operations."""
        with self.neo4j_driver.session() as session:
            operations = [
                """
                CREATE (d:TestDocument {
                    id: $doc_id,
                    title: $title,
                    created_at: datetime()
                })
                """,
                """
                MATCH (d:TestDocument {id: $doc_id})
                CREATE (c:TestConcept {
                    id: $concept_id,
                    name: $name
                })
                CREATE (d)-[:CONTAINS]->(c)
                """,
                """
                MATCH (c1:TestConcept {id: $id1}), (c2:TestConcept {id: $id2})
                CREATE (c1)-[:RELATED_TO]->(c2)
                """
            ]
            
            operation = random.choice(operations)
            
            if "CREATE (d:TestDocument" in operation:
                session.run(
                    operation,
                    doc_id=str(uuid.uuid4()),
                    title=f"Test Document {uuid.uuid4().hex[:8]}"
                )
            elif "CREATE (c:TestConcept" in operation:
                session.run(
                    operation,
                    doc_id=str(uuid.uuid4()),
                    concept_id=str(uuid.uuid4()),
                    name=f"test_concept_{uuid.uuid4().hex[:8]}"
                )
            elif "RELATED_TO" in operation:
                session.run(
                    operation,
                    id1=str(uuid.uuid4()),
                    id2=str(uuid.uuid4())
                )
    
    async def _redis_read_operation(self, redis_conn):
        """Simulate realistic Redis read operations."""
        # Simulate cache lookups
        operations = [
            lambda: redis_conn.get(f"cache:session:{uuid.uuid4()}"),
            lambda: redis_conn.get(f"cache:user:{uuid.uuid4()}"),
            lambda: redis_conn.lrange(f"queue:tasks", 0, 10),
            lambda: redis_conn.hgetall(f"stats:daily:{datetime.now().strftime('%Y%m%d')}"),
            lambda: redis_conn.smembers(f"active_users"),
            lambda: redis_conn.zrange(f"leaderboard", 0, 10)
        ]
        
        operation = random.choice(operations)
        return operation()
    
    async def _redis_write_operation(self, redis_conn):
        """Simulate realistic Redis write operations."""
        # Simulate cache writes
        operations = [
            lambda: redis_conn.set(
                f"cache:session:{uuid.uuid4()}",
                json.dumps({"user_id": str(uuid.uuid4()), "timestamp": time.time()}),
                ex=3600
            ),
            lambda: redis_conn.lpush(f"queue:tasks", json.dumps({"task": "test", "id": str(uuid.uuid4())})),
            lambda: redis_conn.hset(
                f"stats:daily:{datetime.now().strftime('%Y%m%d')}",
                "requests",
                random.randint(1, 1000)
            ),
            lambda: redis_conn.sadd("active_users", str(uuid.uuid4())),
            lambda: redis_conn.zadd("leaderboard", {str(uuid.uuid4()): random.randint(1, 100)})
        ]
        
        operation = random.choice(operations)
        return operation()
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value from a list of numbers."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _generate_sample_documents(self) -> List[Dict[str, Any]]:
        """Generate sample documents for testing."""
        documents = []
        topics = [
            "knee rehabilitation", "shoulder physiotherapy", "spinal mobility",
            "sports injury recovery", "chronic pain management", "post-surgery rehabilitation"
        ]
        
        for i in range(100):
            doc = {
                "id": str(uuid.uuid4()),
                "title": f"Clinical Guide: {random.choice(topics)} - Part {i+1}",
                "content": f"Detailed clinical content about {random.choice(topics)} " * 50,
                "tenant_id": str(uuid.uuid4())
            }
            documents.append(doc)
        
        return documents
    
    def _generate_sample_embeddings(self) -> List[List[float]]:
        """Generate sample embeddings for testing."""
        return [
            [random.random() for _ in range(1536)]  # OpenAI embedding dimension
            for _ in range(100)
        ]
    
    def _generate_sample_graph_data(self) -> List[Dict[str, Any]]:
        """Generate sample graph data for testing."""
        concepts = [
            "knee", "shoulder", "spine", "muscle", "tendon", "ligament",
            "rehabilitation", "exercise", "therapy", "recovery"
        ]
        
        graph_data = []
        for i in range(50):
            data = {
                "source": random.choice(concepts),
                "target": random.choice(concepts),
                "relationship": random.choice(["RELATED_TO", "TREATS", "AFFECTS", "STRENGTHENS"])
            }
            graph_data.append(data)
        
        return graph_data
    
    def generate_stress_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive stress test report."""
        if not self.test_results:
            return {"error": "No test results available"}
        
        # Group results by database type
        postgres_results = [r for r in self.test_results if r.database_type == "PostgreSQL"]
        neo4j_results = [r for r in self.test_results if r.database_type == "Neo4j"]
        redis_results = [r for r in self.test_results if r.database_type == "Redis"]
        
        def analyze_results(results: List[DatabaseTestResult]) -> Dict[str, Any]:
            if not results:
                return {}
            
            return {
                "total_tests": len(results),
                "avg_operations_per_second": sum(r.operations_per_second for r in results) / len(results),
                "avg_response_time": sum(r.avg_response_time for r in results) / len(results),
                "max_response_time": max(r.max_response_time for r in results),
                "avg_error_rate": sum(r.error_rate for r in results) / len(results),
                "total_operations": sum(r.total_operations for r in results),
                "total_successful": sum(r.successful_operations for r in results),
                "scenarios": {
                    r.test_type: {
                        "ops_per_second": r.operations_per_second,
                        "avg_response_time": r.avg_response_time,
                        "p95_response_time": r.p95_response_time,
                        "error_rate": r.error_rate
                    }
                    for r in results
                }
            }
        
        report = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "databases_tested": len(set(r.database_type for r in self.test_results))
            },
            "database_performance": {
                "PostgreSQL": analyze_results(postgres_results),
                "Neo4j": analyze_results(neo4j_results), 
                "Redis": analyze_results(redis_results)
            },
            "performance_recommendations": self._generate_recommendations(),
            "raw_results": [
                {
                    "database": r.database_type,
                    "scenario": r.test_type,
                    "operations_per_second": r.operations_per_second,
                    "avg_response_time": r.avg_response_time,
                    "p95_response_time": r.p95_response_time,
                    "error_rate": r.error_rate,
                    "total_operations": r.total_operations
                }
                for r in self.test_results
            ]
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on test results."""
        recommendations = []
        
        for result in self.test_results:
            if result.error_rate > 0.05:  # 5% error rate
                recommendations.append(
                    f"{result.database_type}: High error rate ({result.error_rate:.2%}) in {result.test_type} scenario. "
                    "Consider increasing connection pool size or optimizing queries."
                )
            
            if result.avg_response_time > 1.0:  # 1 second average
                recommendations.append(
                    f"{result.database_type}: Slow average response time ({result.avg_response_time:.2f}s) in {result.test_type}. "
                    "Consider adding indexes or query optimization."
                )
            
            if result.operations_per_second < 10:  # Very low throughput
                recommendations.append(
                    f"{result.database_type}: Low throughput ({result.operations_per_second:.1f} ops/s) in {result.test_type}. "
                    "Database may be a bottleneck under load."
                )
        
        if not recommendations:
            recommendations.append("All databases performed within acceptable thresholds.")
        
        return recommendations
    
    async def cleanup(self):
        """Clean up database connections."""
        if self.postgres_pool:
            await self.postgres_pool.close()
        
        if self.neo4j_driver:
            self.neo4j_driver.close()
        
        if self.redis_client:
            # Connection pool doesn't need explicit closing
            pass


# Standalone test runner
async def run_database_stress_test():
    """Run standalone database stress test."""
    config = LoadTestConfig()
    tester = DatabaseStressTester(config)
    
    try:
        await tester.initialize()
        results = await tester.run_full_stress_test()
        
        print(json.dumps(results, indent=2))
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"database_stress_test_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to {filename}")
        
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    import os
    import sys
    
    # Add current directory to path for imports
    sys.path.append(os.path.dirname(__file__))
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run stress test
    asyncio.run(run_database_stress_test())
