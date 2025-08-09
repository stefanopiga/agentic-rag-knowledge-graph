# Spec (lite)

Scope:
- Consolidate feature branches into main under the new rulesets
- Ensure local run workflow works on Windows (UV + PNPM + Docker)
- Validate login → chat happy path in the UI

Non-goals:
- Full LLM pipeline hardening (ingestion/chunking/embedding) – follow-up phase

Deliverables:
- 3 PRs merged, one release tag
- Updated README with a 3-step run guide
- Minimal auth endpoints available and wired to FE
