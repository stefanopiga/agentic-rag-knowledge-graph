# Agent OS - Pattern di Customizzazione

## Overview

Dopo l'analisi del codebase, ho identificato pattern di customizzazione ricorrenti che permettono di adattare il sistema Agent OS a diversi domini e use cases.

## 🎯 Pattern 1: Domain Specialization

### Cosa Modificare

```python
# agent/prompts.py
SYSTEM_PROMPT = """You are an intelligent AI assistant specializing in [YOUR_DOMAIN]..."""

# Esempio per Legal:
LEGAL_PROMPT = """You are a legal research assistant specializing in contract analysis and compliance. You have access to a database of legal documents and can analyze contracts, identify clauses, and track legal relationships."""
```

### Files Coinvolti

- `agent/prompts.py` - System prompt customization
- `ingestion/graph_builder.py` - Entity types per dominio
- `agent/models.py` - Domain-specific data models

## 🔍 Pattern 2: Custom Search Logic

### Attuale Implementation

```python
# agent/prompts.py (line 27)
"Use the knowledge graph tool only when the user asks about two companies in the same question."
```

### Customization Examples

```python
# Per Legal Domain:
"Use knowledge graph for relationship queries (party-to-party, contract hierarchies). Use vector search for clause analysis and precedent finding."

# Per Medical Domain:
"Use knowledge graph for patient-condition relationships and drug interactions. Use vector search for symptom matching and treatment protocols."
```

## 📊 Pattern 3: Entity Type Customization

### Current Entities (Big Tech)

```python
# Da graph_builder.py
entities = ["companies", "technologies", "people", "locations"]
```

### Domain-Specific Entities

```python
# Legal Domain
entities = ["parties", "contracts", "clauses", "courts", "laws", "dates"]

# Medical Domain
entities = ["patients", "conditions", "treatments", "medications", "doctors", "hospitals"]

# Finance Domain
entities = ["clients", "accounts", "transactions", "products", "regulations", "institutions"]
```

## 🗄️ Pattern 4: Schema Extension

### Base Schema Extension

```sql
-- sql/schema.sql extension example
ALTER TABLE documents ADD COLUMN document_type VARCHAR(50);
ALTER TABLE documents ADD COLUMN jurisdiction VARCHAR(100); -- For legal
ALTER TABLE documents ADD COLUMN patient_id UUID; -- For medical
ALTER TABLE chunks ADD COLUMN confidence_score FLOAT;
```

### Metadata Enrichment

```python
# agent/models.py
class LegalDocumentMetadata(BaseModel):
    document_type: Literal["contract", "policy", "regulation"]
    jurisdiction: str
    effective_date: Optional[datetime]
    expiration_date: Optional[datetime]
    parties: List[str]
```

## 🔧 Pattern 5: Custom Tools

### Current Tools Structure

```python
# agent/tools.py
@tool
async def vector_search_tool(input_data: VectorSearchInput) -> List[ChunkResult]:
    # Implementation
```

### Custom Tool Examples

```python
# Legal-specific tool
@tool
async def contract_expiration_tool(input_data: ExpirationSearchInput) -> List[ContractResult]:
    """Find contracts expiring within specified timeframe."""

# Medical-specific tool
@tool
async def drug_interaction_tool(input_data: DrugInteractionInput) -> List[InteractionResult]:
    """Check for drug interactions and contraindications."""
```

## 📚 Pattern 6: Document Processing

### Current Processing (Markdown)

```python
# ingestion/ingest.py
def process_markdown_files(folder_path: str):
    # Current implementation
```

### Multi-Format Processing

```python
def process_documents(folder_path: str, supported_formats: List[str]):
    processors = {
        '.pdf': process_pdf,
        '.docx': process_word,
        '.csv': process_csv,
        '.json': process_json
    }
```

## 🎨 Pattern 7: UI Customization

### Current CLI

```python
# cli.py
print("🤖 Agentic RAG with Knowledge Graph CLI")
```

### Domain-Specific CLI

```python
# Legal CLI
print("⚖️ Legal Research Assistant")
print("📋 Contract Analysis System")

# Medical CLI
print("🏥 Medical Knowledge Assistant")
print("💊 Clinical Decision Support")
```

## ⚡ Pattern 8: Performance Optimization

### Configuration per Dominio

```python
# Domain-specific configs
LEGAL_CONFIG = {
    "chunk_size": 1000,  # Longer for contracts
    "overlap": 200,
    "embedding_model": "text-embedding-3-large",  # Higher precision
    "graph_depth": 3  # Complex entity relationships
}

MEDICAL_CONFIG = {
    "chunk_size": 512,   # Shorter for precise medical info
    "overlap": 100,
    "embedding_model": "text-embedding-3-small",  # Speed over precision
    "graph_depth": 2  # Direct relationships
}
```

## 🔐 Pattern 9: Security & Compliance

### Privacy-Aware Processing

```python
# Custom processing per requirements
class PrivacyAwareProcessor:
    def __init__(self, privacy_level: Literal["public", "internal", "confidential"]):
        if privacy_level == "confidential":
            self.use_local_llm = True
            self.mask_entities = True

    def process_sensitive_document(self, doc: str) -> ProcessedDocument:
        if self.mask_entities:
            doc = self.mask_personal_data(doc)
        return self.process(doc)
```

## 📋 Implementation Checklist

### Quick Customization (1-2 giorni)

- [ ] Modifica system prompt per dominio
- [ ] Update entity types in graph builder
- [ ] Personalizza CLI messaging
- [ ] Configura embedding model per performance

### Medium Customization (1-2 settimane)

- [ ] Nuovi tool domain-specific
- [ ] Schema database extension
- [ ] Custom document processors
- [ ] Domain-specific models

### Deep Customization (2-4 settimane)

- [ ] Custom search algorithms
- [ ] Advanced UI development
- [ ] Complex entity relationship modeling
- [ ] Performance optimization
- [ ] Security & compliance features

## 🚀 Quick Start Templates

### Template per Legal Domain

```bash
# 1. Copy prompts template
cp templates/legal_prompts.py agent/prompts.py

# 2. Update entities
cp templates/legal_entities.py ingestion/graph_builder.py

# 3. Configure for legal docs
export DOMAIN="legal"
export ENTITY_TYPES="parties,contracts,clauses,courts"
```

### Template per Medical Domain

```bash
# 1. Medical prompts
cp templates/medical_prompts.py agent/prompts.py

# 2. Medical entities
cp templates/medical_entities.py ingestion/graph_builder.py

# 3. Configure for medical docs
export DOMAIN="medical"
export ENTITY_TYPES="patients,conditions,treatments,medications"
```

## 💡 Best Practices

### 1. Iterative Approach

- Inizia con system prompt e entities
- Testa con sample documents
- Raffina basandoti su risultati

### 2. Performance Testing

- Misura response times per dominio
- Ottimizza chunk size e overlap
- Valuta embedding model trade-offs

### 3. User Feedback Loop

- Deploy con small user group
- Raccogli feedback su relevance
- Itera su prompt e tool selection

### 4. Documentation

- Documenta ogni customizzazione
- Mantieni mapping tra versioni
- Crea troubleshooting guide

Il sistema Agent OS è progettato per supportare tutti questi pattern di customizzazione con modifiche minimali al core codebase.
