"""
Runner unificato per tutti i test del sistema.
"""

import pytest
import sys
import asyncio
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class ComprehensiveTestRunner:
    """Runner per test completi del sistema."""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.test_modules = [
            "test_database_connections",
            "test_ingestion_pipeline", 
            "test_query_operations"
        ]
        self.results = {}
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging per test runner."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        return logging.getLogger(__name__)
    
    def run_test_suite(
        self,
        test_type: str = "all",
        verbose: bool = False,
        fail_fast: bool = False,
        parallel: bool = False
    ) -> Dict[str, Any]:
        """
        Esegue suite test completa.
        
        Args:
            test_type: Tipo test ("all", "unit", "integration", "slow")
            verbose: Output verboso
            fail_fast: Ferma al primo fallimento
            parallel: Esecuzione parallela
            
        Returns:
            Risultati test
        """
        self.logger.info(f"🚀 Avvio test suite completa - Tipo: {test_type}")
        start_time = datetime.now()
        
        # Build pytest arguments
        pytest_args = self._build_pytest_args(test_type, verbose, fail_fast, parallel)
        
        # Run tests
        exit_code = pytest.main(pytest_args)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Collect results
        results = {
            "test_type": test_type,
            "exit_code": exit_code,
            "duration_seconds": duration,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "success": exit_code == 0
        }
        
        self._log_results(results)
        return results
    
    def _build_pytest_args(
        self,
        test_type: str,
        verbose: bool,
        fail_fast: bool,
        parallel: bool
    ) -> List[str]:
        """Costruisce argomenti pytest."""
        args = [str(Path(__file__).parent)]
        
        # Verbosity
        if verbose:
            args.extend(["-v", "-s"])
        
        # Fail fast
        if fail_fast:
            args.append("-x")
        
        # Parallel execution
        if parallel:
            args.extend(["-n", "auto"])
        
        # Test type filters
        if test_type == "unit":
            args.extend(["-m", "unit"])
        elif test_type == "integration":
            args.extend(["-m", "integration"])
        elif test_type == "slow":
            args.extend(["-m", "slow"])
        elif test_type == "fast":
            args.extend(["-m", "not slow"])
        
        # Coverage
        args.extend([
            "--cov=agent",
            "--cov=ingestion", 
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov/comprehensive"
        ])
        
        # Output format
        args.extend([
            "--tb=short",
            "--strict-markers",
            "--strict-config"
        ])
        
        return args
    
    def _log_results(self, results: Dict[str, Any]):
        """Log risultati test."""
        if results["success"]:
            self.logger.info(f"✅ Test suite completata con successo in {results['duration_seconds']:.2f}s")
        else:
            self.logger.error(f"❌ Test suite fallita (exit code: {results['exit_code']}) in {results['duration_seconds']:.2f}s")
    
    def run_database_tests(self) -> Dict[str, Any]:
        """Esegue solo test database."""
        self.logger.info("🗄️ Esecuzione test database")
        
        args = [
            str(Path(__file__).parent / "test_database_connections.py"),
            "-v",
            "--tb=short"
        ]
        
        exit_code = pytest.main(args)
        return {"module": "database", "success": exit_code == 0}
    
    def run_pipeline_tests(self) -> Dict[str, Any]:
        """Esegue solo test pipeline."""
        self.logger.info("⚙️ Esecuzione test pipeline")
        
        args = [
            str(Path(__file__).parent / "test_ingestion_pipeline.py"),
            "-v",
            "--tb=short"
        ]
        
        exit_code = pytest.main(args)
        return {"module": "pipeline", "success": exit_code == 0}
    
    def run_query_tests(self) -> Dict[str, Any]:
        """Esegue solo test query."""
        self.logger.info("🔍 Esecuzione test query")
        
        args = [
            str(Path(__file__).parent / "test_query_operations.py"),
            "-v", 
            "--tb=short"
        ]
        
        exit_code = pytest.main(args)
        return {"module": "query", "success": exit_code == 0}
    
    def run_smoke_tests(self) -> Dict[str, Any]:
        """Esegue test smoke rapidi."""
        self.logger.info("💨 Esecuzione smoke tests")
        
        args = [
            str(Path(__file__).parent),
            "-v",
            "-m", "not slow",
            "--maxfail=5",
            "--tb=line"
        ]
        
        exit_code = pytest.main(args)
        return {"type": "smoke", "success": exit_code == 0}
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Esegue test performance."""
        self.logger.info("⚡ Esecuzione performance tests")
        
        args = [
            str(Path(__file__).parent),
            "-v",
            "-m", "slow",
            "--tb=short"
        ]
        
        exit_code = pytest.main(args)
        return {"type": "performance", "success": exit_code == 0}
    
    def generate_test_report(self) -> str:
        """Genera report test dettagliato."""
        self.logger.info("📊 Generazione report test")
        
        # Run tests with detailed reporting
        args = [
            str(Path(__file__).parent),
            "--html=test_report.html",
            "--self-contained-html",
            "--cov=agent",
            "--cov=ingestion",
            "--cov-report=html:htmlcov/full_report",
            "--cov-report=term",
            "--junit-xml=test_results.xml"
        ]
        
        pytest.main(args)
        return "test_report.html"


def main():
    """Main function per CLI."""
    parser = argparse.ArgumentParser(description="Runner test completo")
    
    parser.add_argument(
        "--type", "-t",
        choices=["all", "unit", "integration", "slow", "fast", "smoke", "performance"],
        default="all",
        help="Tipo di test da eseguire"
    )
    
    parser.add_argument(
        "--module", "-m",
        choices=["database", "pipeline", "query"],
        help="Modulo specifico da testare"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Output verboso"
    )
    
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Ferma al primo fallimento"
    )
    
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Esecuzione parallela"
    )
    
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="Genera report dettagliato"
    )
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    if args.report:
        report_file = runner.generate_test_report()
        print(f"📊 Report generato: {report_file}")
        return
    
    if args.module:
        if args.module == "database":
            result = runner.run_database_tests()
        elif args.module == "pipeline":
            result = runner.run_pipeline_tests()
        elif args.module == "query":
            result = runner.run_query_tests()
    elif args.type == "smoke":
        result = runner.run_smoke_tests()
    elif args.type == "performance":
        result = runner.run_performance_tests()
    else:
        result = runner.run_test_suite(
            test_type=args.type,
            verbose=args.verbose,
            fail_fast=args.fail_fast,
            parallel=args.parallel
        )
    
    # Exit with appropriate code
    exit_code = 0 if result.get("success", False) else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()