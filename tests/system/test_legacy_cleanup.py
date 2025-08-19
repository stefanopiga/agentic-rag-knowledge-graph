#!/usr/bin/env python3
"""
Test suite per verifica legacy cleanup e documentazione critica.
"""

import os
import sys
from pathlib import Path
import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestLegacyCleanup:
    """Test per verifica pulizia legacy code e preservazione docs critici."""
    
    def test_agent_os_navigation_guide_exists(self):
        """Verifica che la guida navigazione Agent OS rimanga accessibile."""
        guide_path = project_root / ".agent-os" / "AGENT_OS_NAVIGATION_GUIDE.md"
        assert guide_path.exists(), f"Agent OS Navigation Guide non trovato: {guide_path}"
        
        # Verifica contenuto non vuoto
        content = guide_path.read_text(encoding='utf-8')
        assert len(content) > 100, "Navigation guide troppo breve o vuoto"
        assert "Agent OS" in content, "Navigation guide non contiene riferimenti Agent OS"
    
    def test_agent_os_product_directory_intact(self):
        """Verifica che directory .agent-os/product/ rimanga intatta."""
        product_dir = project_root / ".agent-os" / "product"
        assert product_dir.exists(), "Directory .agent-os/product/ non trovata"
        
        # Verifica files critici
        critical_files = [
            "mission-lite.md",
            "tech-stack.md", 
            "roadmap.md",
            "MEDICAL_RAG_SYSTEM_SPECIFICATION.md",
            "ARCHITECTURE.md"
        ]
        
        for file in critical_files:
            file_path = product_dir / file
            assert file_path.exists(), f"File critico mancante: {file}"
            
            # Verifica contenuto non vuoto
            content = file_path.read_text(encoding='utf-8')
            assert len(content) > 50, f"File {file} troppo breve o vuoto"
    
    def test_agent_os_instructions_intact(self):
        """Verifica che directory .agent-os/instructions/ rimanga intatta."""
        instructions_dir = project_root / ".agent-os" / "instructions"
        assert instructions_dir.exists(), "Directory .agent-os/instructions/ non trovata"
        
        # Verifica subdirectory importanti
        assert (instructions_dir / "core").exists(), "Directory core/ mancante"
        assert (instructions_dir / "project").exists(), "Directory project/ mancante"
    
    def test_legacy_files_removed(self):
        """Verifica che files legacy siano stati effettivamente rimossi."""
        legacy_files = [
            "AGENT_OS_SETUP.md",
            "AGENT_OS_STATUS.md", 
            "FINAL_IMPLEMENTATION_ROADMAP.md",
            "CUSTOMIZATION_PATTERNS.md",
            "CUSTOMIZATION_PLANNING.md",
            "IMPLEMENTATION_SUMMARY.md",
            "MEDICAL_DOMAIN_ANALYSIS.md",
            "MEDICAL_IMPLEMENTATION_PLAN.md", 
            "VERCEL_PRICING_BREAKDOWN.md"
        ]
        
        for file in legacy_files:
            file_path = project_root / file
            assert not file_path.exists(), f"File legacy non rimosso: {file}"
    
    def test_memory_bank_directory_removed(self):
        """Verifica che directory memory-bank/ sia stata completamente rimossa."""
        memory_bank_dir = project_root / "memory-bank"
        assert not memory_bank_dir.exists(), "Directory memory-bank/ non rimossa"
    
    def test_fisio_rag_saas_directory_removed(self):
        """Verifica che directory fisio_rag_saas/ Django sia stata rimossa."""
        django_dir = project_root / "fisio_rag_saas"
        assert not django_dir.exists(), "Directory fisio_rag_saas/ non rimossa"
    
    def test_current_spec_exists(self):
        """Verifica che la spec corrente sia accessibile."""
        spec_dir = project_root / ".agent-os" / "specs" / "2025-01-19-codebase-legacy-cleanup"
        assert spec_dir.exists(), "Directory spec corrente non trovata"
        
        # Verifica files spec
        spec_files = ["spec.md", "spec-lite.md", "tasks.md"]
        for file in spec_files:
            file_path = spec_dir / file  
            assert file_path.exists(), f"File spec mancante: {file}"


if __name__ == "__main__":
    # Esecuzione diretta per debug
    test_instance = TestLegacyCleanup()
    
    print("🧪 Running Legacy Cleanup Tests...")
    
    try:
        test_instance.test_agent_os_navigation_guide_exists()
        print("✅ Agent OS Navigation Guide test passed")
        
        test_instance.test_agent_os_product_directory_intact()
        print("✅ Agent OS Product Directory test passed")
        
        test_instance.test_agent_os_instructions_intact()
        print("✅ Agent OS Instructions test passed")
        
        test_instance.test_legacy_files_removed()
        print("✅ Legacy Files Removal test passed")
        
        test_instance.test_memory_bank_directory_removed()
        print("✅ Memory Bank Removal test passed")
        
        test_instance.test_fisio_rag_saas_directory_removed()
        print("✅ Django Directory Removal test passed")
        
        test_instance.test_current_spec_exists()
        print("✅ Current Spec Exists test passed")
        
        print("\n🎉 All legacy cleanup tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
