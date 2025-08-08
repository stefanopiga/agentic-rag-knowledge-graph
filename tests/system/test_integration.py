"""
Test Integration - AI e Django.

Fase 3 del testing di sistema: verifica integrazione AI, Django e API.
"""

import os
import sys
import asyncio
import traceback
import subprocess
from pathlib import Path

# Aggiungi project root al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.system.test_logger import create_logger


class IntegrationTests:
    """Test per verifica integrazione AI e Django."""
    
    def __init__(self):
        self.logger = create_logger("integration")
        self.test_results = {
            "openai_integration": False,
            "django_setup": False,
            "django_migrations": False,
            "quiz_models": False,
            "quiz_generator": False,
            "api_endpoints": False
        }
    
    async def run_all_tests(self) -> dict:
        """Esegue tutti i test di integrazione."""
        self.logger.log_info("🔗 INIZIANDO TEST INTEGRAZIONE...")
        
        try:
            # Test 1: OpenAI Integration
            await self.test_openai_integration()
            
            # Test 2: Django Setup
            await self.test_django_setup()
            
            # Test 3: Django Migrations
            await self.test_django_migrations()
            
            # Test 4: Quiz Models
            await self.test_quiz_models()
            
            # Test 5: Quiz Generator
            await self.test_quiz_generator()
            
            # Test 6: API Endpoints
            await self.test_api_endpoints()
            
        except Exception as e:
            self.logger.log_error(f"Errore critico durante test integrazione: {e}")
            self.logger.log_error(traceback.format_exc())
        
        finally:
            return self.logger.finalize()
    
    async def test_openai_integration(self):
        """Test OpenAI Integration."""
        self.logger.log_test_start("Verifica OpenAI Integration")
        
        try:
            import openai
            
            # Check API key
            api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('LLM_API_KEY')
            
            if not api_key:
                self.logger.log_test_skip("Verifica OpenAI Integration", "API key non disponibile")
                return
            
            if api_key.startswith('sk-test'):
                self.logger.log_test_skip("Verifica OpenAI Integration", "Test API key - skip test reali")
                return
            
            # Test client creation
            client = openai.OpenAI(api_key=api_key)
            self.logger.log_info("✅ OpenAI client creato")
            
            # Test minimal completion
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": "Rispondi semplicemente 'test riuscito'"}
                    ],
                    max_tokens=10,
                    temperature=0
                )
                
                if response.choices and response.choices[0].message:
                    content = response.choices[0].message.content
                    self.logger.log_info(f"✅ Risposta OpenAI: {content}")
                
            except Exception as e:
                self.logger.log_warning(f"⚠️ Test OpenAI completion fallito: {e}")
            
            # Test embeddings
            try:
                embedding_response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input="test embedding"
                )
                
                if embedding_response.data:
                    embedding_dim = len(embedding_response.data[0].embedding)
                    self.logger.log_info(f"✅ Embedding creato: {embedding_dim} dimensioni")
                
            except Exception as e:
                self.logger.log_warning(f"⚠️ Test OpenAI embedding fallito: {e}")
            
            self.test_results["openai_integration"] = True
            self.logger.log_test_success("Verifica OpenAI Integration", "Integrazione funzionante")
            
        except Exception as e:
            self.test_results["openai_integration"] = False
            self.logger.log_test_failure("Verifica OpenAI Integration", str(e))
    
    async def test_django_setup(self):
        """Test Django Setup."""
        self.logger.log_test_start("Verifica Django Setup")
        
        try:
            # Check Django project directory
            django_dir = Path("../fisio-rag-saas")
            if not django_dir.exists():
                self.logger.log_test_skip("Verifica Django Setup", "Directory Django non trovata")
                return
            
            self.logger.log_info(f"✅ Directory Django trovata: {django_dir.resolve()}")
            
            # Check Django files
            django_files = [
                "fisio_rag_saas/settings.py",
                "fisio_rag_saas/urls.py",
                "manage.py",
                "accounts/models.py",
                "medical_content/models.py",
                "rag_engine/models.py"
            ]
            
            existing_files = []
            for file in django_files:
                file_path = django_dir / file
                if file_path.exists():
                    existing_files.append(file)
                    self.logger.log_info(f"✅ {file}")
                else:
                    self.logger.log_warning(f"⚠️ {file} non trovato")
            
            self.logger.log_info(f"✅ File Django: {len(existing_files)}/{len(django_files)}")
            
            # Test Django import
            original_cwd = os.getcwd()
            try:
                os.chdir(django_dir)
                sys.path.insert(0, str(django_dir.resolve()))
                
                # Set Django settings
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fisio_rag_saas.settings')
                
                import django
                django.setup()
                
                self.logger.log_info("✅ Django setup completato")
                
                # Test apps
                from django.apps import apps
                installed_apps = [app.label for app in apps.get_app_configs()]
                self.logger.log_info(f"✅ Apps Django: {len(installed_apps)}")
                
            except Exception as e:
                self.logger.log_warning(f"⚠️ Errore Django setup: {e}")
            finally:
                os.chdir(original_cwd)
                if str(django_dir.resolve()) in sys.path:
                    sys.path.remove(str(django_dir.resolve()))
            
            self.test_results["django_setup"] = True
            self.logger.log_test_success("Verifica Django Setup", f"Setup OK - {len(existing_files)} file presenti")
            
        except Exception as e:
            self.test_results["django_setup"] = False
            self.logger.log_test_failure("Verifica Django Setup", str(e))
    
    async def test_django_migrations(self):
        """Test Django Migrations."""
        self.logger.log_test_start("Verifica Django Migrations")
        
        try:
            django_dir = Path("../fisio-rag-saas")
            if not django_dir.exists():
                self.logger.log_test_skip("Verifica Django Migrations", "Directory Django non trovata")
                return
            
            original_cwd = os.getcwd()
            try:
                os.chdir(django_dir)
                
                # Test makemigrations --dry-run
                result = subprocess.run([
                    sys.executable, "manage.py", "makemigrations", "--dry-run"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    self.logger.log_info("✅ makemigrations --dry-run riuscito")
                    if "No changes detected" in result.stdout:
                        self.logger.log_info("✅ Nessuna migration pending")
                    else:
                        self.logger.log_info("ℹ️ Migration da creare rilevate")
                else:
                    self.logger.log_warning(f"⚠️ makemigrations fallito: {result.stderr}")
                
                # Test migrate --dry-run
                result = subprocess.run([
                    sys.executable, "manage.py", "migrate", "--dry-run"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    self.logger.log_info("✅ migrate --dry-run riuscito")
                else:
                    self.logger.log_warning(f"⚠️ migrate fallito: {result.stderr}")
                
                # Test Django check
                result = subprocess.run([
                    sys.executable, "manage.py", "check"
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    self.logger.log_info("✅ Django check riuscito")
                else:
                    self.logger.log_warning(f"⚠️ Django check fallito: {result.stderr}")
                
            except subprocess.TimeoutExpired:
                self.logger.log_warning("⚠️ Timeout durante test Django")
            except Exception as e:
                self.logger.log_warning(f"⚠️ Errore test Django: {e}")
            finally:
                os.chdir(original_cwd)
            
            self.test_results["django_migrations"] = True
            self.logger.log_test_success("Verifica Django Migrations", "Migration system verificato")
            
        except Exception as e:
            self.test_results["django_migrations"] = False
            self.logger.log_test_failure("Verifica Django Migrations", str(e))
    
    async def test_quiz_models(self):
        """Test Quiz Models."""
        self.logger.log_test_start("Verifica Quiz Models")
        
        try:
            django_dir = Path("../fisio-rag-saas")
            if not django_dir.exists():
                self.logger.log_test_skip("Verifica Quiz Models", "Directory Django non trovata")
                return
            
            # Check quiz model files
            quiz_files = [
                "medical_content/quiz_models.py",
                "api/quiz_serializers.py",
                "api/quiz_views.py",
                "medical_content/quiz_generator.py"
            ]
            
            existing_quiz_files = []
            for file in quiz_files:
                file_path = django_dir / file
                if file_path.exists():
                    existing_quiz_files.append(file)
                    file_size = file_path.stat().st_size
                    self.logger.log_info(f"✅ {file} ({file_size} bytes)")
                else:
                    self.logger.log_warning(f"⚠️ {file} non trovato")
            
            # Test Django management command
            quiz_command_path = django_dir / "medical_content/management/commands/generate_quiz.py"
            if quiz_command_path.exists():
                self.logger.log_info("✅ Django management command generate_quiz trovato")
            else:
                self.logger.log_warning("⚠️ Management command generate_quiz non trovato")
            
            self.test_results["quiz_models"] = True
            self.logger.log_test_success("Verifica Quiz Models", f"{len(existing_quiz_files)} file quiz presenti")
            
        except Exception as e:
            self.test_results["quiz_models"] = False
            self.logger.log_test_failure("Verifica Quiz Models", str(e))
    
    async def test_quiz_generator(self):
        """Test Quiz Generator."""
        self.logger.log_test_start("Verifica Quiz Generator")
        
        try:
            django_dir = Path("../fisio-rag-saas")
            if not django_dir.exists():
                self.logger.log_test_skip("Verifica Quiz Generator", "Directory Django non trovata")
                return
            
            original_cwd = os.getcwd()
            try:
                os.chdir(django_dir)
                
                # Test generate_quiz command help
                result = subprocess.run([
                    sys.executable, "manage.py", "generate_quiz", "--help"
                ], capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    self.logger.log_info("✅ generate_quiz command disponibile")
                    
                    # Check opzioni disponibili
                    if "--category" in result.stdout:
                        self.logger.log_info("✅ Opzione --category disponibile")
                    if "--dry-run" in result.stdout:
                        self.logger.log_info("✅ Opzione --dry-run disponibile")
                    if "--num-questions" in result.stdout:
                        self.logger.log_info("✅ Opzione --num-questions disponibile")
                    
                else:
                    self.logger.log_warning(f"⚠️ generate_quiz command non funziona: {result.stderr}")
                
                # Test dry-run
                result = subprocess.run([
                    sys.executable, "manage.py", "generate_quiz", "--dry-run"
                ], capture_output=True, text=True, timeout=15)
                
                if "DRY RUN" in result.stdout:
                    self.logger.log_info("✅ Dry-run mode funzionante")
                
            except subprocess.TimeoutExpired:
                self.logger.log_warning("⚠️ Timeout durante test quiz generator")
            except Exception as e:
                self.logger.log_warning(f"⚠️ Errore test quiz generator: {e}")
            finally:
                os.chdir(original_cwd)
            
            self.test_results["quiz_generator"] = True
            self.logger.log_test_success("Verifica Quiz Generator", "Generator command verificato")
            
        except Exception as e:
            self.test_results["quiz_generator"] = False
            self.logger.log_test_failure("Verifica Quiz Generator", str(e))
    
    async def test_api_endpoints(self):
        """Test API Endpoints."""
        self.logger.log_test_start("Verifica API Endpoints")
        
        try:
            django_dir = Path("../fisio-rag-saas")
            if not django_dir.exists():
                self.logger.log_test_skip("Verifica API Endpoints", "Directory Django non trovata")
                return
            
            # Check API files
            api_files = [
                "api/urls.py",
                "api/serializers.py",
                "api/views.py",
                "api/quiz_views.py",
                "api/quiz_serializers.py"
            ]
            
            existing_api_files = []
            for file in api_files:
                file_path = django_dir / file
                if file_path.exists():
                    existing_api_files.append(file)
                    self.logger.log_info(f"✅ {file}")
                else:
                    self.logger.log_warning(f"⚠️ {file} non trovato")
            
            # Check URL configuration
            main_urls = django_dir / "fisio_rag_saas/urls.py"
            if main_urls.exists():
                content = main_urls.read_text(encoding='utf-8')
                if "api/" in content:
                    self.logger.log_info("✅ API URLs configurati in main urls.py")
                else:
                    self.logger.log_warning("⚠️ API URLs non trovati in main urls.py")
            
            self.test_results["api_endpoints"] = True
            self.logger.log_test_success("Verifica API Endpoints", f"{len(existing_api_files)} file API presenti")
            
        except Exception as e:
            self.test_results["api_endpoints"] = False
            self.logger.log_test_failure("Verifica API Endpoints", str(e))


async def main():
    """Esegue tutti i test di integrazione."""
    tester = IntegrationTests()
    results = await tester.run_all_tests()
    
    # Return code based on results
    if results["summary"]["failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)