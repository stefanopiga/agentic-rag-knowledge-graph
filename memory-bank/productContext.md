# Product Context - Agentic RAG with Knowledge Graph

## Problem Solved

I tradizionali sistemi RAG sono limitati nella comprensione di relationships e temporal evolution of facts. I knowledge graph puri mancano di semantic similarity search. Questa combinazione risolve entrambe le limitazioni.

## Core Use Cases

### Semantic Questions

- **"What AI research is Google working on?"**
- **Tool Used**: Vector search per trovare document chunks semanticamente rilevanti
- **Value**: Recupero rapido di contenuti specifici su ricerca AI

### Relationship Questions

- **"How are Microsoft and OpenAI connected?"**
- **Tool Used**: Knowledge graph traversal per esplorare partnerships
- **Value**: Discovery di connessioni non ovvie tra entities

### Temporal Questions

- **"Show me timeline of Meta's AI announcements"**
- **Tool Used**: Graphiti temporal capabilities
- **Value**: Comprensione evoluzione strategica nel tempo

### Complex Analysis

- **"Compare AI strategies of FAANG companies"**
- **Tool Used**: Hybrid search (vector + graph)
- **Value**: Analisi competitiva completa con context e relationships

## User Experience Goals

### Agent Intelligence

- **Automatic Tool Selection**: Agent decide autonomamente quale tool utilizzare
- **Reasoning Transparency**: User vede quali tool sono stati utilizzati e perché
- **Context Awareness**: Maintain conversational context across queries

### Performance Expectations

- **Sub-second Response**: Vector search deve essere veloce
- **Comprehensive Results**: Hybrid search combina meglio di entrambi i mondi
- **Streaming UX**: Real-time responses con Server-Sent Events

### Developer Experience

- **Flexible Setup**: Supporto multiple LLM providers (OpenAI, Ollama, etc.)
- **Clear Documentation**: Installation e usage immediati
- **Testing Confidence**: Comprehensive test suite (58/58 passing)

## Business Value

### For Analysts

- **Research Acceleration**: Queries complesse risolte in secondi vs ore
- **Competitive Intelligence**: Relationship discovery automatica
- **Trend Analysis**: Temporal pattern recognition

### For Developers

- **Architecture Reference**: Pattern per hybrid RAG + Knowledge Graph
- **Production Template**: Setup completo con testing, monitoring, error handling
- **Flexibility**: Provider swapping senza code changes

## Content Strategy

- **Domain Focus**: Big tech companies e AI initiatives (sample: 21 detailed documents)
- **Document Structure**: Markdown format con semantic chunking
- **Metadata Enrichment**: Entity extraction automatica (companies, technologies, people, locations)
- **Graph Relationships**: Automatic relationship detection tra entities
