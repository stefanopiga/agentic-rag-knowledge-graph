#!/usr/bin/env python3
"""
Deploy schema per section tracking granulare.
Esegue il deploy delle tabelle e funzioni per recovery sezioni.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncpg
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


async def deploy_section_tracking_schema():
    """Deploy section tracking schema to database."""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    schema_file = project_root / 'sql' / 'section_tracking_schema.sql'
    
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    
    print(f"🔄 Deploying section tracking schema...")
    print(f"📁 Schema file: {schema_file}")
    print(f"🔗 Database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    
    try:
        # Read schema SQL
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Connect and execute
        conn = await asyncpg.connect(database_url)
        
        try:
            # Execute schema deployment
            await conn.execute(schema_sql)
            print("✅ Section tracking schema deployed successfully")
            
            # Verify deployment
            tables_created = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('document_sections')
            """)
            
            views_created = await conn.fetch("""
                SELECT table_name as view_name
                FROM information_schema.views 
                WHERE table_schema = 'public' 
                AND table_name IN ('failed_sections')
            """)
            
            functions_created = await conn.fetch("""
                SELECT routine_name 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_name IN ('cleanup_failed_sections', 'update_document_sections_timestamp')
            """)
            
            print(f"\n📊 Deployment verification:")
            print(f"  ✅ Tables: {len(tables_created)} created")
            for table in tables_created:
                print(f"    - {table['table_name']}")
            
            print(f"  ✅ Views: {len(views_created)} created")
            for view in views_created:
                print(f"    - {view['view_name']}")
            
            print(f"  ✅ Functions: {len(functions_created)} created")
            for func in functions_created:
                print(f"    - {func['routine_name']}")
            
            # Test section tracking functionality
            print(f"\n🧪 Testing section tracking...")
            
            # Test insert
            await conn.execute("""
                INSERT INTO document_sections (
                    document_status_id, section_position, section_type, section_hash,
                    content_length, content_preview, status
                ) VALUES (-1, 999, 'test', 'test_hash', 100, 'test content preview', 'pending')
                ON CONFLICT DO NOTHING
            """)
            
            # Test cleanup function
            result = await conn.fetchval("SELECT cleanup_failed_sections(-1)")
            
            # Cleanup test data
            await conn.execute("DELETE FROM document_sections WHERE document_status_id = -1")
            
            print(f"  ✅ Section tracking functional")
            
        finally:
            await conn.close()
    
    except Exception as e:
        print(f"❌ Schema deployment failed: {str(e)}")
        raise
    
    print(f"\n🎉 Section tracking deployment completed successfully!")
    print(f"\n📋 Available commands:")
    print(f"  python -m ingestion.ingest --recovery-report")
    print(f"  python -m ingestion.ingest --cleanup-failed-sections")


async def main():
    """Main function."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    try:
        await deploy_section_tracking_schema()
    except KeyboardInterrupt:
        print("\n⚠️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())