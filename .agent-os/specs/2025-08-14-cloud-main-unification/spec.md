# Spec: Cloud Main Unification & CI Enablement

## Overview

Unificare il codice sanificato nella branch `cloud-shared-ci` dentro `main`, abilitare il workflow “Cloud Shared Test Suite” su `main`, configurare i secrets CI e verificare l’esito dei run.

## Goals
- Portare il codice completo e sanificato su `main` remoto
- Eseguire workflow cloud su `main` e ottenere esito
- Impostare i secrets necessari per far passare gli step cloud

## Non-Goals
- Refactor applicativo
- Modifica suite test oltre al necessario per CI

## Acceptance Criteria
- `main` contiene codice e workflow aggiornati
- Run “Cloud Shared Test Suite” dispatchato su `main`
- Logs del run consultabili via `gh run view <RUN_ID> --log`
- Secrets GitHub definiti: `DATABASE_URL`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `LLM_API_KEY`, `EMBEDDING_API_KEY`, `API_BASE_URL`

## Risks
- Merge histories unrelated → necessario `--allow-unrelated-histories`
- Push protection/secret scanning → evitare file `.env.*` nel repo
