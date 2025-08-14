# Decisioni Architetturali

Questo documento traccia le decisioni chiave che hanno plasmato l'architettura di FisioRAG.

- **Scelta di FastAPI**: Sebbene la struttura iniziale del progetto includesse Django, si è optato per FastAPI per il servizio API principale grazie alle sue elevate prestazioni, al supporto nativo per le operazioni asincrone (fondamentale per le chiamate a LLM e DB) e alla generazione automatica della documentazione API.

- **Database Ibrido (Postgres + Neo4j)**: La combinazione di un database relazionale/vettoriale e un database a grafo è una decisione strategica.

  - **PostgreSQL con pgvector**: Scelto per la sua robustezza, il supporto a SQL e la capacità di gestire in modo efficiente gli embedding vettoriali per la ricerca di similarità.
  - **Neo4j**: Mantenuto dalla base di codice originale, è ideale per modellare e interrogare le complesse relazioni tra concetti medici e fisioterapici, arricchendo il contesto fornito al LLM.

- **Standardizzazione su OpenAI**: Per garantire coerenza, prevedibilità e prestazioni di alta qualità, si è deciso di utilizzare esclusivamente i modelli di OpenAI, eliminando la complessità legata alla gestione di provider multipli.

- **Architettura Multi-Tenant**: Progettata fin dall'inizio per supportare l'isolamento dei dati tra diversi utenti o organizzazioni, garantendo sicurezza e scalabilità per un futuro utilizzo in un contesto SaaS.
