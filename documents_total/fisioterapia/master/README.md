# Documentazione Medica - Fisioterapia

Questa cartella contiene la documentazione medica organizzata per aree anatomiche e specializzazioni.

## Struttura Organizzativa

### Naming Convention
I documenti devono seguire la convenzione di nomenclatura:
```
{numero_ordine}_{descrizione}.docx
```

**Esempi:**
- `01_anatomia_caviglia.docx`
- `02_patologie_comuni.docx`
- `03_riabilitazione_distorsioni.docx`

### Priorità Citazioni
Il sistema ordina automaticamente le citazioni basandosi su:
1. **Categoria anatomica** (ordine di priorità)
2. **Numero documento** all'interno della categoria

## Categorie Disponibili

### 1. caviglia_e_piede/
Documenti relativi a caviglia e piede:
- Anatomia e biomeccanica
- Patologie comuni (distorsioni, fratture)
- Protocolli riabilitativi
- Tecniche specifiche

### 2. ginocchio/
Documenti relativi al ginocchio:
- Anatomia articolare
- Lesioni legamentose
- Riabilitazione post-chirurgica
- Esercizi terapeutici

### 3. lombare/
Documenti relativi alla colonna lombare:
- Anatomia vertebrale
- Lombalgia e problematiche correlate
- Stabilizzazione lombare
- Tecniche manuali

### 4. toracico/
Documenti relativi alla colonna toracica:
- Anatomia toracica
- Mobilizzazioni specifiche
- Problematiche posturali
- Terapie manuali

### 5. lombo_pelvico/
Documenti relativi al complesso lombo-pelvico:
- Biomeccanica pelvica
- Disfunzioni del cingolo pelvico
- Approcci integrati
- Valutazione funzionale

## Formati Supportati

Il sistema supporta i seguenti formati:
- **.docx** (raccomandato per documenti medici strutturati)
- **.pdf** (per documenti scansionati o pubblicazioni)
- **.txt** (per note e documenti semplici)
- **.md** (per documentazione tecnica)

## Ingestion Incrementale

Il sistema utilizza l'ingestion incrementale:
- **Solo nuovi/modificati** documenti vengono processati
- **Tracking automatico** dello stato di ogni documento
- **Cleanup automatico** di ingestion incomplete
- **Citazioni ordinate** per priorità anatomica

## Comandi Utili

```bash
# Ingestion incrementale (default)
python ingestion/ingest.py

# Status report
python ingestion/ingest.py --status

# Cleanup documenti parziali
python ingestion/ingest.py --cleanup-partial

# Re-ingestion categoria specifica
python ingestion/ingest.py --reingest-category caviglia_e_piede

# Ingestion completa (cancella tutto)
python ingestion/ingest.py --clean
```

## Note Importanti

1. **Numerazione sequenziale**: Rispettare l'ordine numerico per citazioni corrette
2. **Backup regolari**: Mantenere backup dei documenti originali
3. **Validazione contenuti**: Verificare qualità e accuratezza medica
4. **Aggiornamenti**: Documentare modifiche e versioning

---

*Sistema Agentic RAG per Formazione Medica*  
*Versione con Gestione Incrementale e Citazioni Strutturate*