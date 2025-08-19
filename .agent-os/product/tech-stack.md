# Technical Stack

- application_framework: FastAPI ^0.115
- database_system: PostgreSQL (Neon) + Neo4j (Aura) + Redis (optional)
- javascript_framework: React ^19 (Vite)
- realtime_communication: Server-Sent Events (SSE) only
- import_strategy: node
- css_framework: TailwindCSS ^3
- ui_component_library: None (custom + lucide-react)
- fonts_provider: Google Fonts
- icon_library: lucide-react
- application_hosting: Railway (backend) + Vercel (frontend)
- database_hosting: Neon (Postgres), Neo4j Aura
- asset_hosting: Vercel (frontend static)
- deployment_solution: GitHub Actions (cloud suite), container-ready (gunicorn for prod)
- code_repository_url: https://github.com/stefanopiga/agentic-rag-knowledge-graph
