# Project Brief - Agentic RAG with Knowledge Graph

## Core Mission

Sistema di AI agent che ridefinisce il knowledge retrieval combinando RAG tradizionale (vector search) con knowledge graph capabilities per analizzare e fornire insights su big tech companies e le loro AI initiatives.

## Primary Goals

- **Hybrid Intelligence**: Combinazione di vector search (PostgreSQL + pgvector) e knowledge graph (Neo4j + Graphiti)
- **Agentic RAG Excellence**: Agent conversazionale che seleziona automaticamente i tool ottimali per ogni query
- **Temporal Knowledge**: Tracciamento evoluzione facts nel tempo tramite Graphiti
- **Production Ready**: Sistema completo con testing, streaming API, CLI interattiva

## Target Users

- Researcher che analizzano landscape AI delle big tech companies
- Analyst che necessitano di insights su partnerships, acquisitions, competitive dynamics
- Developer che vogliono comprendere pattern architetturali per RAG + Knowledge Graph

## Success Metrics

- **Sistema completo funzionante**: Ingestion → Vector Storage → Knowledge Graph → Agent → API → CLI
- **Flessibilità provider**: Supporto OpenAI, Ollama, OpenRouter, Gemini
- **Performance**: Ricerche semantiche rapide + graph traversal intelligente
- **Quality**: Test coverage >80% (attualmente 58/58 test passing)

## Key Differentiators

1. **Complementary Strengths**: Vector search per contenuti semanticamente simili, knowledge graph per connessioni nascoste
2. **Intelligent Tool Selection**: Agent decide automaticamente quando usare vector vs graph vs hybrid search
3. **Temporal Intelligence**: Graphiti traccia cambiamenti facts nel tempo (cruciale per fast-evolving AI landscape)
4. **Agent Transparency**: Visibilità completa dei tool utilizzati dall'agent tramite CLI e API

## Technology Foundation

- **Python 3.11+** con Pydantic AI, FastAPI, PostgreSQL+pgvector, Neo4j+Graphiti
- **Document Focus**: Markdown files su big tech companies (21 sample documents inclusi)
- **Flexible Architecture**: Provider LLM intercambiabili, semantic chunking, streaming responses
