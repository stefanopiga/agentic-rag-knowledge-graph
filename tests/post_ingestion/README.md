# tests/post_ingestion/README.md

## Suite di Test di Validazione Post-Ingestione

### Obiettivo

Questa suite di test è progettata per **verificare e validare i dati** che sono il prodotto di un'esecuzione di ingestione manuale. A differenza dei test di sistema, questa suite **non pulisce i database** prima dell'esecuzione, ma opera sui dati esistenti per confermarne l'integrità.

### Utilizzo

Per eseguire questa suite di test di validazione, utilizzare lo script dedicato:

```bash
python -m tests.post_ingestion.run_verification
```

Lo script eseguirà specificamente i test contenuti in `test_ingestion_product.py` e fornirà un report dettagliato.

### Logica dei Test

La suite esegue i seguenti controlli:

1.  **Validazione PostgreSQL**:
    *   Verifica che il documento principale sia stato creato correttamente nella tabella `documents`.
    *   Verifica che il numero di `chunks` associati al documento sia corretto.
    *   Verifica l'integrità dei singoli `chunks` (es. presenza di embedding).

2.  **Validazione Neo4j (Knowledge Graph)**:
    *   Verifica l'esistenza del nodo `:Document` corrispondente.
    *   Verifica l'esistenza e il numero corretto di nodi `:Chunk` e relazioni `[:HAS_CHUNK]`.
    *   Verifica l'esistenza e il numero corretto di nodi `:Episode` e relazioni `[:PART_OF]`.

Questa suite è uno strumento essenziale per confermare rapidamente e in modo affidabile il successo di un'operazione di ingestione dati.
