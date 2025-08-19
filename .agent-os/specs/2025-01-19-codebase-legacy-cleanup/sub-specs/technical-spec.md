# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-01-19-codebase-legacy-cleanup/spec.md

## Technical Requirements

### Legacy Files Removal

- **Root Documentation Cleanup**: Remove obsolete MD files (`AGENT_OS_*.md`, `FINAL_*.md`, `IMPLEMENTATION_*.md`, `MEDICAL_*.md`, `CUSTOMIZATION_*.md`, `VERCEL_*.md`)
- **Memory Bank Directory**: Remove entire `memory-bank/` directory (6 files) replaced by Agent OS structure
- **Requirements Files**: Remove `requirements-clean.txt` and `requirements.windows.txt` (duplicates)
- **Test Files**: Remove Django-specific test sections in `tests/system/test_integration.py` and `tests/system/test_complete_integration.py`

### Requirements Consolidation

- **Update requirements.txt**: Add missing dependencies from pyproject.toml (redis>=5.0.1, aiofiles>=24.1.0, psycopg2-binary>=2.9.0, python-multipart>=0.0.20)
- **Version Alignment**: Ensure requirements.txt versions match pyproject.toml specifications
- **Validation**: Script to verify pyproject.toml dependencies are reflected in requirements.txt

### Frontend WebSocket Cleanup

- **Remove Socket.io Client**: Delete `frontend/src/services/websocket.ts` (112 lines)
- **Update Vite Config**: Remove Socket.io proxy configuration in `frontend/vite.config.ts:34-38`
- **Package Dependencies**: Remove `socket.io-client` from frontend package.json catalog
- **Service Layer**: Update chat services to use only SSE streaming (`frontend/src/services/stream.ts`)

### Documentation Architecture Update

- **MEDICAL_RAG_SYSTEM_SPECIFICATION.md**: Update line 13 to remove Django reference, specify FastAPI-only architecture
- **ARCHITECTURE.md**: Remove Redis as "core component", specify as optional cache
- **README.md**: Update architecture section to reflect single backend (FastAPI), remove Docker compose references until file exists
- **Tech Stack**: Update to reflect WebSocket via SSE only, no Socket.io

### Test Suite Alignment

- **Django Test Removal**: Remove Django import tests, path references, model tests
- **Redis Test Updates**: Modify Redis tests to handle optional dependency gracefully
- **SSE Test Addition**: Add tests for `/chat/stream` endpoint functionality
- **Path Correction**: Fix Django path references from `../fisio-rag-saas` to correct relative paths

## External Dependencies (Conditional)

No new external dependencies required. This spec involves only removal and consolidation of existing dependencies.
