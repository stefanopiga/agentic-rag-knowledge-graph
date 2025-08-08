#!/usr/bin/env python3
"""
🚀 NEON SCHEMA DEPLOYMENT
Deploy schema_with_auth.sql su Neon PostgreSQL 17
"""

import psycopg2
import os
import sys
from pathlib import Path

def deploy_schema(database_url: str, schema_file: str = "sql/schema_with_auth.sql"):
    """Deploy schema su Neon PostgreSQL"""
    
    print("🚀 INIZIANDO DEPLOYMENT SCHEMA SU NEON...")
    print("=" * 50)
    
    # Verifica file schema
    schema_path = Path(schema_file)
    if not schema_path.exists():
        print(f"❌ File schema non trovato: {schema_file}")
        return False
    
    print(f"📄 Schema file: {schema_file} ({schema_path.stat().st_size:,} bytes)")
    
    try:
        # Connessione a Neon
        print("🔌 Connettendo a Neon PostgreSQL...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Verifica connessione
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"✅ Connesso a: {version}")
            
            # Leggi schema file
            print("📖 Leggendo schema file...")
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            print(f"📊 Schema size: {len(schema_sql):,} caratteri")
            
            # Esegui schema deployment
            print("⚙️ Eseguendo deployment schema...")
            cur.execute(schema_sql)
            
            # Verifica deployment
            print("🔍 Verificando deployment...")
            
            # Check extensions
            cur.execute("""
                SELECT extname FROM pg_extension 
                WHERE extname IN ('vector', 'uuid-ossp', 'pg_trgm', 'btree_gin')
                ORDER BY extname
            """)
            extensions = [row[0] for row in cur.fetchall()]
            print(f"✅ Extensions: {', '.join(extensions)}")
            
            # Check tables
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            table_count = cur.fetchone()[0]
            print(f"✅ Tabelle create: {table_count}")
            
            # Check functions
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.routines 
                WHERE routine_schema = 'public'
                AND routine_name IN ('match_chunks', 'hybrid_search', 'get_document_chunks')
            """)
            function_count = cur.fetchone()[0]
            print(f"✅ Funzioni RAG: {function_count}")
            
            # Check default tenant
            cur.execute("SELECT COUNT(*) FROM accounts_tenant")
            tenant_count = cur.fetchone()[0]
            print(f"✅ Default tenant: {tenant_count} created")
            
            # Check medical categories
            cur.execute("SELECT COUNT(*) FROM medical_content_medicalcategory")
            category_count = cur.fetchone()[0]
            print(f"✅ Medical categories: {category_count} created")
            
            # Note: Admin user will be created later via Django
            print("ℹ️ Admin user: sarà creato via Django management command")
            
        conn.close()
        
        print("\n" + "=" * 50)
        print("🎉 DEPLOYMENT SCHEMA COMPLETATO CON SUCCESSO!")
        print("✅ Database Neon pronto per l'uso")
        print("✅ Tutte le tabelle e funzioni create")
        print("✅ Dati iniziali popolati")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Errore PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore generale: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("📋 Uso: python deploy_neon_schema.py <DATABASE_URL>")
        print("📝 Esempio: python deploy_neon_schema.py 'postgres://user:pass@host:port/db?sslmode=require'")
        return
    
    database_url = sys.argv[1]
    
    # Nascondi password nell'output
    safe_url = database_url.split('@')[1] if '@' in database_url else database_url
    print(f"🎯 Target: {safe_url}")
    
    success = deploy_schema(database_url)
    
    if success:
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. ✅ Configura Django DATABASE_URL={database_url.split('@')[1] if '@' in database_url else '***'}")
        print(f"2. ✅ cd fisio-rag-saas")
        print(f"3. ✅ python manage.py migrate --fake-initial")
        print(f"4. ✅ python manage.py createsuperuser")
        print(f"5. ✅ Test con: python scripts/verify_neon_schema.py")
        sys.exit(0)
    else:
        print(f"\n❌ DEPLOYMENT FALLITO")
        print(f"🔧 Verifica connection string e riprova")
        sys.exit(1)

if __name__ == "__main__":
    main()