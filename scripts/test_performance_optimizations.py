#!/usr/bin/env python3
"""
Test performance optimizations: Cache, Connection Pool, Query speed.
"""

import os
import sys
import asyncio
import time
import statistics
from typing import List, Dict, Any
from uuid import uuid4, UUID

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from agent.db_utils import initialize_database, close_database, get_database_status, test_connection
from agent.cache_manager import initialize_cache, close_cache, cache_manager
from agent.tools import vector_search_tool, hybrid_search_tool, VectorSearchInput, HybridSearchInput

load_dotenv()

class PerformanceTestSuite:
    """Test suite for performance optimizations."""
    
    def __init__(self):
        self.test_tenant_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        self.test_queries = [
            "riabilitazione ginocchio",
            "lesioni menisco",
            "fisioterapia post-operatoria",
            "dolore articolare",
            "esercizi riabilitativi"
        ]
        self.results = {}
    
    async def setup(self):
        """Setup test environment."""
        print("🔧 Setting up test environment...")
        
        try:
            await initialize_database()
            await initialize_cache()
            print("✅ Databases initialized")
            
            # Test connections
            db_ok = await test_connection()
            cache_health = await cache_manager.health_check()
            cache_ok = cache_health.get("status") == "healthy"
            
            if not db_ok:
                raise Exception("Database connection failed")
            if not cache_ok:
                raise Exception("Cache connection failed")
                
            print("✅ Connections verified")
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            raise
    
    async def teardown(self):
        """Cleanup test environment."""
        print("🧹 Cleaning up...")
        await close_database()
        await close_cache()
        print("✅ Cleanup complete")
    
    async def test_cache_performance(self) -> Dict[str, Any]:
        """Test cache hit/miss performance."""
        print("\n📊 Testing Cache Performance...")
        
        cache_miss_times = []
        cache_hit_times = []
        
        # Test cache miss (first queries)
        for query in self.test_queries:
            start_time = time.time()
            
            # This should be cache miss
            input_data = VectorSearchInput(query=query, limit=5)
            try:
                results = await vector_search_tool(input_data, self.test_tenant_id)
                cache_miss_time = (time.time() - start_time) * 1000
                cache_miss_times.append(cache_miss_time)
                print(f"  Cache MISS: {query[:30]:<30} - {cache_miss_time:6.1f}ms - {len(results)} results")
            except Exception as e:
                print(f"  ❌ Query failed: {query[:30]:<30} - {e}")
        
        # Small delay to ensure cache is set
        await asyncio.sleep(0.1)
        
        # Test cache hit (repeat queries)
        for query in self.test_queries:
            start_time = time.time()
            
            # This should be cache hit
            input_data = VectorSearchInput(query=query, limit=5)
            try:
                results = await vector_search_tool(input_data, self.test_tenant_id)
                cache_hit_time = (time.time() - start_time) * 1000
                cache_hit_times.append(cache_hit_time)
                print(f"  Cache HIT:  {query[:30]:<30} - {cache_hit_time:6.1f}ms - {len(results)} results")
            except Exception as e:
                print(f"  ❌ Query failed: {query[:30]:<30} - {e}")
        
        if cache_miss_times and cache_hit_times:
            avg_miss = statistics.mean(cache_miss_times)
            avg_hit = statistics.mean(cache_hit_times)
            speedup = avg_miss / avg_hit if avg_hit > 0 else 0
            
            return {
                "avg_cache_miss_ms": avg_miss,
                "avg_cache_hit_ms": avg_hit,
                "speedup_factor": speedup,
                "cache_efficiency": ((avg_miss - avg_hit) / avg_miss * 100) if avg_miss > 0 else 0
            }
        
        return {"error": "No valid timing data collected"}
    
    async def test_connection_pool_performance(self) -> Dict[str, Any]:
        """Test connection pool performance under concurrent load."""
        print("\n🔗 Testing Connection Pool Performance...")
        
        async def concurrent_query_task(query_id: int):
            """Single concurrent query task."""
            start_time = time.time()
            try:
                input_data = VectorSearchInput(query=f"test query {query_id}", limit=3)
                results = await vector_search_tool(input_data, self.test_tenant_id)
                duration = (time.time() - start_time) * 1000
                return {"query_id": query_id, "duration_ms": duration, "results": len(results), "success": True}
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                return {"query_id": query_id, "duration_ms": duration, "error": str(e), "success": False}
        
        # Test concurrent queries
        concurrent_levels = [1, 5, 10, 20]
        results = {}
        
        for level in concurrent_levels:
            print(f"  Testing {level} concurrent queries...")
            
            start_time = time.time()
            tasks = [concurrent_query_task(i) for i in range(level)]
            task_results = await asyncio.gather(*tasks)
            total_time = (time.time() - start_time) * 1000
            
            successful_tasks = [r for r in task_results if r.get("success", False)]
            failed_tasks = [r for r in task_results if not r.get("success", False)]
            
            if successful_tasks:
                avg_query_time = statistics.mean([r["duration_ms"] for r in successful_tasks])
                throughput = len(successful_tasks) / (total_time / 1000) # queries per second
            else:
                avg_query_time = 0
                throughput = 0
            
            results[f"concurrent_{level}"] = {
                "total_time_ms": total_time,
                "successful_queries": len(successful_tasks),
                "failed_queries": len(failed_tasks),
                "avg_query_time_ms": avg_query_time,
                "throughput_qps": throughput,
                "success_rate": len(successful_tasks) / level * 100
            }
            
            print(f"    ✅ {len(successful_tasks)}/{level} success, avg: {avg_query_time:.1f}ms, {throughput:.1f} q/s")
            
            if failed_tasks:
                print(f"    ❌ {len(failed_tasks)} failures")
        
        return results
    
    async def test_database_metrics(self) -> Dict[str, Any]:
        """Test database pool metrics and status."""
        print("\n📈 Testing Database Metrics...")
        
        try:
            status = await get_database_status()
            cache_health = await cache_manager.health_check()
            
            print(f"  Database Pool:")
            print(f"    Size: {status.get('pool_size', 'unknown')}")
            print(f"    Idle: {status.get('idle_connections', 'unknown')}")
            print(f"    Active: {status.get('metrics', {}).get('active_connections', 'unknown')}")
            print(f"    Total queries: {status.get('metrics', {}).get('query_count', 'unknown')}")
            print(f"    Avg query time: {status.get('metrics', {}).get('avg_query_time', 0):.3f}s")
            
            print(f"  Cache Status: {cache_health.get('status', 'unknown')}")
            print(f"    Memory used: {cache_health.get('memory_used', 'unknown')}")
            print(f"    Uptime: {cache_health.get('uptime', 'unknown')}s")
            
            return {
                "database_status": status,
                "cache_status": cache_health
            }
            
        except Exception as e:
            print(f"    ❌ Metrics collection failed: {e}")
            return {"error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance tests."""
        print("🚀 Starting Performance Test Suite...")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Run tests
            cache_results = await self.test_cache_performance()
            pool_results = await self.test_connection_pool_performance()
            metrics_results = await self.test_database_metrics()
            
            self.results = {
                "cache_performance": cache_results,
                "connection_pool_performance": pool_results,
                "database_metrics": metrics_results,
                "test_timestamp": time.time()
            }
            
            await self.teardown()
            
            # Summary
            print("\n" + "=" * 60)
            print("📊 PERFORMANCE TEST SUMMARY")
            print("=" * 60)
            
            if "speedup_factor" in cache_results:
                print(f"Cache Performance:")
                print(f"  Speedup Factor: {cache_results['speedup_factor']:.1f}x")
                print(f"  Cache Efficiency: {cache_results['cache_efficiency']:.1f}%")
            
            if "concurrent_10" in pool_results:
                concurrent_10 = pool_results["concurrent_10"]
                print(f"Connection Pool (10 concurrent):")
                print(f"  Success Rate: {concurrent_10['success_rate']:.1f}%")
                print(f"  Throughput: {concurrent_10['throughput_qps']:.1f} queries/sec")
            
            print("\n✅ Performance tests completed!")
            
            return self.results
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            await self.teardown()
            return {"error": str(e)}


async def main():
    """Main test runner."""
    test_suite = PerformanceTestSuite()
    results = await test_suite.run_all_tests()
    
    # Optional: Save results to file
    import json
    with open("performance_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📁 Results saved to performance_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())
