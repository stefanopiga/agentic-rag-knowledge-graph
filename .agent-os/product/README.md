# FisioRAG - Sistema RAG Agentico per la Fisioterapia

## Idea Principale

FisioRAG è un sistema avanzato di Retrieval-Augmented Generation (RAG) progettato specificamente per il dominio della fisioterapia. Sfrutta un'architettura basata su knowledge graph e ricerca semantica per fornire risposte accurate, contestualizzate e basate su evidenze a studenti e professionisti del settore. L'obiettivo è diventare uno strumento indispensabile per la formazione e la pratica clinica, supportato da un'interfaccia utente intuitiva e un backend robusto e affidabile.

## Utenti Target

- **Studenti Universitari**: Principalmente studenti del corso di laurea magistrale in fisioterapia che necessitano di un accesso rapido e affidabile a informazioni di studio complesse.
- **Professionisti del Settore**: Medici, fisioterapisti e altri specialisti che cercano supporto basato su evidenze per le loro decisioni cliniche.

## Installazione e Setup

Per eseguire il progetto correttamente, è essenziale configurare l'ambiente come segue:

1.  **Creare un Ambiente Virtuale**:

    ```bash
    python -m venv venv
    ```

2.  **Attivare l'Ambiente Virtuale**:

    - **Windows**:
      ```bash
      venv\Scripts\activate
      ```
    - **Linux/macOS**:
      ```bash
      source venv/bin/activate
      ```

3.  **Installare le Dipendenze**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurare le Variabili d'Ambiente**:
    Creare un file `.env` nella root del progetto utilizzando `env.txt` come template per le connessioni ai database e le chiavi API.
