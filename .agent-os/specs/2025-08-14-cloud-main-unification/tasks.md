# Spec Tasks

## Tasks

- [x] 1. Unifica codice su main
  - [x] 1.1 Checkout main
  - [x] 1.2 Merge senza storia comune
  - [x] 1.3 Push su remoto

- [x] 2. Esegui workflow Cloud Shared Test Suite
  - [x] 2.1 Dispatch workflow su main
  - [x] 2.2 Leggi stato ultimo run
  - [x] 2.3 Ispeziona log del run

- [x] 3. Configura secrets GitHub
  - [x] 3.1 Imposta `DATABASE_URL`
  - [x] 3.2 Imposta `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
  - [x] 3.3 Imposta `LLM_API_KEY`, `EMBEDDING_API_KEY`
  - [x] 3.4 Imposta `API_BASE_URL`

## Command Reference

```bash
# 1) Unifica codice in main
git checkout main
git merge --allow-unrelated-histories cloud-shared-ci -m "merge sanitized code into main"
git push origin main

# 2) Re-run workflow
gh workflow run "Cloud Shared Test Suite" -r main
# Verifica esito e log
gh run list --workflow="cloud-tests.yml" --limit 1
gh run view <RUN_ID> --log
```
