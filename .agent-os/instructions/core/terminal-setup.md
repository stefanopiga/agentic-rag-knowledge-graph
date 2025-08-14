# Terminal Setup per Progetti Python

## Attivazione Automatica Ambiente Virtuale

Per progetti che utilizzano ambienti virtuali Python, TUTTI i comandi devono essere preceduti dall'attivazione dell'ambiente.

### Regola Generale

**PRIMA** di eseguire qualsiasi comando Python, pip, o comando di progetto:

1. **Verificare** la presenza di `venv/` nella directory root
2. **Attivare** l'ambiente virtuale
3. **Poi** eseguire il comando richiesto

### Sintassi Corretta

#### Windows:

```cmd
venv\Scripts\activate && [COMANDO]
```

#### Linux/macOS:

```bash
source venv/bin/activate && [COMANDO]
```

### Esempi Pratici

```cmd
# ❌ SCORRETTO
python -m agent.api
pip install package

# ✅ CORRETTO
venv\Scripts\activate && python -m agent.api
venv\Scripts\activate && pip install package
```

### Comando Compositi

Per comandi che richiedono cambio directory:

```cmd
# ✅ CORRETTO
venv\Scripts\activate && cd fisio_rag_saas && python manage.py runserver
venv\Scripts\activate && cd frontend && pnpm install
```

## Rilevamento Automatico

Se nella directory root è presente:

- `venv/` directory
- `requirements.txt` file
- `pyproject.toml` file

Allora il progetto richiede ambiente virtuale attivo.
