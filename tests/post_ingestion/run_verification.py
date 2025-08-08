import pytest
import sys
from pathlib import Path

# Aggiungi il percorso del progetto al sys.path
# Questo assicura che i moduli del progetto possano essere importati correttamente
# quando lo script viene eseguito come modulo (python -m)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

if __name__ == "__main__":
    # Esegui pytest sul file di test specifico
    # -v: verbose, per un output dettagliato
    # -s: per mostrare l'output di print() durante l'esecuzione
    pytest.main(["-v", "-s", "tests/post_ingestion/test_ingestion_product.py"])
