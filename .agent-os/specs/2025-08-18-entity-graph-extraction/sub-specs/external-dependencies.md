# External Dependencies

This specification requires new external dependencies for NLP entity extraction functionality.

## New Dependencies Required

- **spaCy** (>=3.7.0) - Core NLP library per entity extraction
  - **Justification:** Industry standard per NER con modelli pre-trained robusti, performance elevate, integrazione semplice
  - **Usage:** Entity extraction da document chunks, NER pipeline configuration

- **en_core_web_sm** (>=3.7.0) - spaCy English model small
  - **Justification:** Modello lightweight per entity extraction generale, balance tra performance e accuracy
  - **Usage:** Named Entity Recognition per PERSON, ORG, GPE, DATE, MONEY, PRODUCT entities
  - **Alternative:** en_core_web_lg per accuracy superiore se performance lo permette

## Installation Commands

```bash
pip install spacy>=3.7.0
python -m spacy download en_core_web_sm
```

## Configuration Requirements

- **Model Loading**: Configurare lazy loading di spaCy model per evitare overhead startup
- **Memory Management**: spaCy model richiede ~15MB RAM, considerare model sharing tra worker processes
- **Error Handling**: Implementare fallback se modello spaCy non disponibile (skip entity extraction, log warning)