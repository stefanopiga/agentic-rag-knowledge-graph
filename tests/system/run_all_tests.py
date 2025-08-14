"""
Master Test Runner - Esegue tutti i test di sistema.

Script principale per eseguire l'intera suite di test del sistema Agentic RAG.
"""

import os
import sys
import asyncio
import argparse
import traceback
from datetime import datetime
from pathlib import Path
import json
from dotenv import load_dotenv

# Carica environment variables all'inizio
load_dotenv()

# Deprecazione esecuzione locale per default: richiede esplicito consenso via env
if os.getenv("ALLOW_LOCAL_SYSTEM_TESTS", "0").lower() not in ("1", "true", "yes"):
    print("⚠️ Esecuzione locale dei system tests è deprecata. Usa il workflow CI cloud (cloud-tests.yml) o imposta ALLOW_LOCAL_SYSTEM_TESTS=1 per forzare.")
    sys.exit(0)

# Aggiungi project root al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.system.test_logger import create_logger
from tests.system.test_infrastructure import InfrastructureTests
from tests.system.test_pipeline import PipelineTests
from tests.system.test_integration import IntegrationTests
from tests.system.test_end_to_end import EndToEndTests


class MasterTestRunner:
    """Runner principale per tutti i test di sistema."""
    
    def __init__(self, args):
        self.args = args
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = create_logger("master_runner", self.session_id)
        
        # Risultati aggregati
        self.all_results = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "phases": {},
            "summary": {}
        }
        
        # Fasi di test
        self.test_phases = [
            ("infrastructure", "🏗️ Infrastruttura", InfrastructureTests),
            ("pipeline", "⚙️ Pipeline", PipelineTests),
            ("integration", "🔗 Integrazione", IntegrationTests),
            ("end_to_end", "🚀 End-to-End", EndToEndTests)
        ]
    
    async def run_all_tests(self) -> dict:
        """Esegue tutte le fasi di test."""
        self.logger.log_info("🎯 INIZIANDO MASTER TEST RUNNER")
        self.logger.log_info(f"📅 Session ID: {self.session_id}")
        self.logger.log_info(f"🔧 Modalità: {'FAST' if self.args.fast else 'COMPLETA'}")
        
        try:
            # Header informativo
            self._log_system_info()
            
            # Esegui fasi di test
            for phase_id, phase_name, test_class in self.test_phases:
                
                # Skip fasi se modalità fast
                if self.args.fast and phase_id in ['integration', 'end_to_end']:
                    self.logger.log_test_skip(
                        f"{phase_name} Tests",
                        "Saltato in modalità fast"
                    )
                    continue
                
                # Skip fase specifica se richiesto
                if hasattr(self.args, f'skip_{phase_id}') and getattr(self.args, f'skip_{phase_id}'):
                    self.logger.log_test_skip(
                        f"{phase_name} Tests",
                        f"Saltato per flag --skip-{phase_id}"
                    )
                    continue
                
                await self._run_phase(phase_id, phase_name, test_class)
            
            # Genera summary finale
            self._generate_final_summary()
            
        except KeyboardInterrupt:
            self.logger.log_warning("⚠️ Test interrotti dall'utente")
        except Exception as e:
            self.logger.log_error(f"Errore critico nel master runner: {e}")
            self.logger.log_error(traceback.format_exc())
        
        finally:
            return self.logger.finalize()
    
    async def _run_phase(self, phase_id: str, phase_name: str, test_class):
        """Esegue una singola fase di test."""
        self.logger.log_info(f"\n{'='*60}")
        self.logger.log_info(f"🎯 FASE: {phase_name}")
        self.logger.log_info(f"{'='*60}")
        
        try:
            # Inizializza tester
            tester = test_class()
            
            # Esegui test della fase
            phase_results = await tester.run_all_tests()
            
            # Salva risultati
            self.all_results["phases"][phase_id] = {
                "name": phase_name,
                "results": phase_results,
                "status": "COMPLETED"
            }
            
            # Log riassunto fase
            summary = phase_results.get("summary", {})
            self.logger.log_info(f"📊 {phase_name} - Risultati:")
            self.logger.log_info(f"   ✅ Successi: {summary.get('successful', 0)}")
            self.logger.log_info(f"   ❌ Fallimenti: {summary.get('failed', 0)}")
            self.logger.log_info(f"   ⏭️ Saltati: {summary.get('skipped', 0)}")
            self.logger.log_info(f"   📈 Tasso successo: {summary.get('success_rate', 0):.1%}")
            
        except Exception as e:
            self.logger.log_error(f"Errore nella fase {phase_name}: {e}")
            self.all_results["phases"][phase_id] = {
                "name": phase_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    def _log_system_info(self):
        """Log informazioni di sistema."""
        self.logger.log_info("\n📋 INFORMAZIONI SISTEMA:")
        self.logger.log_info(f"   🐍 Python: {sys.version.split()[0]}")
        self.logger.log_info(f"   💻 OS: {os.name}")
        self.logger.log_info(f"   📁 Working Dir: {os.getcwd()}")
        
        # Environment variables critiche
        env_vars = [
            'LLM_PROVIDER', 'LLM_CHOICE', 'EMBEDDING_MODEL',
            'POSTGRES_HOST', 'NEO4J_URI'
        ]
        
        self.logger.log_info("   🔑 Environment:")
        for var in env_vars:
            value = os.environ.get(var, 'NOT SET')
            if 'API_KEY' in var and value != 'NOT SET':
                value = value[:8] + "..." if len(value) > 8 else "***"
            self.logger.log_info(f"      {var}: {value}")
    
    def _generate_final_summary(self):
        """Genera summary finale di tutti i test."""
        self.logger.log_info("\n" + "="*80)
        self.logger.log_info("📊 SUMMARY FINALE - AGENTIC RAG SYSTEM TESTS")
        self.logger.log_info("="*80)
        
        # Statistiche aggregate
        total_tests = 0
        total_successful = 0
        total_failed = 0
        total_skipped = 0
        
        phases_completed = 0
        phases_with_errors = 0
        
        for phase_id, phase_data in self.all_results["phases"].items():
            if phase_data["status"] == "COMPLETED":
                phases_completed += 1
                summary = phase_data["results"].get("summary", {})
                total_tests += summary.get("total_tests", 0)
                total_successful += summary.get("successful", 0)
                total_failed += summary.get("failed", 0)
                total_skipped += summary.get("skipped", 0)
            else:
                phases_with_errors += 1
        
        # Log statistics
        self.logger.log_info(f"🎯 FASI COMPLETATE: {phases_completed}/{len(self.test_phases)}")
        self.logger.log_info(f"📋 TEST TOTALI: {total_tests}")
        self.logger.log_info(f"✅ SUCCESSI: {total_successful}")
        self.logger.log_info(f"❌ FALLIMENTI: {total_failed}")
        self.logger.log_info(f"⏭️ SALTATI: {total_skipped}")
        
        if total_tests > 0:
            success_rate = total_successful / total_tests
            self.logger.log_info(f"📈 TASSO SUCCESSO GLOBALE: {success_rate:.1%}")
        
        # Status finale
        if total_failed == 0 and phases_with_errors == 0:
            final_status = "🎉 TUTTI I TEST SUPERATI!"
            status_emoji = "✅"
        elif total_failed <= 2 and phases_with_errors == 0:
            final_status = "⚠️ SISTEMA PRINCIPALMENTE FUNZIONANTE"
            status_emoji = "⚠️"
        else:
            final_status = "❌ PROBLEMI CRITICI RILEVATI"
            status_emoji = "❌"
        
        self.logger.log_info(f"\n{status_emoji} STATUS FINALE: {final_status}")
        
        # Raccomandazioni
        self._generate_recommendations(total_failed, phases_with_errors)
        
        # Salva risultati finali
        self.all_results["summary"] = {
            "end_time": datetime.now().isoformat(),
            "phases_completed": phases_completed,
            "phases_with_errors": phases_with_errors,
            "total_tests": total_tests,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "success_rate": total_successful / total_tests if total_tests > 0 else 0.0,
            "final_status": final_status
        }
    
    def _generate_recommendations(self, total_failed: int, phases_with_errors: int):
        """Genera raccomandazioni basate sui risultati."""
        self.logger.log_info("\n💡 RACCOMANDAZIONI:")
        
        if total_failed == 0 and phases_with_errors == 0:
            self.logger.log_info("   🚀 Sistema pronto per ingestion documenti reali")
            self.logger.log_info("   📱 Testare interfaccia Django e API")
            self.logger.log_info("   🎯 Procedere con deployment development")
        
        elif total_failed <= 2:
            self.logger.log_info("   🔧 Verificare fallimenti minori prima di procedere")
            self.logger.log_info("   ✅ Sistema base funzionante")
            self.logger.log_info("   📋 Consultare log individuali per dettagli")
        
        else:
            self.logger.log_info("   🚨 Risolvere problemi critici prima di procedere")
            self.logger.log_info("   🔍 Verificare configurazione database")
            self.logger.log_info("   🔑 Controllare variabili environment")
            self.logger.log_info("   📞 Consultare documentazione setup")
        
        # Link ai log
        logs_dir = Path("logs")
        if logs_dir.exists():
            self.logger.log_info(f"\n📁 LOG DETTAGLIATI DISPONIBILI IN: {logs_dir.resolve()}")
            self.logger.log_info(f"   📄 Session log: test_session_{self.session_id}.log")
            self.logger.log_info("   📄 Log individuali: infrastructure.log, pipeline.log, ...")


def create_arg_parser():
    """Crea parser per argomenti CLI."""
    parser = argparse.ArgumentParser(
        description="Master Test Runner per Agentic RAG System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi d'uso:
  python run_all_tests.py                    # Test completi
  python run_all_tests.py --fast            # Solo infrastruttura + pipeline
  python run_all_tests.py --skip-integration # Salta test integrazione
  python run_all_tests.py --skip-end-to-end # Salta test end-to-end
  python run_all_tests.py --verbose         # Output dettagliato
        """
    )
    
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Modalità veloce (solo infrastruttura + pipeline)'
    )
    
    parser.add_argument(
        '--skip-infrastructure',
        action='store_true',
        help='Salta test infrastruttura'
    )
    
    parser.add_argument(
        '--skip-pipeline',
        action='store_true',
        help='Salta test pipeline'
    )
    
    parser.add_argument(
        '--skip-integration',
        action='store_true',
        help='Salta test integrazione'
    )
    
    parser.add_argument(
        '--skip-end-to-end',
        action='store_true',
        help='Salta test end-to-end'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Output dettagliato'
    )
    
    return parser


async def main():
    """Funzione principale."""
    parser = create_arg_parser()
    args = parser.parse_args()
    
    # Crea e esegui runner
    runner = MasterTestRunner(args)
    results = await runner.run_all_tests()
    
    # Return code basato sui risultati
    summary = results.get("summary", {})
    failed_tests = summary.get("failed", 0)
    
    if failed_tests == 0:
        return 0  # Successo
    elif failed_tests <= 2:
        return 1  # Warning
    else:
        return 2  # Errore critico


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrotti dall'utente")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Errore critico: {e}")
        sys.exit(1)