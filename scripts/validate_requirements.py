#!/usr/bin/env python3
"""
Script di validazione per allineamento pyproject.toml ↔ requirements.txt
Verifica consistenza dipendenze e versioni tra i due file.
"""

import sys
import re
from pathlib import Path
from typing import Dict, Set, List, Tuple
import argparse


def parse_requirements_file(file_path: Path) -> Dict[str, str]:
    """Parse requirements.txt e ritorna dict {package: version}."""
    requirements = {}
    if not file_path.exists():
        return requirements
        
    content = file_path.read_text(encoding='utf-8')
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('http'):
            continue
            
        # Parse package==version or package>=version pattern
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


def parse_pyproject_dependencies(pyproject_path: Path) -> Dict[str, str]:
    """Parse pyproject.toml dependencies."""
    if not pyproject_path.exists():
        return {}
    
    content = pyproject_path.read_text(encoding='utf-8')
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
                    version = parts[1].strip()
                    dependencies[package] = f">={version}"
            elif '==' in dep:
                parts = dep.split('==')
                if len(parts) == 2:
                    package = parts[0].strip()
                    version = parts[1].strip()
                    dependencies[package] = f"=={version}"
    
    return dependencies


def extract_version_number(version_spec: str) -> str:
    """Estrae numero versione da specifiche come '>=1.2.3' o '==1.2.3'."""
    return re.sub(r'^[><=!]+', '', version_spec)


def compare_versions(req_version: str, pyproject_version: str) -> bool:
    """Confronta se due specifiche di versione sono compatibili."""
    req_num = extract_version_number(req_version)
    pyproject_num = extract_version_number(pyproject_version)
    
    # Se i numeri di versione sono uguali, sono compatibili
    if req_num == pyproject_num:
        return True
    
    # Se uno è >= e l'altro ==, controllare se il numero == soddisfa >=
    if req_version.startswith('>=') and pyproject_version.startswith('=='):
        return req_num <= pyproject_num
    elif pyproject_version.startswith('>=') and req_version.startswith('=='):
        return pyproject_num <= req_num
    
    return False


def validate_requirements_alignment(project_root: Path, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Valida allineamento tra pyproject.toml e requirements.txt.
    
    Returns:
        Tuple[bool, List[str]]: (success, lista_messaggi)
    """
    requirements_txt = project_root / "requirements.txt"
    pyproject_toml = project_root / "pyproject.toml"
    
    messages = []
    success = True
    
    # Verifica esistenza files
    if not requirements_txt.exists():
        messages.append("❌ requirements.txt non trovato")
        return False, messages
    
    if not pyproject_toml.exists():
        messages.append("❌ pyproject.toml non trovato")
        return False, messages
    
    messages.append("✅ Files trovati")
    
    # Parse dependencies
    req_deps = parse_requirements_file(requirements_txt)
    pyproject_deps = parse_pyproject_dependencies(pyproject_toml)
    
    if verbose:
        messages.append(f"📊 requirements.txt: {len(req_deps)} dipendenze")
        messages.append(f"📊 pyproject.toml: {len(pyproject_deps)} dipendenze")
    
    # Core dependencies che devono essere in entrambi
    core_dependencies = {
        'fastapi', 'uvicorn', 'pydantic-ai', 'openai', 'graphiti', 
        'graphiti-core', 'neo4j', 'asyncpg', 'python-multipart', 
        'python-dotenv', 'pydantic', 'pydantic-settings'
    }
    
    # Verifica core dependencies
    missing_in_req = core_dependencies - set(req_deps.keys())
    missing_in_pyproject = core_dependencies - set(pyproject_deps.keys())
    
    if missing_in_req:
        success = False
        messages.append(f"❌ Core dependencies mancanti in requirements.txt: {missing_in_req}")
    
    if missing_in_pyproject:
        success = False
        messages.append(f"❌ Core dependencies mancanti in pyproject.toml: {missing_in_pyproject}")
    
    if not missing_in_req and not missing_in_pyproject:
        messages.append("✅ Tutte le core dependencies presenti in entrambi i file")
    
    # Verifica versioni conflittuali
    version_conflicts = []
    for package in req_deps:
        if package in pyproject_deps:
            req_version = req_deps[package]
            pyproject_version = pyproject_deps[package]
            
            if not compare_versions(req_version, pyproject_version):
                version_conflicts.append((package, req_version, pyproject_version))
    
    if version_conflicts:
        success = False
        messages.append("❌ Versioni conflittuali rilevate:")
        for package, req_v, pyproject_v in version_conflicts:
            messages.append(f"   • {package}: requirements.txt={req_v} vs pyproject.toml={pyproject_v}")
    else:
        messages.append("✅ Nessun conflitto di versioni rilevato")
    
    # Verifica dipendenze extra in pyproject ma mancanti in requirements
    extra_in_pyproject = set(pyproject_deps.keys()) - set(req_deps.keys())
    if extra_in_pyproject:
        # Filtra dipendenze che potrebbero essere opzionali
        important_extra = extra_in_pyproject - {'redis', 'aiofiles', 'psycopg2-binary'}
        if important_extra:
            messages.append(f"⚠️ Dipendenze in pyproject.toml ma non in requirements.txt: {important_extra}")
    
    # Verifica dipendenze extra in requirements ma non in pyproject  
    extra_in_req = set(req_deps.keys()) - set(pyproject_deps.keys())
    if extra_in_req:
        if verbose:
            messages.append(f"ℹ️ Dipendenze extra in requirements.txt: {len(extra_in_req)} packages")
    
    return success, messages


def main():
    """Main function per esecuzione CLI."""
    parser = argparse.ArgumentParser(
        description="Valida allineamento tra pyproject.toml e requirements.txt"
    )
    parser.add_argument(
        '--project-root', 
        type=Path, 
        default=Path.cwd(),
        help="Path alla root del progetto (default: directory corrente)"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Output verboso con dettagli aggiuntivi"
    )
    
    args = parser.parse_args()
    
    print("🔍 Validazione allineamento requirements...")
    print(f"📁 Project root: {args.project_root}")
    print()
    
    success, messages = validate_requirements_alignment(args.project_root, args.verbose)
    
    for message in messages:
        print(message)
    
    print()
    if success:
        print("🎉 Validazione completata con successo!")
        return 0
    else:
        print("💥 Validazione fallita - rilevate inconsistenze")
        return 1


if __name__ == "__main__":
    sys.exit(main())
