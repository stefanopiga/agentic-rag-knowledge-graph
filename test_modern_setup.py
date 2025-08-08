#!/usr/bin/env python3
"""
Test script per verificare il setup modernizzato con UV + PNPM + BUN
Questo script verifica che tutti i tool siano installati e funzionanti.
"""

import subprocess
import sys
from pathlib import Path
import json
import os

def run_command(command: str, check: bool = True) -> tuple[int, str, str]:
    """Esegue un comando e ritorna exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout or "", e.stderr or ""
    except FileNotFoundError:
        return 127, "", f"Command not found: {command.split()[0]}"

def test_uv():
    """Test UV package manager"""
    print("🧪 Testing UV (Python package manager)...")
    
    # Test UV installation
    code, stdout, stderr = run_command("uv --version", check=False)
    if code != 0:
        print(f"❌ UV not installed: {stderr}")
        return False
    
    print(f"✅ UV installed: {stdout.strip()}")
    
    # Test pyproject.toml exists
    if not Path("pyproject.toml").exists():
        print("❌ pyproject.toml not found")
        return False
    
    print("✅ pyproject.toml found")
    
    # Test UV sync (dry run)
    code, stdout, stderr = run_command("uv sync --dry-run", check=False)
    if code != 0:
        print(f"⚠️ UV sync issues: {stderr}")
        return False
    
    print("✅ UV configuration valid")
    return True

def test_pnpm():
    """Test PNPM package manager"""
    print("\n🧪 Testing PNPM (Node.js package manager)...")
    
    # Test PNPM installation
    code, stdout, stderr = run_command("pnpm --version", check=False)
    if code != 0:
        print(f"❌ PNPM not installed: {stderr}")
        return False
    
    print(f"✅ PNPM installed: {stdout.strip()}")
    
    # Test workspace configuration
    if not Path("pnpm-workspace.yaml").exists():
        print("❌ pnpm-workspace.yaml not found")
        return False
    
    print("✅ pnpm-workspace.yaml found")
    
    # Test package.json exists
    if not Path("package.json").exists():
        print("❌ package.json not found")
        return False
    
    print("✅ package.json found")
    
    # Test workspace validation
    code, stdout, stderr = run_command("pnpm list --depth=0", check=False)
    if code != 0:
        print(f"⚠️ PNPM workspace issues: {stderr}")
        return False
    
    print("✅ PNPM workspace configuration valid")
    return True

def test_bun():
    """Test BUN runtime (optional)"""
    print("\n🧪 Testing BUN (JavaScript runtime - optional)...")
    
    # Test BUN installation
    code, stdout, stderr = run_command("bun --version", check=False)
    if code != 0:
        print(f"⚠️ BUN not installed (optional): {stderr}")
        return True  # BUN è opzionale
    
    print(f"✅ BUN installed: {stdout.strip()}")
    
    # Test BUN config if exists
    if Path("frontend/bun.config.ts").exists():
        print("✅ BUN configuration found")
    
    return True

def test_project_structure():
    """Test project structure"""
    print("\n🧪 Testing Project Structure...")
    
    required_files = [
        "pyproject.toml",
        "pnpm-workspace.yaml", 
        "package.json",
        "frontend/package.json",
        ".uvrc"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Missing required file: {file_path}")
            return False
        print(f"✅ Found: {file_path}")
    
    return True

def test_package_configs():
    """Test package configurations"""
    print("\n🧪 Testing Package Configurations...")
    
    # Test pyproject.toml structure
    try:
        import tomllib
        with open("pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)
        
        if "project" not in pyproject:
            print("❌ pyproject.toml missing [project] section")
            return False
        
        if "dependencies" not in pyproject["project"]:
            print("❌ pyproject.toml missing dependencies")
            return False
        
        print("✅ pyproject.toml structure valid")
        
    except Exception as e:
        print(f"❌ Error reading pyproject.toml: {e}")
        return False
    
    # Test package.json structure
    try:
        with open("package.json") as f:
            package = json.load(f)
        
        if "packageManager" not in package:
            print("❌ package.json missing packageManager field")
            return False
        
        if "pnpm" not in package["packageManager"]:
            print("❌ package.json not configured for PNPM")
            return False
        
        print("✅ package.json structure valid")
        
    except Exception as e:
        print(f"❌ Error reading package.json: {e}")
        return False
    
    return True

def test_performance():
    """Test performance improvements"""
    print("\n⚡ Testing Performance Optimizations...")
    
    # Test UV cache
    uv_cache = Path.home() / ".cache" / "uv"
    if uv_cache.exists():
        print("✅ UV cache directory found")
    
    # Test PNPM store
    code, stdout, stderr = run_command("pnpm store path", check=False)
    if code == 0:
        print(f"✅ PNPM store: {stdout.strip()}")
    
    return True

def main():
    """Main test runner"""
    print("🚀 FisioRAG - Modern Setup Verification")
    print("=" * 50)
    
    tests = [
        test_project_structure,
        test_uv,
        test_pnpm, 
        test_bun,
        test_package_configs,
        test_performance
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Modern setup is working correctly.")
        print("\n🚀 Next steps:")
        print("   1. Run: pnpm setup")
        print("   2. Run: pnpm dev")
        print("   3. Enjoy ultra-fast development!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above.")
        print("\n📚 See MIGRATION_GUIDE.md for setup instructions")
        return 1

if __name__ == "__main__":
    sys.exit(main())
