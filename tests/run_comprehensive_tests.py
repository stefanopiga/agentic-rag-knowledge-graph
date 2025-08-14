#!/usr/bin/env python3
"""
Script di avvio per test suite completo.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.comprehensive.test_runner import ComprehensiveTestRunner


def main():
    """Entry point principale."""
    print("🧪 SISTEMA RAG - TEST SUITE COMPLETO")
    print("=" * 50)
    
    runner = ComprehensiveTestRunner()
    
    if len(sys.argv) > 1:
        # Pass arguments to test runner
        sys.argv[0] = str(Path(__file__).parent / "tests" / "comprehensive" / "test_runner.py")
        from tests.comprehensive.test_runner import main as runner_main
        runner_main()
    else:
        # Interactive mode
        print("\nScegli tipo di test:")
        print("1. 💨 Smoke tests (veloci)")
        print("2. 🗄️ Database connections")  
        print("3. ⚙️ Ingestion pipeline")
        print("4. 🔍 Query operations")
        print("5. ⚡ Performance tests")
        print("6. 🚀 Test completi")
        print("7. 📊 Genera report")
        
        choice = input("\nScelta (1-7): ").strip()
        
        try:
            if choice == "1":
                result = runner.run_smoke_tests()
            elif choice == "2":
                result = runner.run_database_tests()
            elif choice == "3":
                result = runner.run_pipeline_tests()
            elif choice == "4":
                result = runner.run_query_tests()
            elif choice == "5":
                result = runner.run_performance_tests()
            elif choice == "6":
                result = runner.run_test_suite("all", verbose=True)
            elif choice == "7":
                report_file = runner.generate_test_report()
                print(f"\n📊 Report generato: {report_file}")
                return
            else:
                print("❌ Scelta non valida")
                sys.exit(1)
            
            # Show results
            if result.get("success", False):
                print("\n✅ Test completati con successo!")
            else:
                print("\n❌ Alcuni test sono falliti.")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Test interrotti dall'utente")
            sys.exit(1)
        except Exception as e:
            print(f"\n💥 Errore durante esecuzione test: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()