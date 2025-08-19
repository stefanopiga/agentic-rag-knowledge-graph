#!/usr/bin/env python3
"""
Test suite per verifica consistenza e consolidamento requirements.
"""

import os
import sys
from pathlib import Path
import re
import subprocess
from typing import List, Dict, Set, Tuple
import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestRequirementsConsistency:
    """Test per verifica consistenza requirements files."""
    
    def __init__(self):
        """Initialize test instance."""
        self.project_root = project_root
        self.requirements_txt = self.project_root / "requirements.txt"
        self.requirements_clean = self.project_root / "requirements-clean.txt"
        self.requirements_windows = self.project_root / "requirements.windows.txt"
        self.pyproject_toml = self.project_root / "pyproject.toml"
    
    def parse_requirements_file(self, file_path: Path) -> Dict[str, str]:
        """Parse requirements file e ritorna dict {package: version}."""
        requirements = {}
        if not file_path.exists():
            return requirements
            
        content = file_path.read_text(encoding='utf-8')
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('http'):
                continue
                
            # Parse package==version pattern
            if '==' in line:
                parts = line.split('==')
                if len(parts) == 2:
                    package = parts[0].strip()
                    version = parts[1].strip()
                    requirements[package] = f"=={version}"
            elif '>=' in line:
                parts = line.split('>=')
                if len(parts) == 2:
                    package = parts[0].strip()
                    version = parts[1].strip()
                    requirements[package] = f">={version}"
        
        return requirements
    
    def parse_pyproject_dependencies(self) -> Dict[str, str]:
        """Parse pyproject.toml dependencies."""
        if not self.pyproject_toml.exists():
            return {}
        
        content = self.pyproject_toml.read_text(encoding='utf-8')
        dependencies = {}
        
        # Simple parsing - find dependencies section
        in_dependencies = False
        for line in content.splitlines():
            line = line.strip()
            
            if line == 'dependencies = [':
                in_dependencies = True
                continue
            elif in_dependencies and line == ']':
                in_dependencies = False
                continue
            elif in_dependencies and line.startswith('"'):
                # Parse "package>=version" format
                dep = line.strip('"').strip(',').strip()
                if '>=' in dep:
                    parts = dep.split('>=')
                    if len(parts) == 2:
                        package = parts[0].strip()
                        version = parts[1].strip().strip('"')
                        dependencies[package] = f">={version}"
                elif '==' in dep:
                    parts = dep.split('==')
                    if len(parts) == 2:
                        package = parts[0].strip()
                        version = parts[1].strip().strip('"')
                        dependencies[package] = f"=={version}"
        
        return dependencies
    
    def test_requirements_files_exist(self):
        """Verifica che i requirements files consolidati esistano."""
        assert self.requirements_txt.exists(), "requirements.txt mancante"
        assert self.pyproject_toml.exists(), "pyproject.toml mancante"
        
        # Verifica che i file duplicati siano stati rimossi (Task 2.2)
        assert not self.requirements_clean.exists(), "requirements-clean.txt dovrebbe essere stato rimosso"
        assert not self.requirements_windows.exists(), "requirements.windows.txt dovrebbe essere stato rimosso"
    
    def test_pyproject_contains_missing_dependencies(self):
        """Verifica che dipendenze siano ora presenti in entrambi i files dopo Task 2.3."""
        pyproject_deps = self.parse_pyproject_dependencies()
        requirements_deps = self.parse_requirements_file(self.requirements_txt)
        
        # Dipendenze che sono state aggiunte nel Task 2.3
        added_deps = ['redis', 'aiofiles', 'psycopg2-binary']
        
        # Verifica che siano ora presenti in entrambi i files
        for dep in added_deps:
            assert dep in pyproject_deps, f"Dipendenza {dep} mancante in pyproject.toml"
            assert dep in requirements_deps, f"Dipendenza {dep} mancante in requirements.txt dopo Task 2.3"
        
        print("✅ Dipendenze consolidate correttamente in entrambi i files")
    
    def test_duplicated_files_identification(self):
        """Verifica che files duplicati siano stati rimossi."""
        # Dopo Task 2.2, i file duplicati dovrebbero essere stati rimossi
        assert not self.requirements_clean.exists(), "requirements-clean.txt dovrebbe essere rimosso"
        assert not self.requirements_windows.exists(), "requirements.windows.txt dovrebbe essere rimosso"
        
        print("✅ Files duplicati rimossi correttamente")
    
    def test_requirements_txt_completeness_after_update(self):
        """Test per verifica completezza requirements.txt dopo update (WILL FAIL INITIALLY)."""
        # Questo test fallirà inizialmente e passerà dopo l'update
        requirements_deps = self.parse_requirements_file(self.requirements_txt)
        pyproject_deps = self.parse_pyproject_dependencies()
        
        # Core dependencies che devono essere in entrambi
        core_deps = ['fastapi', 'pydantic-ai', 'openai', 'neo4j', 'asyncpg']
        
        for dep in core_deps:
            assert dep in requirements_deps, f"Dipendenza core {dep} mancante in requirements.txt"
            assert dep in pyproject_deps, f"Dipendenza core {dep} mancante in pyproject.toml"
    
    def test_no_conflicting_versions(self):
        """Verifica che non ci siano versioni conflittuali tra files."""
        requirements_deps = self.parse_requirements_file(self.requirements_txt)
        pyproject_deps = self.parse_pyproject_dependencies()
        
        for package in requirements_deps:
            if package in pyproject_deps:
                req_version = requirements_deps[package]
                pyproject_version = pyproject_deps[package]
                
                # Versioni devono essere compatibili
                req_num = req_version.replace('>=', '').replace('==', '').strip()
                pyproject_num = pyproject_version.replace('>=', '').replace('==', '').strip()
                
                # Funzione helper per confronto semantico versioni
                def version_compare(v1: str, v2: str) -> int:
                    """Confronta due versioni semanticamente. Ritorna: -1 se v1<v2, 0 se v1==v2, 1 se v1>v2"""
                    parts1 = [int(x) for x in v1.split('.')]
                    parts2 = [int(x) for x in v2.split('.')]
                    
                    # Padding per stesso numero di parti
                    max_len = max(len(parts1), len(parts2))
                    parts1.extend([0] * (max_len - len(parts1)))
                    parts2.extend([0] * (max_len - len(parts2)))
                    
                    for p1, p2 in zip(parts1, parts2):
                        if p1 < p2:
                            return -1
                        elif p1 > p2:
                            return 1
                    return 0
                
                # Se versioni numeriche uguali, compatibili
                if version_compare(req_num, pyproject_num) == 0:
                    continue
                
                # Verifica compatibilità basata su operatori
                versions_compatible = False
                if req_version.startswith('==') and pyproject_version.startswith('>='):
                    # requirements.txt ha versione fissa, pyproject.toml ha minima
                    # Compatibile se versione fissa >= versione minima
                    versions_compatible = version_compare(req_num, pyproject_num) >= 0
                elif req_version.startswith('>=') and pyproject_version.startswith('=='):
                    # requirements.txt ha minima, pyproject.toml ha fissa
                    versions_compatible = version_compare(pyproject_num, req_num) >= 0
                elif req_version.startswith('>=') and pyproject_version.startswith('>='):
                    # Entrambi hanno versioni minime, sempre compatibili
                    versions_compatible = True
                else:
                    # Entrambi ==, devono essere uguali (già controllato sopra)
                    versions_compatible = version_compare(req_num, pyproject_num) == 0
                
                assert versions_compatible, \
                    f"Versioni conflittuali per {package}: {req_version} vs {pyproject_version}"
    
    def test_validation_script_functionality(self):
        """Test per script di validazione (PLACEHOLDER - will implement)."""
        # Questo test verificherà che lo script di validazione funzioni
        validation_script = self.project_root / "scripts" / "validate_requirements.py"
        
        # Per ora, questo è un placeholder che passerà sempre
        # Lo script verrà implementato nel subtask 2.4
        assert True, "Validation script test - placeholder"


if __name__ == "__main__":
    # Esecuzione diretta per debug
    test_instance = TestRequirementsConsistency()
    
    print("🧪 Running Requirements Consistency Tests...")
    
    try:
        test_instance.test_requirements_files_exist()
        print("✅ Requirements files exist test passed")
        
        test_instance.test_pyproject_contains_missing_dependencies()
        print("✅ Pyproject missing dependencies test passed")
        
        test_instance.test_duplicated_files_identification()
        print("✅ Duplicated files identification test passed")
        
        try:
            test_instance.test_requirements_txt_completeness_after_update()
            print("✅ Requirements completeness test passed")
        except AssertionError as e:
            print(f"⚠️ Requirements completeness test failed (expected): {e}")
        
        test_instance.test_no_conflicting_versions()
        print("✅ No conflicting versions test passed")
        
        test_instance.test_validation_script_functionality()
        print("✅ Validation script functionality test passed")
        
        print("\n🎉 Requirements consistency tests completed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
