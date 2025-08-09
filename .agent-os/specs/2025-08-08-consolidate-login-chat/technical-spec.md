# Technical Spec

## Branch consolidation
- Create PRs with concise titles and single-line commit messages (Windows-safe)
- Ensure checks: CodeQL, CI, signed commits, reviews
- Merge order: docker-modernization → scalability-testing → security-hardening

## Local run (Windows)
- DB stack via Docker compose (`docker compose up -d postgres neo4j redis`)
- Backend via compose service `app` or `uv run python run_backend.py`
- Frontend via PNPM workspace `pnpm --filter frontend dev`, VITE_API_URL=http://localhost:8000

## Auth wiring
- If missing, add minimal FastAPI auth routes in `agent/api.py`:
  - POST /auth/login → returns JWT
  - GET /auth/me → returns current user
- Seed test user via SQL in `sql/seed_user.sql` and mount in postgres init

## QA checklist
- /health returns 200
- UI login page reachable
- After login, chat screen renders and can send a message (stub ok)
