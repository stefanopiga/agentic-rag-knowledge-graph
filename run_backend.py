#!/usr/bin/env python3
"""
Entry point per avviare il backend FastAPI dell'agentic RAG system.
Risolve i problemi di import relativi.
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Aggiungi il path del progetto al PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Carica le variabili ambiente
load_dotenv()

# Import del modulo agent dopo aver sistemato il path
from agent.api import app

# Esponi app a livello globale per uvicorn
app = app

if __name__ == "__main__":
    # Configurazione dal file env
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 8000))
    APP_ENV = os.getenv("APP_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    print(f"🚀 Avvio backend FisioRAG su {APP_HOST}:{APP_PORT}")
    print(f"📋 Ambiente: {APP_ENV}")
    print(f"📝 Log Level: {LOG_LEVEL}")
    
    uvicorn.run(
        "run_backend:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=False,  # Disabilita reload per evitare problemi
        log_level=LOG_LEVEL.lower()
    )
