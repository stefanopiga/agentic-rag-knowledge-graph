#!/usr/bin/env python3
"""
Test completo integrazione RAG + Django + Neo4j
per il progetto fisio-rag-saas
"""

import os
import sys

def test_integration():
    print('🔍 TESTING COMPLETE RAG INTEGRATION...')
    print()
    
    results = []
    
    # Test 1: Import moduli RAG esistenti
    try:
        from agent.agent import get_agent
        print('✅ Agent module: Import riuscito')
        results.append('✅ Agent')
    except Exception as e:
        print(f'❌ Agent module: {e}')
        results.append('❌ Agent')
    
    # Test 2: Import Django models
    try:
        # Setup Django
        sys.path.append('fisio_rag_saas')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        
        import django
        django.setup()
        
        from accounts.models import Tenant, User
        from medical_content.models import Quiz
        from rag_engine.models import ChatSession
        print('✅ Django models: Import riuscito')
        results.append('✅ Django')
    except Exception as e:
        print(f'❌ Django models: {e}')
        results.append('❌ Django')
    
    # Test 3: Neo4j integration
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'), 
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
        driver.verify_connectivity()
        driver.close()
        print('✅ Neo4j integration: Connessione attiva')
        results.append('✅ Neo4j')
    except Exception as e:
        print(f'❌ Neo4j integration: {e}')
        results.append('❌ Neo4j')
    
    # Test 4: Database operations
    try:
        # Test query Django
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM accounts_tenant")
        tenant_count = cursor.fetchone()[0]
        print(f'✅ Database operations: {tenant_count} tenants in DB')
        results.append('✅ Database')
    except Exception as e:
        print(f'❌ Database operations: {e}')
        results.append('❌ Database')
    
    print()
    print('📊 RISULTATI TEST:')
    for result in results:
        print(f'  {result}')
    
    print()
    success_count = len([r for r in results if '✅' in r])
    total_count = len(results)
    print(f'🎯 SUCCESSO: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)')
    
    if success_count == total_count:
        print('🎉 INTEGRATION TEST: COMPLETAMENTE RIUSCITO!')
    else:
        print('⚠️ INTEGRATION TEST: Alcuni problemi da risolvere')

if __name__ == '__main__':
    test_integration()