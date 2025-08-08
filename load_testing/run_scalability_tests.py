#!/usr/bin/env python3
"""
Main entry point for FisioRAG scalability testing.
Simplified interface for running comprehensive scalability tests.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from config import LoadTestConfig, TestScenario
from test_orchestrator import TestOrchestrator, TestPlan


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory
    logs_dir = Path("load_testing/logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Setup file and console logging
    log_filename = logs_dir / f"scalability_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_filename


def print_banner():
    """Print test banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║              FisioRAG Scalability Testing Suite             ║
║                                                              ║
║  Comprehensive load testing for production readiness        ║
║  • API Load Testing with Locust                             ║
║  • Real-time Performance Monitoring                         ║
║  • Database Stress Testing                                  ║
║  • Automated Report Generation                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


async def quick_baseline_test():
    """Run a quick baseline test (5 minutes)."""
    print("\n🚀 Running Quick Baseline Test (5 minutes)")
    print("=" * 60)
    
    config = LoadTestConfig()
    orchestrator = TestOrchestrator(config)
    
    test_plan = TestPlan(
        name="Quick Baseline Test",
        scenario=TestScenario.BASELINE,
        duration_minutes=5,
        concurrent_users=10,
        spawn_rate=2.0,
        warmup_duration_seconds=30
    )
    
    try:
        await orchestrator.initialize()
        results = await orchestrator.run_test_plan(test_plan)
        
        # Print summary
        summary = results.get("test_summary", {})
        print(f"\n✅ Test Status: {summary.get('overall_status', 'unknown').upper()}")
        
        key_metrics = summary.get("key_metrics", {})
        print(f"📊 Max Throughput: {key_metrics.get('max_throughput_rps', 0):.1f} RPS")
        print(f"⏱️  Avg Response Time: {key_metrics.get('avg_response_time_ms', 0):.1f} ms")
        print(f"❌ Error Rate: {key_metrics.get('error_rate_percent', 0):.2f}%")
        
        return results
        
    finally:
        await orchestrator.cleanup()


async def peak_hours_simulation():
    """Run peak hours simulation test (15 minutes)."""
    print("\n🎯 Running Peak Hours Simulation (15 minutes)")
    print("=" * 60)
    print("Simulating university exam period traffic...")
    
    config = LoadTestConfig()
    orchestrator = TestOrchestrator(config)
    
    test_plan = TestPlan(
        name="Peak Hours Simulation",
        scenario=TestScenario.PEAK_HOURS,
        duration_minutes=15,
        concurrent_users=50,
        spawn_rate=5.0,
        warmup_duration_seconds=60
    )
    
    try:
        await orchestrator.initialize()
        results = await orchestrator.run_test_plan(test_plan)
        
        # Print detailed summary
        summary = results.get("test_summary", {})
        print(f"\n✅ Test Status: {summary.get('overall_status', 'unknown').upper()}")
        
        key_metrics = summary.get("key_metrics", {})
        print(f"📊 Max Throughput: {key_metrics.get('max_throughput_rps', 0):.1f} RPS")
        print(f"⏱️  Avg Response Time: {key_metrics.get('avg_response_time_ms', 0):.1f} ms")
        print(f"❌ Error Rate: {key_metrics.get('error_rate_percent', 0):.2f}%")
        print(f"💾 Max CPU: {key_metrics.get('max_cpu_percent', 0):.1f}%")
        print(f"🧠 Max Memory: {key_metrics.get('max_memory_percent', 0):.1f}%")
        
        # Show recommendations
        recommendations = summary.get("recommendations", [])
        if recommendations:
            print("\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        return results
        
    finally:
        await orchestrator.cleanup()


async def stress_test():
    """Run comprehensive stress test (30 minutes)."""
    print("\n💪 Running Comprehensive Stress Test (30 minutes)")
    print("=" * 60)
    print("Testing system breaking points and recovery...")
    
    config = LoadTestConfig()
    orchestrator = TestOrchestrator(config)
    
    test_plan = TestPlan(
        name="Comprehensive Stress Test",
        scenario=TestScenario.STRESS_TEST,
        duration_minutes=30,
        concurrent_users=200,
        spawn_rate=10.0,
        warmup_duration_seconds=120
    )
    
    try:
        await orchestrator.initialize()
        results = await orchestrator.run_test_plan(test_plan)
        
        # Detailed analysis
        summary = results.get("test_summary", {})
        status = summary.get("overall_status", "unknown")
        
        print(f"\n✅ Test Status: {status.upper()}")
        
        if status == "passed":
            print("🎉 System handled stress test successfully!")
        elif status == "degraded":
            print("⚠️  System showed degraded performance under stress")
        else:
            print("❌ System failed under stress conditions")
        
        key_metrics = summary.get("key_metrics", {})
        print(f"📊 Max Throughput: {key_metrics.get('max_throughput_rps', 0):.1f} RPS")
        print(f"⏱️  Avg Response Time: {key_metrics.get('avg_response_time_ms', 0):.1f} ms")
        print(f"❌ Error Rate: {key_metrics.get('error_rate_percent', 0):.2f}%")
        
        # Database performance
        db_perf = key_metrics.get("database_performance", {})
        print("\n🗄️  Database Performance:")
        for db_type, ops_per_sec in db_perf.items():
            print(f"   {db_type}: {ops_per_sec:.1f} ops/sec")
        
        return results
        
    finally:
        await orchestrator.cleanup()


async def full_production_readiness_suite():
    """Run complete production readiness test suite."""
    print("\n🏭 Running Full Production Readiness Suite")
    print("=" * 60)
    print("This comprehensive test takes 2-3 hours and validates production readiness.")
    print("Tests include: Baseline, Peak Hours, Stress, Spike, and Endurance scenarios.")
    
    config = LoadTestConfig()
    orchestrator = TestOrchestrator(config)
    
    try:
        await orchestrator.initialize()
        results = await orchestrator.run_full_scalability_suite()
        
        # Print comprehensive summary
        suite_summary = results.get("suite_summary", {})
        print(f"\n🎯 PRODUCTION READINESS RESULTS")
        print("=" * 60)
        print(f"Total Tests: {suite_summary.get('total_tests', 0)}")
        print(f"✅ Passed: {suite_summary.get('passed_tests', 0)}")
        print(f"⚠️  Degraded: {suite_summary.get('degraded_tests', 0)}")
        print(f"❌ Failed: {suite_summary.get('failed_tests', 0)}")
        
        overall_status = suite_summary.get('overall_suite_status', 'unknown')
        if overall_status == "passed":
            print("\n🎉 SYSTEM IS PRODUCTION READY! 🎉")
        else:
            print("\n⚠️  SYSTEM NEEDS OPTIMIZATION BEFORE PRODUCTION")
        
        # Show suite recommendations
        recommendations = suite_summary.get("suite_recommendations", [])
        if recommendations:
            print("\n💡 Production Recommendations:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        return results
        
    finally:
        await orchestrator.cleanup()


def main():
    """Main CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="FisioRAG Scalability Testing Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scalability_tests.py --quick          # 5-minute baseline test
  python run_scalability_tests.py --peak           # 15-minute peak hours test
  python run_scalability_tests.py --stress         # 30-minute stress test
  python run_scalability_tests.py --full-suite     # Complete 2-3 hour suite
  
Environment Variables:
  LOAD_TEST_API_URL     - Target API URL (default: http://localhost:8000)
  DATABASE_URL          - PostgreSQL connection string
  NEO4J_URI            - Neo4j connection URI
  REDIS_URL            - Redis connection URL
        """
    )
    
    # Test selection (mutually exclusive)
    test_group = parser.add_mutually_exclusive_group(required=True)
    test_group.add_argument(
        "--quick",
        action="store_true",
        help="Quick baseline test (5 minutes)"
    )
    test_group.add_argument(
        "--peak",
        action="store_true",
        help="Peak hours simulation (15 minutes)"
    )
    test_group.add_argument(
        "--stress",
        action="store_true",
        help="Comprehensive stress test (30 minutes)"
    )
    test_group.add_argument(
        "--full-suite",
        action="store_true",
        help="Complete production readiness suite (2-3 hours)"
    )
    
    # Options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("LOAD_TEST_API_URL", "http://localhost:8000"),
        help="Target API URL"
    )
    
    args = parser.parse_args()
    
    # Setup
    print_banner()
    log_file = setup_logging(args.verbose)
    
    print(f"🔗 Target API: {args.api_url}")
    print(f"📝 Log file: {log_file}")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Validate environment
    if not os.getenv("DATABASE_URL"):
        print("⚠️  Warning: DATABASE_URL not set - database tests will be skipped")
    
    # Run selected test
    try:
        if args.quick:
            asyncio.run(quick_baseline_test())
        elif args.peak:
            asyncio.run(peak_hours_simulation())
        elif args.stress:
            asyncio.run(stress_test())
        elif args.full_suite:
            asyncio.run(full_production_readiness_suite())
        
        print(f"\n✅ Testing completed successfully!")
        print(f"📊 Results saved in: load_testing/results/")
        print(f"📝 Logs saved in: {log_file}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logging.error(f"Test execution failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
