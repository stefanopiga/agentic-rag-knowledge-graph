"""
Incremental ingestion manager for medical documents.
Handles tracking, cleanup, and structured citations.
"""

import os
import hashlib
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

import asyncpg
from dotenv import load_dotenv

# Import database utilities
try:
    from ..agent.db_utils import db_pool
except ImportError:
    # For direct execution or testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent.db_utils import db_pool

load_dotenv()
logger = logging.getLogger(__name__)


class IngestionAction(Enum):
    """Actions for document ingestion."""
    SKIP = "skip"
    INGEST = "ingest"
    REINGEST = "reingest"
    CLEANUP_AND_REINGEST = "cleanup_and_reingest"


@dataclass
class DocumentScanResult:
    """Result of document scanning."""
    file_path: str
    category: str
    document_order: int
    current_hash: str
    file_size: int
    last_modified: datetime
    action: IngestionAction
    reason: str
    existing_status: Optional[Dict[str, Any]] = None


@dataclass
class IngestionStatusRecord:
    """Database record for ingestion status."""
    id: int
    file_path: str
    file_hash: str
    file_size: int
    last_modified: datetime
    status: str
    chunks_created: int
    chunks_expected: int
    entities_extracted: int
    graph_episodes_created: int
    category: Optional[str]
    document_order: Optional[int]
    priority_weight: int
    ingestion_started_at: Optional[datetime]
    ingestion_completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class IncrementalIngestionManager:
    """Manages incremental document ingestion and cleanup."""
    
    def __init__(self):
        """Initialize the incremental ingestion manager."""
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connections."""
        if not self._initialized:
            # Database connection is managed by db_pool
            self._initialized = True
    
    async def scan_documents(self, base_path: str) -> List[DocumentScanResult]:
        """
        Scansiona documenti e determina azioni necessarie.
        
        Args:
            base_path: Path base per la scansione documenti
            
        Returns:
            Lista di risultati scansione con azioni da eseguire
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"Scanning documents in: {base_path}")
        
        results = []
        document_files = self._find_all_documents(base_path)
        
        logger.info(f"Found {len(document_files)} document files")
        
        for file_path in document_files:
            try:
                # Calcola hash e metadati file
                file_hash = self._calculate_file_hash(file_path)
                file_stat = os.stat(file_path)
                file_size = file_stat.st_size
                last_modified = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)
                
                # Estrai metadati da struttura directory
                category, order = self._extract_metadata_from_path(file_path)
                
                # Controlla stato nel database
                status_record = await self._get_ingestion_status(file_path)
                
                # Determina azione necessaria
                action, reason = self._determine_action(status_record, file_hash, file_size, last_modified)
                
                results.append(DocumentScanResult(
                    file_path=file_path,
                    category=category,
                    document_order=order,
                    current_hash=file_hash,
                    file_size=file_size,
                    last_modified=last_modified,
                    action=action,
                    reason=reason,
                    existing_status=status_record.__dict__ if status_record else None
                ))
                
            except Exception as e:
                logger.error(f"Error scanning {file_path}: {e}")
                results.append(DocumentScanResult(
                    file_path=file_path,
                    category="error",
                    document_order=999,
                    current_hash="",
                    file_size=0,
                    last_modified=datetime.now(tz=timezone.utc),
                    action=IngestionAction.SKIP,
                    reason=f"Scan error: {str(e)}"
                ))
        
        return results
    
    def _find_all_documents(self, base_path: str) -> List[str]:
        """Find all supported document files."""
        if not os.path.exists(base_path):
            logger.warning(f"Base path not found: {base_path}")
            return []
        
        # Support DOCX, PDF, TXT, and markdown files
        patterns = ["*.docx", "*.pdf", "*.txt", "*.md", "*.markdown"]
        files = []
        
        for pattern in patterns:
            import glob
            found_files = glob.glob(os.path.join(base_path, "**", pattern), recursive=True)
            # Filter out temporary files (starting with ~$)
            found_files = [f for f in found_files if not os.path.basename(f).startswith('~$')]
            files.extend(found_files)
        
        return sorted(files)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file content."""
        hash_sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def _extract_metadata_from_path(self, file_path: str) -> Tuple[str, int]:
        """
        Estrae categoria e ordine da percorso file.
        
        Esempio: documents/fisioterapia/master/caviglia_e_piede/01_anatomia.docx
        -> categoria: caviglia_e_piede, ordine: 1
        """
        try:
            parts = Path(file_path).parts
            
            # Cerca la struttura master
            master_index = None
            for i, part in enumerate(parts):
                if part == 'master':
                    master_index = i
                    break
            
            if master_index is not None and len(parts) > master_index + 2:
                # Categoria è la cartella dopo 'master'
                category = parts[master_index + 1]
                
                # Estrai numero ordine da nome file
                filename = parts[-1]
                order_match = re.match(r'^(\d+)_', filename)
                order = int(order_match.group(1)) if order_match else 999
                
                return category, order
            
            # Fallback: usa nome cartella genitore e ordine default
            if len(parts) >= 2:
                category = parts[-2]
            else:
                category = "uncategorized"
                
            return category, 999
            
        except Exception as e:
            logger.warning(f"Error extracting metadata from path {file_path}: {e}")
            return "uncategorized", 999
    
    async def _get_ingestion_status(self, file_path: str) -> Optional[IngestionStatusRecord]:
        """Get ingestion status record from database."""
        try:
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM document_ingestion_status WHERE file_path = $1",
                    file_path
                )
                
                if row:
                    return IngestionStatusRecord(**dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Error getting ingestion status for {file_path}: {e}")
            return None
    
    def _determine_action(
        self, 
        status_record: Optional[IngestionStatusRecord], 
        current_hash: str, 
        current_size: int,
        current_modified: datetime
    ) -> Tuple[IngestionAction, str]:
        """Determina azione per il documento."""
        
        if not status_record:
            return IngestionAction.INGEST, "New document"
        
        # File modificato (hash o dimensione diversa)
        if (status_record.file_hash != current_hash or 
            status_record.file_size != current_size):
            return IngestionAction.CLEANUP_AND_REINGEST, "File modified"
        
        # Completato con successo
        if status_record.status == 'completed':
            return IngestionAction.SKIP, "Already completed"
        
        # Fallito o parziale
        if status_record.status in ['failed', 'partial']:
            return IngestionAction.CLEANUP_AND_REINGEST, f"Previous {status_record.status}"
        
        # In processing ma "bloccato" (> 2 ore)
        if status_record.status == 'processing':
            if self._is_stale_processing(status_record):
                return IngestionAction.CLEANUP_AND_REINGEST, "Stale processing"
            else:
                return IngestionAction.SKIP, "Currently processing"
        
        # Pending
        if status_record.status == 'pending':
            return IngestionAction.INGEST, "Resume pending"
        
        return IngestionAction.INGEST, "Unknown status"
    
    def _is_stale_processing(self, status_record: IngestionStatusRecord) -> bool:
        """Check if processing is stale (stuck)."""
        if not status_record.ingestion_started_at:
            return True
        
        now = datetime.now(tz=timezone.utc)
        processing_time = now - status_record.ingestion_started_at
        
        # Consider stale if processing for more than 2 hours
        return processing_time.total_seconds() > 7200
    
    async def create_or_update_status(
        self, 
        file_path: str, 
        file_hash: str, 
        file_size: int,
        last_modified: datetime,
        category: str,
        document_order: int,
        status: str = 'pending'
    ) -> int:
        """Create or update ingestion status record."""
        try:
            priority_weight = self.calculate_citation_priority(category, document_order)
            
            async with db_pool.acquire() as conn:
                # Try update first
                result = await conn.fetchrow("""
                    UPDATE document_ingestion_status 
                    SET file_hash = $2, file_size = $3, last_modified = $4,
                        category = $5, document_order = $6, priority_weight = $7,
                        status = $8, updated_at = NOW()
                    WHERE file_path = $1
                    RETURNING id
                """, file_path, file_hash, file_size, last_modified, 
                    category, document_order, priority_weight, status)
                
                if result:
                    return result['id']
                
                # Insert new record
                result = await conn.fetchrow("""
                    INSERT INTO document_ingestion_status 
                    (file_path, file_hash, file_size, last_modified, category, 
                     document_order, priority_weight, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                """, file_path, file_hash, file_size, last_modified,
                    category, document_order, priority_weight, status)
                
                return result['id']
                
        except Exception as e:
            logger.error(f"Error creating/updating status for {file_path}: {e}")
            raise
    
    async def update_status(self, status_id: int, **kwargs):
        """Update specific fields in status record."""
        try:
            if not kwargs:
                return
            
            # Build dynamic UPDATE query
            set_clauses = []
            values = []
            param_num = 1
            
            for key, value in kwargs.items():
                set_clauses.append(f"{key} = ${param_num}")
                values.append(value)
                param_num += 1
            
            # Always update timestamp
            set_clauses.append(f"updated_at = NOW()")
            
            query = f"""
                UPDATE document_ingestion_status 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_num}
            """
            values.append(status_id)
            
            async with db_pool.acquire() as conn:
                await conn.execute(query, *values)
                
        except Exception as e:
            logger.error(f"Error updating status {status_id}: {e}")
            raise
    
    async def cleanup_incomplete_ingestion(self, file_path: str):
        """Pulisce dati di ingestion incompleta."""
        logger.info(f"Cleaning up incomplete ingestion for: {file_path}")
        
        try:
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    # 1. Get document IDs to clean
                    doc_rows = await conn.fetch(
                        "SELECT id FROM documents WHERE source = $1 OR source LIKE $2",
                        file_path, f"%{os.path.basename(file_path)}"
                    )
                    
                    doc_ids = [row['id'] for row in doc_rows]
                    
                    if doc_ids:
                        # 2. Remove chunks
                        chunks_deleted = await conn.fetchval(
                            "DELETE FROM chunks WHERE document_id = ANY($1) RETURNING COUNT(*)",
                            doc_ids
                        )
                        logger.info(f"Deleted {chunks_deleted or 0} chunks")
                        
                        # 3. Remove documents
                        docs_deleted = await conn.fetchval(
                            "DELETE FROM documents WHERE id = ANY($1) RETURNING COUNT(*)",
                            doc_ids
                        )
                        logger.info(f"Deleted {docs_deleted or 0} documents")
                    
                    # 4. Reset ingestion status
                    await conn.execute("""
                        UPDATE document_ingestion_status 
                        SET status = 'pending', 
                            chunks_created = 0,
                            chunks_expected = 0,
                            entities_extracted = 0,
                            graph_episodes_created = 0,
                            ingestion_started_at = NULL,
                            ingestion_completed_at = NULL,
                            updated_at = NOW()
                        WHERE file_path = $1
                    """, file_path)
                    
            logger.info(f"✓ Cleanup completed for: {file_path}")
                    
        except Exception as e:
            logger.error(f"Error during cleanup of {file_path}: {e}")
            raise
    
    def calculate_citation_priority(self, category: str, document_order: int) -> int:
        """Calcola priorità per ordinamento citazioni."""
        
        # Priorità categorie (lower = higher priority)
        category_priorities = {
            'caviglia_e_piede': 10,
            'ginocchio': 20, 
            'lombare': 30,
            'toracico': 40,
            'lombo_pelvico': 50,
            'uncategorized': 100
        }
        
        base_priority = category_priorities.get(category, 100)
        return base_priority + document_order  # 11, 12, 13... per caviglia_e_piede
    
    async def get_ingestion_report(self) -> Dict[str, Any]:
        """Generate comprehensive ingestion status report."""
        try:
            async with db_pool.acquire() as conn:
                # Overall statistics
                overall_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_documents,
                        COUNT(*) FILTER (WHERE status = 'completed') as completed,
                        COUNT(*) FILTER (WHERE status = 'partial') as partial,
                        COUNT(*) FILTER (WHERE status = 'failed') as failed,
                        COUNT(*) FILTER (WHERE status = 'processing') as processing,
                        COUNT(*) FILTER (WHERE status = 'pending') as pending
                    FROM document_ingestion_status
                """)
                
                # Category breakdown
                category_stats = await conn.fetch("""
                    SELECT 
                        category,
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'completed') as completed,
                        COUNT(*) FILTER (WHERE status != 'completed') as incomplete
                    FROM document_ingestion_status
                    WHERE category IS NOT NULL
                    GROUP BY category
                    ORDER BY category
                """)
                
                # Problem documents
                problem_docs = await conn.fetch("""
                    SELECT file_path, status, category, document_order, updated_at
                    FROM document_ingestion_status
                    WHERE status IN ('failed', 'partial', 'processing')
                    ORDER BY category, document_order
                """)
                
                return {
                    'overall': dict(overall_stats) if overall_stats else {},
                    'by_category': [dict(row) for row in category_stats],
                    'problem_documents': [dict(row) for row in problem_docs]
                }
                
        except Exception as e:
            logger.error(f"Error generating ingestion report: {e}")
            return {}
    
    async def cleanup_category(self, category: str):
        """Clean up all documents in a specific category."""
        logger.info(f"Cleaning up category: {category}")
        
        try:
            async with db_pool.acquire() as conn:
                # Get all files in category
                files = await conn.fetch(
                    "SELECT file_path FROM document_ingestion_status WHERE category = $1",
                    category
                )
                
                for file_row in files:
                    await self.cleanup_incomplete_ingestion(file_row['file_path'])
                
                logger.info(f"✓ Category cleanup completed: {category}")
                
        except Exception as e:
            logger.error(f"Error cleaning up category {category}: {e}")
            raise


# Factory function
def create_incremental_manager() -> IncrementalIngestionManager:
    """Create incremental ingestion manager instance."""
    return IncrementalIngestionManager()


# Citation formatting utilities
class CitationFormatter:
    """Formats structured citations for medical documents."""
    
    @staticmethod
    def format_single_citation(category: str, document_order: int, title: str, page: int) -> str:
        """Format a single citation."""
        category_display = category.replace('_', ' ').title()
        return f"[{category_display}] Doc.{document_order:02d} - {title}, pagina {page}"
    
    @staticmethod
    def format_multiple_citations(sources: List[Dict[str, Any]]) -> str:
        """Format multiple citations ordered by priority."""
        if not sources:
            return ""
        
        # Sort by priority_weight
        sorted_sources = sorted(sources, key=lambda s: s.get('priority_weight', 999))
        
        citations = []
        for source in sorted_sources:
            citation = CitationFormatter.format_single_citation(
                source.get('category', 'uncategorized'),
                source.get('document_order', 0),
                source.get('title', 'Unknown'),
                source.get('page', 0)
            )
            citations.append(citation)
        
        if len(citations) == 1:
            return f"Fonte: {citations[0]}"
        else:
            return f"Fonti: {'; '.join(citations)}"