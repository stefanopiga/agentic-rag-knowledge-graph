"""
Manager per recovery granulare delle sezioni fallite.
Consente re-ingestione solo delle sezioni problematiche.
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

import asyncpg
from dotenv import load_dotenv

# Import database utilities
try:
    from ..agent.db_utils import db_pool
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent.db_utils import db_pool

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class SectionStatus:
    """Status di una sezione documento."""
    id: int
    document_status_id: int
    section_position: int
    section_type: str
    section_hash: str
    status: str
    error_message: Optional[str]
    chunks_created: int
    entities_extracted: int


class SectionRecoveryManager:
    """Manager per recovery intelligente delle sezioni."""
    
    def __init__(self):
        """Initialize section recovery manager."""
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connections."""
        if not self._initialized:
            self._initialized = True
    
    async def track_section(self, 
                          document_status_id: int,
                          section_position: int,
                          section_type: str,
                          content: str,
                          metadata: Optional[Dict] = None) -> int:
        """
        Track una nuova sezione per elaborazione.
        
        Args:
            document_status_id: ID del documento parent
            section_position: Posizione sezione nel documento
            section_type: Tipo sezione (paragraph, table, etc.)
            content: Contenuto sezione
            metadata: Metadati opzionali
            
        Returns:
            ID della sezione creata
        """
        if not self._initialized:
            await self.initialize()
        
        section_hash = self._calculate_section_hash(content)
        content_preview = content[:200] if content else ""
        
        async with db_pool.acquire() as conn:
            section_id = await conn.fetchval("""
                INSERT INTO document_sections (
                    document_status_id, section_position, section_type, section_hash,
                    content_length, content_preview, status, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (document_status_id, section_position) 
                DO UPDATE SET
                    section_type = EXCLUDED.section_type,
                    section_hash = EXCLUDED.section_hash,
                    content_length = EXCLUDED.content_length,
                    content_preview = EXCLUDED.content_preview,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                RETURNING id
            """, document_status_id, section_position, section_type, section_hash,
                len(content), content_preview, 'pending', metadata)
        
        logger.debug(f"Tracked section {section_position} for document {document_status_id}")
        return section_id
    
    async def update_section_status(self,
                                   section_id: int,
                                   status: str,
                                   chunks_created: int = 0,
                                   entities_extracted: int = 0,
                                   graph_episodes_created: int = 0,
                                   error_message: Optional[str] = None):
        """
        Aggiorna status di una sezione.
        
        Args:
            section_id: ID sezione
            status: Nuovo status (processing, completed, failed)
            chunks_created: Numero chunks creati
            entities_extracted: Numero entità estratte
            graph_episodes_created: Episodi knowledge graph
            error_message: Messaggio errore se failed
        """
        if not self._initialized:
            await self.initialize()
        
        now = datetime.now(timezone.utc)
        
        async with db_pool.acquire() as conn:
            if status == 'processing':
                await conn.execute("""
                    UPDATE document_sections 
                    SET status = $1, processing_started_at = $2, updated_at = $2
                    WHERE id = $3
                """, status, now, section_id)
            
            elif status in ['completed', 'failed']:
                await conn.execute("""
                    UPDATE document_sections 
                    SET status = $1, 
                        chunks_created = $2,
                        entities_extracted = $3,
                        graph_episodes_created = $4,
                        error_message = $5,
                        processing_completed_at = $6,
                        updated_at = $6
                    WHERE id = $7
                """, status, chunks_created, entities_extracted, 
                    graph_episodes_created, error_message, now, section_id)
        
        logger.debug(f"Updated section {section_id} status to {status}")
    
    async def get_failed_sections(self, document_status_id: Optional[int] = None) -> List[SectionStatus]:
        """
        Recupera sezioni fallite per recovery.
        
        Args:
            document_status_id: Se specificato, filtra per documento
            
        Returns:
            Lista sezioni fallite
        """
        if not self._initialized:
            await self.initialize()
        
        async with db_pool.acquire() as conn:
            if document_status_id:
                rows = await conn.fetch("""
                    SELECT id, document_status_id, section_position, section_type, 
                           section_hash, status, error_message, chunks_created, entities_extracted
                    FROM document_sections
                    WHERE document_status_id = $1 AND status = 'failed'
                    ORDER BY section_position
                """, document_status_id)
            else:
                rows = await conn.fetch("""
                    SELECT id, document_status_id, section_position, section_type,
                           section_hash, status, error_message, chunks_created, entities_extracted
                    FROM document_sections
                    WHERE status = 'failed'
                    ORDER BY document_status_id, section_position
                """)
        
        return [
            SectionStatus(
                id=row['id'],
                document_status_id=row['document_status_id'],
                section_position=row['section_position'],
                section_type=row['section_type'],
                section_hash=row['section_hash'],
                status=row['status'],
                error_message=row['error_message'],
                chunks_created=row['chunks_created'],
                entities_extracted=row['entities_extracted']
            )
            for row in rows
        ]
    
    async def cleanup_failed_sections(self, document_status_id: int) -> int:
        """
        Cleanup sezioni fallite per re-processing.
        
        Args:
            document_status_id: ID documento
            
        Returns:
            Numero sezioni pulite
        """
        if not self._initialized:
            await self.initialize()
        
        async with db_pool.acquire() as conn:
            sections_cleaned = await conn.fetchval("""
                SELECT cleanup_failed_sections($1)
            """, document_status_id)
        
        logger.info(f"Cleaned {sections_cleaned} failed sections for document {document_status_id}")
        return sections_cleaned
    
    async def get_section_recovery_report(self) -> Dict[str, Any]:
        """
        Genera report per recovery sezioni.
        
        Returns:
            Report con statistiche recovery
        """
        if not self._initialized:
            await self.initialize()
        
        async with db_pool.acquire() as conn:
            # Statistiche generali
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_sections,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    COUNT(*) FILTER (WHERE status = 'processing') as processing,
                    COUNT(*) FILTER (WHERE status = 'pending') as pending
                FROM document_sections
            """)
            
            # Documenti con sezioni fallite
            failed_docs = await conn.fetch("""
                SELECT 
                    dis.file_path,
                    dis.category,
                    COUNT(*) as failed_sections,
                    STRING_AGG(ds.section_position::text, ', ' ORDER BY ds.section_position) as positions
                FROM document_sections ds
                JOIN document_ingestion_status dis ON ds.document_status_id = dis.id
                WHERE ds.status = 'failed'
                GROUP BY dis.file_path, dis.category
                ORDER BY failed_sections DESC
            """)
        
        return {
            'overall': dict(stats) if stats else {},
            'failed_documents': [
                {
                    'file_path': row['file_path'],
                    'category': row['category'],
                    'failed_sections': row['failed_sections'],
                    'section_positions': row['positions']
                }
                for row in failed_docs
            ]
        }
    
    def _calculate_section_hash(self, content: str) -> str:
        """Calculate hash for section content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()


def create_section_recovery_manager() -> SectionRecoveryManager:
    """Create section recovery manager."""
    return SectionRecoveryManager()