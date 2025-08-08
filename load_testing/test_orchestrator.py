"""
Test orchestration for comprehensive FisioRAG scalability testing.
Coordinates load testing, performance monitoring, and database stress testing.
"""

import asyncio
import json
import logging
import os
import subprocess
import signal
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from config import LoadTestConfig, TestScenario, SCENARIO_CONFIGS
from performance_monitor import PerformanceMonitor
from database_stress_test import DatabaseStressTester


@dataclass
class TestPlan:
    """Definition of a comprehensive test plan."""
    name: str
    scenario: TestScenario
    duration_minutes: int
    concurrent_users: int
    spawn_rate: float
    include_database_stress: bool = True
    include_performance_monitoring: bool = True
    warmup_duration_seconds: int = 30


class TestOrchestrator:
    """
    Orchestrates comprehensive scalability testing.
    Coordinates multiple test types and generates unified reports.
    """
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Test components
        self.performance_monitor = PerformanceMonitor(config)
        self.database_tester = DatabaseStressTester(config)
        
        # Test tracking
        self.current_test_plan: Optional[TestPlan] = None
        self.test_results: Dict[str, Any] = {}
        self.test_start_time: Optional[datetime] = None
        
        # Process management
        self.locust_process: Optional[subprocess.Popen] = None
        self.monitoring_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize all test components."""
        try:
            await self.performance_monitor.initialize()
            await self.database_tester.initialize()
            self.logger.info("Test orchestrator initialized successfully")
        except Exception as e:
            self.logger.error(f"Orchestrator initialization failed: {e}")
            raise
    
    async def run_test_plan(self, test_plan: TestPlan) -> Dict[str, Any]:
        """Execute a complete test plan with all components."""
        self.current_test_plan = test_plan
        self.test_start_time = datetime.now()
        
        self.logger.info(f"Starting test plan: {test_plan.name}")
        self.logger.info(f"Scenario: {test_plan.scenario.value}")
        self.logger.info(f"Duration: {test_plan.duration_minutes} minutes")
        self.logger.info(f"Users: {test_plan.concurrent_users}")
        
        try:
            # Phase 1: Pre-test warmup
            await self._warmup_phase(test_plan)
            
            # Phase 2: Start performance monitoring
            if test_plan.include_performance_monitoring:
                await self._start_performance_monitoring()
            
            # Phase 3: Start database stress testing (background)
            if test_plan.include_database_stress:
                database_task = asyncio.create_task(self._run_database_stress())
            else:
                database_task = None
            
            # Phase 4: Execute main load test
            load_test_results = await self._run_load_test(test_plan)
            
            # Phase 5: Wait for all tests to complete
            if database_task:
                database_results = await database_task
            else:
                database_results = {}
            
            # Phase 6: Stop monitoring and collect results
            performance_results = await self._stop_performance_monitoring()
            
            # Phase 7: Generate unified report
            unified_results = await self._generate_unified_report(
                test_plan,
                load_test_results,
                performance_results,
                database_results
            )
            
            self.test_results = unified_results
            return unified_results
            
        except Exception as e:
            self.logger.error(f"Test plan execution failed: {e}")
            await self._cleanup_test()
            raise
        
        finally:
            await self._cleanup_test()
    
    async def run_full_scalability_suite(self) -> Dict[str, Any]:
        """Run the complete scalability testing suite."""
        self.logger.info("Starting comprehensive scalability testing suite")
        
        # Define test plans for different scenarios
        test_plans = [
            TestPlan(
                name="Baseline Performance Test",
                scenario=TestScenario.BASELINE,
                duration_minutes=10,
                concurrent_users=10,
                spawn_rate=1.0,
                warmup_duration_seconds=30
            ),
            TestPlan(
                name="Peak Hours Simulation", 
                scenario=TestScenario.PEAK_HOURS,
                duration_minutes=15,
                concurrent_users=50,
                spawn_rate=5.0,
                warmup_duration_seconds=60
            ),
            TestPlan(
                name="Stress Test - Breaking Point",
                scenario=TestScenario.STRESS_TEST,
                duration_minutes=20,
                concurrent_users=200,
                spawn_rate=10.0,
                warmup_duration_seconds=120
            ),
            TestPlan(
                name="Spike Load Test",
                scenario=TestScenario.SPIKE_TEST,
                duration_minutes=10,
                concurrent_users=100,
                spawn_rate=50.0,  # Rapid spike
                warmup_duration_seconds=30
            ),
            TestPlan(
                name="Endurance Test",
                scenario=TestScenario.ENDURANCE,
                duration_minutes=60,  # 1 hour
                concurrent_users=30,
                spawn_rate=1.0,
                warmup_duration_seconds=60
            )
        ]
        
        suite_results = {
            "suite_metadata": {
                "start_time": datetime.now().isoformat(),
                "total_test_plans": len(test_plans),
                "estimated_duration_minutes": sum(tp.duration_minutes for tp in test_plans) + 30
            },
            "test_results": {},
            "suite_summary": {}
        }
        
        # Execute each test plan
        for i, test_plan in enumerate(test_plans, 1):
            self.logger.info(f"Executing test plan {i}/{len(test_plans)}: {test_plan.name}")
            
            try:
                # Cool-down period between tests
                if i > 1:
                    cooldown_time = 300  # 5 minutes
                    self.logger.info(f"Cooling down for {cooldown_time} seconds...")
                    await asyncio.sleep(cooldown_time)
                
                # Run test plan
                results = await self.run_test_plan(test_plan)
                suite_results["test_results"][test_plan.name] = results
                
                self.logger.info(f"Completed test plan: {test_plan.name}")
                
            except Exception as e:
                self.logger.error(f"Test plan {test_plan.name} failed: {e}")
                suite_results["test_results"][test_plan.name] = {
                    "error": str(e),
                    "status": "failed"
                }
        
        # Generate suite summary
        suite_results["suite_summary"] = self._generate_suite_summary(suite_results)
        suite_results["suite_metadata"]["end_time"] = datetime.now().isoformat()
        
        # Save comprehensive report
        await self._save_suite_report(suite_results)
        
        return suite_results
    
    async def _warmup_phase(self, test_plan: TestPlan):
        """Perform system warmup before main testing."""
        self.logger.info(f"Starting warmup phase ({test_plan.warmup_duration_seconds}s)")
        
        # Light load to warm up the system
        warmup_process = await self._start_locust_test(
            users=5,
            spawn_rate=1.0,
            run_time=f"{test_plan.warmup_duration_seconds}s",
            test_name="warmup"
        )
        
        # Wait for warmup to complete
        await asyncio.sleep(test_plan.warmup_duration_seconds + 10)
        
        # Stop warmup
        if warmup_process and warmup_process.poll() is None:
            warmup_process.terminate()
            await asyncio.sleep(5)
        
        self.logger.info("Warmup phase completed")
    
    async def _start_performance_monitoring(self):
        """Start background performance monitoring."""
        self.logger.info("Starting performance monitoring")
        self.monitoring_task = asyncio.create_task(
            self.performance_monitor.start_monitoring(interval=5)
        )
        # Give monitoring time to start
        await asyncio.sleep(2)
    
    async def _stop_performance_monitoring(self) -> Dict[str, Any]:
        """Stop performance monitoring and return results."""
        if self.monitoring_task:
            self.performance_monitor.stop_monitoring()
            try:
                await asyncio.wait_for(self.monitoring_task, timeout=10)
            except asyncio.TimeoutError:
                self.logger.warning("Performance monitoring stop timed out")
            
            return self.performance_monitor.get_performance_summary()
        
        return {}
    
    async def _run_database_stress(self) -> Dict[str, Any]:
        """Run database stress testing in background."""
        self.logger.info("Starting database stress testing")
        try:
            return await self.database_tester.run_full_stress_test()
        except Exception as e:
            self.logger.error(f"Database stress testing failed: {e}")
            return {"error": str(e)}
    
    async def _run_load_test(self, test_plan: TestPlan) -> Dict[str, Any]:
        """Execute the main Locust load test."""
        self.logger.info(f"Starting main load test: {test_plan.name}")
        
        # Start Locust test
        locust_process = await self._start_locust_test(
            users=test_plan.concurrent_users,
            spawn_rate=test_plan.spawn_rate,
            run_time=f"{test_plan.duration_minutes}m",
            test_name=test_plan.name.lower().replace(" ", "_")
        )
        
        self.locust_process = locust_process
        
        # Monitor test progress
        test_duration_seconds = test_plan.duration_minutes * 60
        
        # Wait for test completion with progress updates
        progress_interval = 60  # Update every minute
        elapsed = 0
        
        while elapsed < test_duration_seconds:
            await asyncio.sleep(progress_interval)
            elapsed += progress_interval
            
            progress_percent = (elapsed / test_duration_seconds) * 100
            self.logger.info(f"Load test progress: {progress_percent:.1f}%")
            
            # Check if process is still running
            if locust_process and locust_process.poll() is not None:
                self.logger.warning("Locust process terminated early")
                break
        
        # Wait for final results and cleanup
        if locust_process and locust_process.poll() is None:
            locust_process.terminate()
            await asyncio.sleep(10)
        
        # Parse Locust results
        return await self._parse_locust_results(test_plan.name)
    
    async def _start_locust_test(
        self,
        users: int,
        spawn_rate: float,
        run_time: str,
        test_name: str
    ) -> subprocess.Popen:
        """Start a Locust test process."""
        
        # Create results directory
        results_dir = Path("load_testing/results")
        results_dir.mkdir(exist_ok=True)
        
        # Locust command
        locust_cmd = [
            "locust",
            "-f", "locustfile.py",
            "--host", self.config.api_base_url,
            "--users", str(users),
            "--spawn-rate", str(spawn_rate),
            "--run-time", run_time,
            "--headless",
            "--html", f"results/{test_name}_report.html",
            "--csv", f"results/{test_name}",
            "--logfile", f"results/{test_name}.log"
        ]
        
        # Start Locust process
        process = subprocess.Popen(
            locust_cmd,
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.logger.info(f"Started Locust test: {' '.join(locust_cmd)}")
        return process
    
    async def _parse_locust_results(self, test_name: str) -> Dict[str, Any]:
        """Parse Locust CSV results."""
        results_dir = Path("load_testing/results")
        stats_file = results_dir / f"{test_name}_stats.csv"
        
        if not stats_file.exists():
            return {"error": "Locust results file not found"}
        
        try:
            # Simple CSV parsing (in production, use pandas)
            results = {
                "test_name": test_name,
                "status": "completed",
                "endpoints": {}
            }
            
            with open(stats_file, 'r') as f:
                lines = f.readlines()
                
            # Parse header and data (simplified)
            if len(lines) > 1:
                header = lines[0].strip().split(',')
                
                for line in lines[1:]:
                    data = line.strip().split(',')
                    if len(data) >= len(header):
                        endpoint_data = dict(zip(header, data))
                        endpoint_name = endpoint_data.get('Name', 'unknown')
                        results["endpoints"][endpoint_name] = endpoint_data
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to parse Locust results: {e}")
            return {"error": f"Failed to parse results: {e}"}
    
    async def _generate_unified_report(
        self,
        test_plan: TestPlan,
        load_test_results: Dict[str, Any],
        performance_results: Dict[str, Any],
        database_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate unified test report."""
        
        test_duration = datetime.now() - self.test_start_time if self.test_start_time else timedelta(0)
        
        unified_report = {
            "test_metadata": {
                "test_plan": asdict(test_plan),
                "start_time": self.test_start_time.isoformat() if self.test_start_time else None,
                "end_time": datetime.now().isoformat(),
                "duration": str(test_duration),
                "config": asdict(self.config)
            },
            "load_test_results": load_test_results,
            "performance_metrics": performance_results,
            "database_stress_results": database_results,
            "test_summary": {
                "overall_status": self._determine_overall_status(
                    load_test_results,
                    performance_results,
                    database_results
                ),
                "key_metrics": self._extract_key_metrics(
                    load_test_results,
                    performance_results,
                    database_results
                ),
                "recommendations": self._generate_test_recommendations(
                    load_test_results,
                    performance_results,
                    database_results
                )
            }
        }
        
        return unified_report
    
    def _determine_overall_status(
        self,
        load_results: Dict[str, Any],
        perf_results: Dict[str, Any],
        db_results: Dict[str, Any]
    ) -> str:
        """Determine overall test status."""
        
        # Check for critical failures
        if any("error" in results for results in [load_results, perf_results, db_results]):
            return "failed"
        
        # Check performance thresholds
        perf_api = perf_results.get("api_performance", {})
        error_rate = perf_api.get("error_rate_avg", 0)
        
        if error_rate > self.config.error_rate_threshold:
            return "degraded"
        
        # Check response times
        response_times = perf_results.get("response_times", {})
        for endpoint, metrics in response_times.items():
            if metrics.get("p95", 0) > self.config.response_time_p95_threshold:
                return "degraded"
        
        return "passed"
    
    def _extract_key_metrics(
        self,
        load_results: Dict[str, Any],
        perf_results: Dict[str, Any],
        db_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract key performance metrics."""
        
        perf_api = perf_results.get("api_performance", {})
        perf_system = perf_results.get("system_performance", {})
        
        return {
            "max_throughput_rps": perf_api.get("throughput_max", 0),
            "avg_response_time_ms": perf_api.get("response_time_avg", 0) * 1000,
            "error_rate_percent": perf_api.get("error_rate_avg", 0) * 100,
            "max_cpu_percent": perf_system.get("cpu_max", 0),
            "max_memory_percent": perf_system.get("memory_max", 0),
            "database_performance": {
                db_type: results.get("avg_operations_per_second", 0)
                for db_type, results in db_results.get("database_performance", {}).items()
            }
        }
    
    def _generate_test_recommendations(
        self,
        load_results: Dict[str, Any],
        perf_results: Dict[str, Any],
        db_results: Dict[str, Any]
    ) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Performance-based recommendations
        perf_system = perf_results.get("system_performance", {})
        
        if perf_system.get("cpu_max", 0) > 80:
            recommendations.append("Consider CPU optimization or horizontal scaling")
        
        if perf_system.get("memory_max", 0) > 85:
            recommendations.append("Memory usage is high - consider memory optimization")
        
        # Database-specific recommendations
        db_perf = db_results.get("database_performance", {})
        for db_type, metrics in db_perf.items():
            if metrics.get("avg_error_rate", 0) > 0.05:
                recommendations.append(f"{db_type}: High error rate detected - review connection pooling")
        
        # API-specific recommendations
        perf_api = perf_results.get("api_performance", {})
        if perf_api.get("error_rate_avg", 0) > self.config.error_rate_threshold:
            recommendations.append("API error rate exceeds threshold - investigate error causes")
        
        if not recommendations:
            recommendations.append("System performed within acceptable parameters")
        
        return recommendations
    
    def _generate_suite_summary(self, suite_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of the complete test suite."""
        test_results = suite_results.get("test_results", {})
        
        passed_tests = sum(
            1 for result in test_results.values()
            if result.get("test_summary", {}).get("overall_status") == "passed"
        )
        
        failed_tests = sum(
            1 for result in test_results.values()
            if "error" in result or result.get("test_summary", {}).get("overall_status") == "failed"
        )
        
        degraded_tests = sum(
            1 for result in test_results.values()
            if result.get("test_summary", {}).get("overall_status") == "degraded"
        )
        
        return {
            "total_tests": len(test_results),
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "degraded_tests": degraded_tests,
            "overall_suite_status": "passed" if failed_tests == 0 else "failed",
            "suite_recommendations": self._generate_suite_recommendations(test_results)
        }
    
    def _generate_suite_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for the entire test suite."""
        recommendations = []
        
        # Analyze patterns across all tests
        error_pattern = any(
            "error" in result for result in test_results.values()
        )
        
        if error_pattern:
            recommendations.append("Multiple test failures detected - investigate infrastructure stability")
        
        # Look for consistent performance issues
        degraded_count = sum(
            1 for result in test_results.values()
            if result.get("test_summary", {}).get("overall_status") == "degraded"
        )
        
        if degraded_count > 1:
            recommendations.append("Performance degradation in multiple scenarios - consider system optimization")
        
        return recommendations
    
    async def _save_suite_report(self, suite_results: Dict[str, Any]):
        """Save comprehensive suite report."""
        results_dir = Path("load_testing/results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = results_dir / f"scalability_suite_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(suite_results, f, indent=2, default=str)
        
        self.logger.info(f"Comprehensive report saved to {filename}")
        
        # Also create a summary report
        summary_filename = results_dir / f"scalability_summary_{timestamp}.json"
        summary = {
            "suite_metadata": suite_results["suite_metadata"],
            "suite_summary": suite_results["suite_summary"],
            "test_summaries": {
                name: result.get("test_summary", {})
                for name, result in suite_results["test_results"].items()
            }
        }
        
        with open(summary_filename, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.logger.info(f"Summary report saved to {summary_filename}")
    
    async def _cleanup_test(self):
        """Clean up test resources."""
        # Stop Locust process
        if self.locust_process and self.locust_process.poll() is None:
            self.locust_process.terminate()
            await asyncio.sleep(5)
            if self.locust_process.poll() is None:
                self.locust_process.kill()
        
        # Stop monitoring
        if self.monitoring_task:
            self.performance_monitor.stop_monitoring()
            try:
                await asyncio.wait_for(self.monitoring_task, timeout=10)
            except asyncio.TimeoutError:
                pass
    
    async def cleanup(self):
        """Final cleanup of orchestrator resources."""
        await self._cleanup_test()
        await self.performance_monitor.cleanup()
        await self.database_tester.cleanup()


# CLI Interface
async def main():
    """Main CLI interface for test orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="FisioRAG Scalability Test Orchestrator")
    parser.add_argument(
        "--scenario",
        choices=[s.value for s in TestScenario],
        help="Run single test scenario"
    )
    parser.add_argument(
        "--full-suite",
        action="store_true",
        help="Run complete scalability test suite"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Test duration in minutes (for single scenario)"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=10,
        help="Number of concurrent users (for single scenario)"
    )
    parser.add_argument(
        "--spawn-rate",
        type=float,
        default=1.0,
        help="User spawn rate per second (for single scenario)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize orchestrator
    config = LoadTestConfig()
    orchestrator = TestOrchestrator(config)
    
    try:
        await orchestrator.initialize()
        
        if args.full_suite:
            # Run complete test suite
            results = await orchestrator.run_full_scalability_suite()
            print("\n=== SCALABILITY SUITE COMPLETED ===")
            print(json.dumps(results["suite_summary"], indent=2))
            
        elif args.scenario:
            # Run single scenario
            scenario = TestScenario(args.scenario)
            test_plan = TestPlan(
                name=f"Custom {scenario.value} Test",
                scenario=scenario,
                duration_minutes=args.duration,
                concurrent_users=args.users,
                spawn_rate=args.spawn_rate
            )
            
            results = await orchestrator.run_test_plan(test_plan)
            print("\n=== TEST COMPLETED ===")
            print(json.dumps(results["test_summary"], indent=2))
            
        else:
            print("Please specify either --scenario or --full-suite")
            return 1
        
        return 0
        
    except Exception as e:
        logging.error(f"Test execution failed: {e}")
        return 1
        
    finally:
        await orchestrator.cleanup()


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
