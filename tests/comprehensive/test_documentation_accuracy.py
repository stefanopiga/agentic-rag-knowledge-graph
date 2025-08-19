"""
Test suite for documentation accuracy validation.

Validates that documentation aligns with actual codebase implementation
and architectural decisions for the legacy cleanup specification.
"""

import pytest
import re
from pathlib import Path
from typing import List, Dict, Any


class TestDocumentationAccuracy:
    """Tests to validate documentation accuracy against codebase."""

    def test_medical_rag_spec_architecture_alignment(self):
        """Verify MEDICAL_RAG_SYSTEM_SPECIFICATION.md reflects actual architecture."""
        spec_file = Path(".agent-os/product/MEDICAL_RAG_SYSTEM_SPECIFICATION.md")
        assert spec_file.exists(), "MEDICAL_RAG_SYSTEM_SPECIFICATION.md must exist"
        
        content = spec_file.read_text(encoding='utf-8')
        
        # Should mention FastAPI as backend
        assert "FastAPI" in content, "Specification should mention FastAPI backend"
        
        # Should NOT mention Django as active frontend (after cleanup)
        django_mentions = self._count_django_references(content)
        assert django_mentions == 0, f"Found {django_mentions} Django references, should be 0 after cleanup"
        
        # Should mention core components
        assert "PostgreSQL" in content, "Should mention PostgreSQL database"
        assert "Neo4j" in content, "Should mention Neo4j knowledge graph"
        assert "Pydantic AI" in content, "Should mention Pydantic AI framework"

    def test_architecture_md_redis_optional_status(self):
        """Verify ARCHITECTURE.md correctly specifies Redis as optional."""
        arch_file = Path(".agent-os/product/ARCHITECTURE.md")
        assert arch_file.exists(), "ARCHITECTURE.md must exist"
        
        content = arch_file.read_text(encoding='utf-8')
        
        # Should mention Redis
        assert "Redis" in content, "Should mention Redis in architecture"
        
        # Should specify Redis as optional (after update)
        redis_context = self._extract_redis_context(content)
        assert "optional" in redis_context.lower() or "opzionale" in redis_context.lower(), \
            "Redis should be described as optional"

    def test_readme_fastapi_only_architecture(self):
        """Verify README.md reflects FastAPI-only backend architecture."""
        readme_file = Path("README.md")
        assert readme_file.exists(), "README.md must exist"
        
        content = readme_file.read_text(encoding='utf-8')
        
        # Should mention FastAPI
        assert "FastAPI" in content, "README should mention FastAPI"
        
        # Should not reference Django as active component
        django_references = self._count_django_references(content)
        assert django_references == 0, f"README contains {django_references} Django references, should be 0"
        
        # Should mention key components
        assert "PostgreSQL" in content or "pgvector" in content, "Should mention PostgreSQL/pgvector"
        assert "Neo4j" in content, "Should mention Neo4j"

    def test_tech_stack_websocket_communication(self):
        """Verify tech-stack.md specifies SSE-only WebSocket communication."""
        tech_stack_file = Path(".agent-os/product/tech-stack.md")
        assert tech_stack_file.exists(), "tech-stack.md must exist"
        
        content = tech_stack_file.read_text(encoding='utf-8')
        
        # Should mention SSE for real-time communication
        assert "SSE" in content or "Server-Sent Events" in content, \
            "tech-stack.md should specify SSE for real-time communication"
        
        # Should NOT mention Socket.io after cleanup
        socket_io_mentions = content.lower().count("socket.io")
        assert socket_io_mentions == 0, f"Found {socket_io_mentions} Socket.io references, should be 0"

    def test_codebase_django_removal_completion(self):
        """Verify Django components have been completely removed from codebase."""
        project_root = Path(".")
        
        # Check that no Django-specific files exist
        django_files = [
            "manage.py",
            "settings.py", 
            "wsgi.py",
            "asgi.py"
        ]
        
        for django_file in django_files:
            found_files = list(project_root.rglob(django_file))
            # Filter out files in legacy directories and dependency directories
            excluded_dirs = ["memory-bank", "venv", ".venv", "site-packages", "__pycache__", ".git", "node_modules"]
            active_django_files = [f for f in found_files if not any(excluded in str(f) for excluded in excluded_dirs)]
            assert len(active_django_files) == 0, f"Found active Django file: {django_file}"

    def test_websocket_client_removal_completion(self):
        """Verify Socket.io client has been completely removed."""
        frontend_dir = Path("frontend")
        if frontend_dir.exists():
            # Check that websocket.ts service has been removed
            websocket_service = frontend_dir / "src" / "services" / "websocket.ts"
            assert not websocket_service.exists(), "websocket.ts service should be removed"
            
            # Check package.json doesn't contain socket.io-client
            package_json = frontend_dir / "package.json"
            if package_json.exists():
                content = package_json.read_text(encoding='utf-8')
                assert "socket.io-client" not in content, "socket.io-client should be removed from dependencies"

    def test_requirements_consolidation_consistency(self):
        """Verify requirements files are consistent with pyproject.toml."""
        pyproject_file = Path("pyproject.toml")
        requirements_file = Path("requirements.txt")
        
        assert pyproject_file.exists(), "pyproject.toml must exist"
        assert requirements_file.exists(), "requirements.txt must exist"
        
        # Basic consistency check - should not have duplicate requirement files
        obsolete_files = [
            "requirements-clean.txt",
            "requirements.windows.txt"
        ]
        
        for obsolete_file in obsolete_files:
            assert not Path(obsolete_file).exists(), f"Obsolete file {obsolete_file} should be removed"

    def test_sse_streaming_implementation_exists(self):
        """Verify SSE streaming implementation exists in frontend."""
        frontend_dir = Path("frontend")
        if frontend_dir.exists():
            # Check that stream.ts service exists for SSE
            stream_service = frontend_dir / "src" / "services" / "stream.ts"
            if stream_service.exists():
                content = stream_service.read_text(encoding='utf-8')
                assert "EventSource" in content or "SSE" in content or "stream" in content.lower(), \
                    "stream.ts should implement SSE functionality"

    def _count_django_references(self, content: str) -> int:
        """Count references to Django in content."""
        django_patterns = [
            r'\bDjango\b',
            r'\bdjango\b',
            r'Django.*SaaS',
            r'Frontend.*Django'
        ]
        
        count = 0
        for pattern in django_patterns:
            count += len(re.findall(pattern, content, re.IGNORECASE))
        
        return count

    def _extract_redis_context(self, content: str) -> str:
        """Extract context around Redis mentions."""
        lines = content.split('\n')
        redis_context = []
        
        for i, line in enumerate(lines):
            if 'Redis' in line:
                # Get surrounding context (3 lines before and after)
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                redis_context.extend(lines[start:end])
        
        return ' '.join(redis_context)


class TestDocumentationConsistency:
    """Tests for consistency across documentation files."""

    def test_architecture_consistency_across_docs(self):
        """Verify architecture is consistently described across all docs."""
        doc_files = [
            ".agent-os/product/MEDICAL_RAG_SYSTEM_SPECIFICATION.md",
            ".agent-os/product/ARCHITECTURE.md", 
            "README.md"
        ]
        
        core_components = ["FastAPI", "PostgreSQL", "Neo4j", "Pydantic AI"]
        
        for doc_file in doc_files:
            file_path = Path(doc_file)
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                
                for component in core_components:
                    assert component in content, \
                        f"{component} should be mentioned in {doc_file}"

    def test_websocket_communication_consistency(self):
        """Verify WebSocket communication method is consistently described."""
        doc_files = [
            ".agent-os/product/tech-stack.md",
            "README.md"
        ]
        
        for doc_file in doc_files:
            file_path = Path(doc_file)
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                
                # Should not mention Socket.io as active
                socket_io_count = content.lower().count("socket.io")
                assert socket_io_count == 0, \
                    f"{doc_file} should not mention Socket.io as active implementation"

    def test_stack_technology_alignment(self):
        """Verify technology stack is aligned across documentation."""
        tech_stack_file = Path(".agent-os/product/tech-stack.md")
        
        if tech_stack_file.exists():
            content = tech_stack_file.read_text(encoding='utf-8')
            
            # Core backend technologies
            assert "FastAPI" in content, "tech-stack should mention FastAPI"
            assert "PostgreSQL" in content or "Neon" in content, "tech-stack should mention PostgreSQL/Neon"
            assert "Neo4j" in content, "tech-stack should mention Neo4j"
            
            # Frontend technologies  
            assert "React" in content, "tech-stack should mention React"
            assert "Vite" in content, "tech-stack should mention Vite"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
