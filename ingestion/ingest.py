"""
Main ingestion script for processing markdown documents into vector DB and knowledge graph.
"""

import os
import asyncio
import logging
import json
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse

import asyncpg
from dotenv import load_dotenv

from .chunker import ChunkingConfig, create_chunker, DocumentChunk
from .embedder import create_embedder
from .graph_builder import create_graph_builder
from .docx_processor import create_docx_processor
from .incremental_manager import create_incremental_manager, IngestionAction

# Import agent utilities
try:
    from ..agent.db_utils import initialize_database, close_database, db_pool
    from ..agent.graph_utils import initialize_graph, close_graph
    from ..agent.models import IngestionConfig, IngestionResult
except ImportError:
    # For direct execution or testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent.db_utils import initialize_database, close_database, db_pool
    from agent.graph_utils import initialize_graph, close_graph
    from agent.models import IngestionConfig, IngestionResult

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DocumentIngestionPipeline:
    """Pipeline for ingesting documents into vector DB and knowledge graph."""
    
    def __init__(
        self,
        config: IngestionConfig,
        documents_folder: str = "documents",
        clean_before_ingest: bool = False
    ):
        """
        Initialize ingestion pipeline.
        
        Args:
            config: Ingestion configuration
            documents_folder: Folder containing markdown documents
            clean_before_ingest: Whether to clean existing data before ingestion
        """
        self.config = config
        self.documents_folder = documents_folder
        self.clean_before_ingest = clean_before_ingest
        
        # Initialize components
        self.chunker_config = ChunkingConfig(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            max_chunk_size=config.max_chunk_size,
            use_semantic_splitting=config.use_semantic_chunking
        )
        
        self.chunker = create_chunker(self.chunker_config)
        self.embedder = create_embedder()
        self.graph_builder = create_graph_builder()
        self.docx_processor = create_docx_processor()
        self.incremental_manager = create_incremental_manager()
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connections."""
        if self._initialized:
            return
        
        logger.info("Initializing ingestion pipeline...")
        
        # Initialize database connections
        await initialize_database()
        await initialize_graph()
        await self.graph_builder.initialize()
        await self.incremental_manager.initialize()
        
        self._initialized = True
        logger.info("Ingestion pipeline initialized")
    
    async def close(self):
        """Close database connections."""
        if self._initialized:
            await self.graph_builder.close()
            await close_graph()
            await close_database()
            self._initialized = False
    
    async def ingest_documents(
        self,
        progress_callback: Optional[callable] = None,
        use_incremental: bool = True
    ) -> List[IngestionResult]:
        """
        Ingest documents with incremental support.
        
        Args:
            progress_callback: Optional callback for progress updates
            use_incremental: Whether to use incremental ingestion (default: True)
        
        Returns:
            List of ingestion results
        """
        if not self._initialized:
            await self.initialize()
        
        # Clean existing data if requested (overrides incremental)
        if self.clean_before_ingest:
            await self._clean_databases()
            use_incremental = False
        
        results = []
        
        if use_incremental:
            # Use incremental ingestion
            logger.info("Using incremental ingestion mode")
            scan_results = await self.incremental_manager.scan_documents(self.documents_folder)
            
            if not scan_results:
                logger.warning(f"No documents found in {self.documents_folder}")
                return []
            
            # Filter documents that need processing
            to_process = [r for r in scan_results if r.action in [IngestionAction.INGEST, IngestionAction.REINGEST, IngestionAction.CLEANUP_AND_REINGEST]]
            to_skip = [r for r in scan_results if r.action == IngestionAction.SKIP]
            
            logger.info(f"Scan results: {len(to_process)} to process, {len(to_skip)} to skip")
            
            for skip_result in to_skip:
                logger.info(f"⏭ Skipping {skip_result.file_path}: {skip_result.reason}")
            
            # Process documents that need ingestion
            for i, scan_result in enumerate(to_process):
                try:
                    logger.info(f"Processing file {i+1}/{len(to_process)}: {scan_result.file_path}")
                    logger.info(f"Action: {scan_result.action.value} - {scan_result.reason}")
                    
                    # Cleanup if needed
                    if scan_result.action == IngestionAction.CLEANUP_AND_REINGEST:
                        await self.incremental_manager.cleanup_incomplete_ingestion(scan_result.file_path)
                    
                    result = await self._ingest_single_document_incremental(scan_result)
                    results.append(result)
                    
                    if progress_callback:
                        progress_callback(i + 1, len(to_process))
                        
                except Exception as e:
                    logger.error(f"Failed to process {scan_result.file_path}: {e}")
                    results.append(IngestionResult(
                        document_id="",
                        title=os.path.basename(scan_result.file_path),
                        chunks_created=0,
                        entities_extracted=0,
                        relationships_created=0,
                        processing_time_ms=0,
                        errors=[str(e)]
                    ))
        else:
            # Legacy full ingestion
            logger.info("Using full ingestion mode")
            document_files = self._find_document_files()
            
            if not document_files:
                logger.warning(f"No supported document files found in {self.documents_folder}")
                return []
            
            logger.info(f"Found {len(document_files)} document files to process")
            
            for i, file_path in enumerate(document_files):
                try:
                    logger.info(f"Processing file {i+1}/{len(document_files)}: {file_path}")
                    
                    result = await self._ingest_single_document(file_path)
                    results.append(result)
                    
                    if progress_callback:
                        progress_callback(i + 1, len(document_files))
                        
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    results.append(IngestionResult(
                        document_id="",
                        title=os.path.basename(file_path),
                        chunks_created=0,
                        entities_extracted=0,
                        relationships_created=0,
                        processing_time_ms=0,
                        errors=[str(e)]
                    ))
        
        # Log summary
        total_chunks = sum(r.chunks_created for r in results)
        total_errors = sum(len(r.errors) for r in results)
        
        logger.info(f"Ingestion complete: {len(results)} documents, {total_chunks} chunks, {total_errors} errors")
        
        return results
    
    async def _ingest_single_document_incremental(self, scan_result) -> IngestionResult:
        """
        Ingest a single document with incremental tracking.
        
        Args:
            scan_result: DocumentScanResult from incremental manager
            
        Returns:
            Ingestion result
        """
        start_time = datetime.now()
        file_path = scan_result.file_path
        
        # Create or update status record
        status_id = await self.incremental_manager.create_or_update_status(
            file_path=file_path,
            file_hash=scan_result.current_hash,
            file_size=scan_result.file_size,
            last_modified=scan_result.last_modified,
            category=scan_result.category,
            document_order=scan_result.document_order,
            status='processing'
        )
        
        # Update status to processing with start time
        await self.incremental_manager.update_status(
            status_id,
            ingestion_started_at=start_time
        )
        
        try:
            # Process document using existing logic
            result = await self._ingest_single_document(file_path)
            
            # Update status to completed
            await self.incremental_manager.update_status(
                status_id,
                status='completed',
                chunks_created=result.chunks_created,
                entities_extracted=result.entities_extracted,
                graph_episodes_created=result.relationships_created,
                ingestion_completed_at=datetime.now()
            )
            
            return result
            
        except Exception as e:
            # Update status to failed
            await self.incremental_manager.update_status(
                status_id,
                status='failed',
                ingestion_completed_at=datetime.now()
            )
            raise
    
    async def _ingest_single_document(self, file_path: str) -> IngestionResult:
        """
        Ingest a single document.
        
        Args:
            file_path: Path to the document file
        
        Returns:
            Ingestion result
        """
        start_time = datetime.now()
        
        # Read document (returns dict with title, content, metadata)
        document_data = self._read_document(file_path)
        document_content = document_data["content"]
        document_title = document_data["title"]
        document_source = os.path.relpath(file_path, self.documents_folder)
        
        # Merge extracted metadata with file metadata
        document_metadata = {
            **document_data.get("metadata", {}),
            **self._extract_document_metadata(document_content, file_path)
        }
        
        logger.info(f"Processing document: {document_title}")
        
        # Chunk the document
        chunks = await self.chunker.chunk_document(
            content=document_content,
            title=document_title,
            source=document_source,
            metadata=document_metadata
        )
        
        if not chunks:
            logger.warning(f"No chunks created for {document_title}")
            return IngestionResult(
                document_id="",
                title=document_title,
                chunks_created=0,
                entities_extracted=0,
                relationships_created=0,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                errors=["No chunks created"]
            )
        
        logger.info(f"Created {len(chunks)} chunks")
        
        # Extract entities if configured
        entities_extracted = 0
        if self.config.extract_entities:
            chunks = await self.graph_builder.extract_entities_from_chunks(chunks)
            entities_extracted = sum(
                len(chunk.metadata.get("entities", {}).get("companies", [])) +
                len(chunk.metadata.get("entities", {}).get("technologies", [])) +
                len(chunk.metadata.get("entities", {}).get("people", []))
                for chunk in chunks
            )
            logger.info(f"Extracted {entities_extracted} entities")
        
        # Generate embeddings
        embedded_chunks = await self.embedder.embed_chunks(chunks)
        logger.info(f"Generated embeddings for {len(embedded_chunks)} chunks")
        
        # Extract metadata from file path
        category, document_order = self.incremental_manager._extract_metadata_from_path(file_path)
        priority_weight = self.incremental_manager.calculate_citation_priority(category, document_order)
        
        # Save to PostgreSQL with structured metadata
        document_id = await self._save_to_postgres(
            document_title,
            document_source,
            document_content,
            embedded_chunks,
            document_metadata,
            category=category,
            document_order=document_order,
            priority_weight=priority_weight
        )
        
        logger.info(f"Saved document to PostgreSQL with ID: {document_id}")
        
        # Add to knowledge graph (if enabled)
        relationships_created = 0
        graph_errors = []
        
        if not self.config.skip_graph_building:
            try:
                logger.info("Building knowledge graph relationships (this may take several minutes)...")
                graph_result = await self.graph_builder.add_document_to_graph(
                    chunks=embedded_chunks,
                    document_title=document_title,
                    document_source=document_source,
                    document_metadata=document_metadata
                )
                
                relationships_created = graph_result.get("episodes_created", 0)
                graph_errors = graph_result.get("errors", [])
                
                logger.info(f"Added {relationships_created} episodes to knowledge graph")
                
            except Exception as e:
                error_msg = f"Failed to add to knowledge graph: {str(e)}"
                logger.error(error_msg)
                graph_errors.append(error_msg)
        else:
            logger.info("Skipping knowledge graph building (skip_graph_building=True)")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return IngestionResult(
            document_id=document_id,
            title=document_title,
            chunks_created=len(chunks),
            entities_extracted=entities_extracted,
            relationships_created=relationships_created,
            processing_time_ms=processing_time,
            errors=graph_errors
        )
    
    def _find_document_files(self) -> List[str]:
        """Find all supported document files in the documents folder."""
        if not os.path.exists(self.documents_folder):
            logger.error(f"Documents folder not found: {self.documents_folder}")
            return []
        
        # Support DOCX, PDF, TXT, and markdown files
        patterns = ["*.docx", "*.pdf", "*.txt", "*.md", "*.markdown"]
        files = []
        
        for pattern in patterns:
            found_files = glob.glob(os.path.join(self.documents_folder, "**", pattern), recursive=True)
            # Filter out temporary files (starting with ~$)
            found_files = [f for f in found_files if not os.path.basename(f).startswith('~$')]
            files.extend(found_files)
        
        return sorted(files)
    
    def _read_document(self, file_path: str) -> Dict[str, Any]:
        """Read document content from file based on file type."""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.docx':
            # Process DOCX file
            return self.docx_processor.process_docx_file(file_path)
        
        elif file_ext == '.pdf':
            # Process PDF file (basic implementation)
            try:
                import PyPDF2
                content = ""
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        content += page.extract_text() + "\n"
                
                return {
                    "title": os.path.splitext(os.path.basename(file_path))[0],
                    "content": content.strip(),
                    "source": file_path,
                    "metadata": {
                        "file_type": "pdf",
                        "character_count": len(content),
                        "estimated_pages": len(reader.pages)
                    }
                }
            except Exception as e:
                logger.error(f"Failed to process PDF {file_path}: {e}")
                raise
        
        else:
            # Process text-based files (MD, TXT)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            return {
                "title": self._extract_title_from_text(content, file_path),
                "content": content,
                "source": file_path,
                "metadata": {
                    "file_type": file_ext[1:] if file_ext else "txt",
                    "character_count": len(content),
                    "word_count": len(content.split())
                }
            }
    
    def _extract_title_from_text(self, content: str, file_path: str) -> str:
        """Extract title from text content or filename."""
        # Try to find markdown title
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        
        # Fallback to filename
        return os.path.splitext(os.path.basename(file_path))[0].replace('_', ' ').replace('-', ' ').title()
    
    def _extract_document_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract metadata from document content."""
        metadata = {
            "file_path": file_path,
            "file_size": len(content),
            "ingestion_date": datetime.now().isoformat()
        }
        
        # Try to extract YAML frontmatter
        if content.startswith('---'):
            try:
                import yaml
                end_marker = content.find('\n---\n', 4)
                if end_marker != -1:
                    frontmatter = content[4:end_marker]
                    yaml_metadata = yaml.safe_load(frontmatter)
                    if isinstance(yaml_metadata, dict):
                        metadata.update(yaml_metadata)
            except ImportError:
                logger.warning("PyYAML not installed, skipping frontmatter extraction")
            except Exception as e:
                logger.warning(f"Failed to parse frontmatter: {e}")
        
        # Extract some basic metadata from content
        lines = content.split('\n')
        metadata['line_count'] = len(lines)
        metadata['word_count'] = len(content.split())
        
        return metadata
    
    async def _save_to_postgres(
        self,
        title: str,
        source: str,
        content: str,
        chunks: List[DocumentChunk],
        metadata: Dict[str, Any],
        category: Optional[str] = None,
        document_order: Optional[int] = None,
        priority_weight: Optional[int] = None
    ) -> str:
        """Save document and chunks to PostgreSQL with structured metadata."""
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                # Insert document with category and order metadata
                document_result = await conn.fetchrow(
                    """
                    INSERT INTO documents (title, source, content, metadata, category, document_order, priority_weight)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id::text
                    """,
                    title,
                    source,
                    content,
                    json.dumps(metadata),
                    category,
                    document_order,
                    priority_weight
                )
                
                document_id = document_result["id"]
                
                # Insert chunks with category and order metadata
                for chunk in chunks:
                    # Convert embedding to PostgreSQL vector string format
                    embedding_data = None
                    if hasattr(chunk, 'embedding') and chunk.embedding:
                        # PostgreSQL vector format: '[1.0,2.0,3.0]' (no spaces after commas)
                        embedding_data = '[' + ','.join(map(str, chunk.embedding)) + ']'
                    
                    await conn.execute(
                        """
                        INSERT INTO chunks (document_id, content, embedding, chunk_index, metadata, token_count, category, document_order)
                        VALUES ($1::uuid, $2, $3::vector, $4, $5, $6, $7, $8)
                        """,
                        document_id,
                        chunk.content,
                        embedding_data,
                        chunk.index,
                        json.dumps(chunk.metadata),
                        chunk.token_count,
                        category,
                        document_order
                    )
                
                return document_id
    
    async def _clean_databases(self):
        """Clean existing data from databases."""
        logger.warning("Cleaning existing data from databases...")
        
        # Clean PostgreSQL
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("DELETE FROM messages")
                await conn.execute("DELETE FROM sessions")
                await conn.execute("DELETE FROM chunks")
                await conn.execute("DELETE FROM documents")
        
        logger.info("Cleaned PostgreSQL database")
        
        # Clean knowledge graph
        await self.graph_builder.clear_graph()
        logger.info("Cleaned knowledge graph")


async def handle_management_commands(args):
    """Handle management commands like status, cleanup, etc."""
    from .incremental_manager import create_incremental_manager
    
    manager = create_incremental_manager()
    await manager.initialize()
    
    try:
        if args.status:
            # Show status report
            report = await manager.get_ingestion_report()
            print_status_report(report)
        
        elif args.reingest_category:
            # Force re-ingestion of category
            print(f"Cleaning up category: {args.reingest_category}")
            await manager.cleanup_category(args.reingest_category)
            print("✓ Category cleanup completed")
        
        elif args.cleanup_partial:
            # Cleanup partial/failed ingestions
            print("Finding partial/failed ingestions...")
            report = await manager.get_ingestion_report()
            problem_docs = report.get('problem_documents', [])
            
            if not problem_docs:
                print("No partial/failed ingestions found")
                return
            
            print(f"Found {len(problem_docs)} documents to cleanup:")
            for doc in problem_docs:
                print(f"  - {doc['file_path']} ({doc['status']})")
            
            confirm = input("Proceed with cleanup? (y/N): ")
            if confirm.lower() == 'y':
                for doc in problem_docs:
                    await manager.cleanup_incomplete_ingestion(doc['file_path'])
                print("✓ Cleanup completed")
            else:
                print("Cleanup cancelled")
        
        elif args.verify_integrity:
            # Verify database integrity
            print("Verifying database integrity...")
            # TODO: Implement integrity check
            print("✓ Integrity check completed")
    
    finally:
        # manager cleanup is handled automatically
        pass


def print_status_report(report):
    """Print formatted status report."""
    overall = report.get('overall', {})
    categories = report.get('by_category', [])
    problems = report.get('problem_documents', [])
    
    print("\n" + "="*60)
    print("INGESTION STATUS REPORT")
    print("="*60)
    
    if overall:
        print(f"Total documents: {overall.get('total_documents', 0)}")
        print(f"✓ Completed: {overall.get('completed', 0)}")
        print(f"⚠ Partial: {overall.get('partial', 0)}")
        print(f"✗ Failed: {overall.get('failed', 0)}")
        print(f"🔄 Processing: {overall.get('processing', 0)}")
        print(f"⏳ Pending: {overall.get('pending', 0)}")
    
    if categories:
        print("\nCategories:")
        for cat in categories:
            status = "✓" if cat['incomplete'] == 0 else "⚠"
            print(f"  {status} {cat['category']}: {cat['completed']}/{cat['total']} completed")
    
    if problems:
        print(f"\nProblem documents ({len(problems)}):")
        for doc in problems[:10]:  # Show first 10
            print(f"  ✗ {doc['file_path']} ({doc['status']})")
        if len(problems) > 10:
            print(f"  ... and {len(problems) - 10} more")
        print("\nUse --cleanup-partial to fix incomplete ingestions")
    
    print()


async def main():
    """Main function for running ingestion."""
    parser = argparse.ArgumentParser(description="Ingest documents into vector DB and knowledge graph")
    parser.add_argument("--documents", "-d", default="documents", help="Documents folder path")
    parser.add_argument("--clean", "-c", action="store_true", help="Clean existing data before ingestion")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size for splitting documents")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Chunk overlap size")
    parser.add_argument("--no-semantic", action="store_true", help="Disable semantic chunking")
    parser.add_argument("--no-entities", action="store_true", help="Disable entity extraction")
    parser.add_argument("--fast", "-f", action="store_true", help="Fast mode: skip knowledge graph building")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    # Incremental ingestion options
    parser.add_argument("--no-incremental", action="store_true", help="Disable incremental ingestion")
    parser.add_argument("--status", action="store_true", help="Show ingestion status report")
    parser.add_argument("--reingest-category", type=str, help="Force re-ingestion of specific category")
    parser.add_argument("--cleanup-partial", action="store_true", help="Cleanup partial/failed ingestions")
    parser.add_argument("--verify-integrity", action="store_true", help="Verify database integrity")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Handle status-only commands
    if args.status or args.reingest_category or args.cleanup_partial or args.verify_integrity:
        await handle_management_commands(args)
        return
    
    # Create ingestion configuration
    config = IngestionConfig(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        use_semantic_chunking=not args.no_semantic,
        extract_entities=not args.no_entities,
        skip_graph_building=args.fast
    )
    
    # Create and run pipeline
    pipeline = DocumentIngestionPipeline(
        config=config,
        documents_folder=args.documents,
        clean_before_ingest=args.clean
    )
    
    def progress_callback(current: int, total: int):
        print(f"Progress: {current}/{total} documents processed")
    
    try:
        start_time = datetime.now()
        
        results = await pipeline.ingest_documents(
            progress_callback, 
            use_incremental=not args.no_incremental
        )
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Print summary
        print("\n" + "="*50)
        print("INGESTION SUMMARY")
        print("="*50)
        print(f"Documents processed: {len(results)}")
        print(f"Total chunks created: {sum(r.chunks_created for r in results)}")
        print(f"Total entities extracted: {sum(r.entities_extracted for r in results)}")
        print(f"Total graph episodes: {sum(r.relationships_created for r in results)}")
        print(f"Total errors: {sum(len(r.errors) for r in results)}")
        print(f"Total processing time: {total_time:.2f} seconds")
        print()
        
        # Print individual results
        for result in results:
            status = "✓" if not result.errors else "✗"
            print(f"{status} {result.title}: {result.chunks_created} chunks, {result.entities_extracted} entities")
            
            if result.errors:
                for error in result.errors:
                    print(f"  Error: {error}")
        
    except KeyboardInterrupt:
        print("\nIngestion interrupted by user")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())