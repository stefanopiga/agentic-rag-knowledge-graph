# Spec Tasks

## Tasks

- [x] 1. Legacy Documentation Cleanup ✅ **COMPLETED**
  - [x] 1.1 Write tests to verify critical docs remain accessible
  - [x] 1.2 Remove obsolete root MD files (AGENT*OS*\_.md, FINAL\__.md, IMPLEMENTATION*\*.md, MEDICAL*_.md, CUSTOMIZATION\_\_.md, VERCEL\_\*.md)
  - [x] 1.3 Remove memory-bank/ directory completely
  - [x] 1.4 Verify Agent OS navigation still works
  - [x] 1.5 Verify all tests pass

- [x] 2. Requirements Files Consolidation ✅ **COMPLETED**
  - [x] 2.1 Write tests to validate requirements consistency
  - [x] 2.2 Remove requirements-clean.txt and requirements.windows.txt
  - [x] 2.3 Update requirements.txt with missing dependencies from pyproject.toml
  - [x] 2.4 Create validation script for pyproject.toml ↔ requirements.txt alignment
  - [x] 2.5 Verify dependency installation works with both files
  - [x] 2.6 Verify all tests pass

- [x] 3. Frontend WebSocket Cleanup ✅ **COMPLETED**
  - [x] 3.1 Write tests for SSE streaming functionality
  - [x] 3.2 Remove frontend/src/services/websocket.ts file
  - [x] 3.3 Remove Socket.io proxy config from frontend/vite.config.ts
  - [x] 3.4 Remove socket.io-client from frontend dependencies
  - [x] 3.5 Update chat services to use only SSE streaming
  - [x] 3.6 Verify frontend-backend communication works
  - [x] 3.7 Verify all tests pass

- [ ] 4. Architecture Documentation Update
  - [ ] 4.1 Write tests to verify documentation accuracy
  - [ ] 4.2 Update MEDICAL_RAG_SYSTEM_SPECIFICATION.md to remove Django references
  - [ ] 4.3 Update ARCHITECTURE.md to specify Redis as optional
  - [ ] 4.4 Update README.md to reflect FastAPI-only architecture
  - [ ] 4.5 Update tech-stack.md for SSE-only WebSocket communication
  - [ ] 4.6 Verify documentation consistency with codebase
  - [ ] 4.7 Verify all tests pass

- [ ] 5. Test Suite Cleanup and Enhancement
  - [ ] 5.1 Write new tests for SSE streaming endpoint
  - [ ] 5.2 Remove Django-specific test sections
  - [ ] 5.3 Update Redis tests to handle optional dependency
  - [ ] 5.4 Fix Django path references in test files
  - [ ] 5.5 Remove obsolete test imports and assertions
  - [ ] 5.6 Verify complete test suite passes
  - [ ] 5.7 Verify test coverage remains adequate
