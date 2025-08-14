"""
Sistema di logging centralizzato per test di sistema.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

class SystemTestLogger:
    """Logger centralizzato per test di sistema con output multipli."""
    
    def __init__(self, test_name: str, session_id: Optional[str] = None):
        self.test_name = test_name
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now()
        
        # Paths
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup loggers
        self.session_logger = self._setup_session_logger()
        self.individual_logger = self._setup_individual_logger()
        self.console_logger = self._setup_console_logger()
        
        # Risultati test
        self.results = {
            "test_name": test_name,
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "tests": [],
            "summary": {}
        }
    
    def _setup_session_logger(self) -> logging.Logger:
        """Logger per sessione completa."""
        logger = logging.getLogger(f"session_{self.session_id}")
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.INFO)
        
        # File handler
        session_file = self.logs_dir / f"test_session_{self.session_id}.log"
        fh = logging.FileHandler(session_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        return logger
    
    def _setup_individual_logger(self) -> logging.Logger:
        """Logger per test individuale."""
        logger = logging.getLogger(f"test_{self.test_name}")
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.INFO)
        
        # File handler
        individual_file = self.logs_dir / f"{self.test_name}.log"
        fh = logging.FileHandler(individual_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        return logger
    
    def _setup_console_logger(self) -> logging.Logger:
        """Logger per output console."""
        logger = logging.getLogger(f"console_{self.test_name}")
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        # Formatter colorato
        formatter = logging.Formatter(
            '🔍 %(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        return logger
    
    def log_test_start(self, test_description: str):
        """Registra inizio test."""
        msg = f"🚀 INIZIO TEST: {test_description}"
        self.session_logger.info(msg)
        self.individual_logger.info(msg)
        self.console_logger.info(msg)
        
        self.results["tests"].append({
            "description": test_description,
            "start_time": datetime.now().isoformat(),
            "status": "RUNNING"
        })
    
    def log_test_success(self, test_description: str, details: Optional[str] = None):
        """Registra successo test."""
        msg = f"✅ SUCCESSO: {test_description}"
        if details:
            msg += f" - {details}"
            
        self.session_logger.info(msg)
        self.individual_logger.info(msg)
        self.console_logger.info(msg)
        
        # Aggiorna risultati
        for test in self.results["tests"]:
            if test["description"] == test_description and test["status"] == "RUNNING":
                test["status"] = "SUCCESS"
                test["end_time"] = datetime.now().isoformat()
                test["details"] = details
                break
    
    def log_test_failure(self, test_description: str, error: str):
        """Registra fallimento test."""
        msg = f"❌ ERRORE: {test_description} - {error}"
        
        self.session_logger.error(msg)
        self.individual_logger.error(msg)
        self.console_logger.error(msg)
        
        # Aggiorna risultati
        for test in self.results["tests"]:
            if test["description"] == test_description and test["status"] == "RUNNING":
                test["status"] = "FAILURE"
                test["end_time"] = datetime.now().isoformat()
                test["error"] = error
                break
    
    def log_test_skip(self, test_description: str, reason: str):
        """Registra test saltato."""
        msg = f"⏭️ SALTATO: {test_description} - {reason}"
        
        self.session_logger.warning(msg)
        self.individual_logger.warning(msg)
        self.console_logger.warning(msg)
        
        self.results["tests"].append({
            "description": test_description,
            "start_time": datetime.now().isoformat(),
            "end_time": datetime.now().isoformat(),
            "status": "SKIPPED",
            "reason": reason
        })
    
    def log_info(self, message: str):
        """Log messaggio informativo."""
        self.session_logger.info(message)
        self.individual_logger.info(message)
        self.console_logger.info(message)
    
    def log_warning(self, message: str):
        """Log warning."""
        self.session_logger.warning(message)
        self.individual_logger.warning(message)
        self.console_logger.warning(message)
    
    def log_error(self, message: str):
        """Log errore."""
        self.session_logger.error(message)
        self.individual_logger.error(message)
        self.console_logger.error(message)
    
    def finalize(self) -> Dict[str, Any]:
        """Finalizza logging e genera summary."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Calcola statistiche
        total_tests = len(self.results["tests"])
        successful = len([t for t in self.results["tests"] if t["status"] == "SUCCESS"])
        failed = len([t for t in self.results["tests"] if t["status"] == "FAILURE"])
        skipped = len([t for t in self.results["tests"] if t["status"] == "SKIPPED"])
        
        self.results["summary"] = {
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "total_tests": total_tests,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "success_rate": successful / total_tests if total_tests > 0 else 0.0
        }
        
        # Log finale
        summary_msg = f"""
📊 SUMMARY TEST '{self.test_name}':
   ⏱️  Durata: {duration:.2f}s
   📋 Test totali: {total_tests}
   ✅ Successi: {successful}
   ❌ Fallimenti: {failed}
   ⏭️ Saltati: {skipped}
   📈 Tasso successo: {self.results['summary']['success_rate']:.1%}
"""
        
        self.session_logger.info(summary_msg)
        self.individual_logger.info(summary_msg)
        self.console_logger.info(summary_msg)
        
        # Salva risultati JSON
        results_file = self.logs_dir / f"{self.test_name}_results_{self.session_id}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        return self.results

def create_logger(test_name: str, session_id: Optional[str] = None) -> SystemTestLogger:
    """Factory per creare logger di sistema."""
    return SystemTestLogger(test_name, session_id)