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
from uuid import UUID

import asyncpg
from dotenv import load_dotenv

from .chunker import ChunkingConfig, create_chunker, DocumentChunk
from .embedder import create_embedder
from .graph_builder import create_graph_builder
from .docx_processor import create_docx_processor
from .incremental_manager import create_incremental_manager, IngestionAction

try:
    from agent.db_utils import initialize_database, close_database, db_pool
    from agent.graph_utils import initialize_graph, close_graph
    from agent.models import IngestionConfig, IngestionResult
except (ImportError, ValueError):
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent.db_utils import initialize_database, close_database, db_pool
    from agent.graph_utils import initialize_graph, close_graph
    from agent.models import IngestionConfig, IngestionResult

load_dotenv()
logger = logging.getLogger(__name__)


class DocumentIngestionPipeline:
    """Pipeline for ingesting documents into vector DB and knowledge graph."""
    
    def __init__(self, config: IngestionConfig, documents_folder: str = "documents", clean_before_ingest: bool = False, use_streaming: bool = True):
        self.config = config
        self.documents_folder = documents_folder
        self.clean_before_ingest = clean_before_ingest
        self.chunker = create_chunker(ChunkingConfig(chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap, use_semantic_splitting=config.use_semantic_chunking))
        self.embedder = create_embedder()
        self.graph_builder = create_graph_builder()
        self.docx_processor = create_docx_processor()
        self.incremental_manager = create_incremental_manager()
        self._initialized = False

    async def initialize(self):
        if not self._initialized:
            await initialize_database()
            await self.graph_builder.initialize()
            await self.incremental_manager.initialize()
            self._initialized = True

    async def close(self):
        if self._initialized:
            await self.graph_builder.close()
            await close_database()
            self._initialized = False

    async def ingest_documents(self, use_incremental: bool = True, tenant_slug: str = 'default') -> List[IngestionResult]:
        if not self._initialized:
            await self.initialize()

        tenant_id = await self._get_tenant_id_from_slug(tenant_slug)

        if self.clean_before_ingest:
            await self._clean_databases()
            # Se puliamo tutto, forziamo la re-ingestione di tutto.
            # La logica incrementale gestirà questo come "INGEST" per ogni file.

        results = []
        scanned_documents = await self.incremental_manager.scan_documents(self.documents_folder, tenant_id)

        for doc in scanned_documents:
            action = doc.action
            file_path = doc.file_path

            if action == IngestionAction.SKIP:
                logger.info(f"Skipping {file_path}: {doc.reason}")
                continue

            status_id = await self.incremental_manager.create_or_update_status(
                file_path=file_path,
                file_hash=doc.current_hash,
                file_size=doc.file_size,
                last_modified=doc.last_modified,
                category=doc.category,
                document_order=doc.document_order,
                tenant_id=tenant_id,
                status='processing'
            )

            try:
                if action == IngestionAction.CLEANUP_AND_REINGEST:
                    logger.info(f"Cleaning up before re-ingesting {file_path}")
                    await self.incremental_manager.cleanup_incomplete_ingestion(file_path)

                result = await self._ingest_single_document(file_path, tenant_id)
                results.append(result)

                if result.success:
                    await self.incremental_manager.update_status(status_id, status='completed', chunks_created=result.chunks_created, graph_episodes_created=result.relationships_created)
                else:
                    await self.incremental_manager.update_status(status_id, status='failed')

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}", exc_info=True)
                await self.incremental_manager.update_status(status_id, status='failed')
                results.append(IngestionResult(
                    document_id="",
                    title=os.path.basename(file_path),
                    success=False,
                    chunks_created=0,
                    entities_extracted=0,
                    relationships_created=0,
                    processing_time_ms=0,
                    errors=[str(e)]
                ))

        return results

    async def _ingest_single_document(self, file_path: str, tenant_id: UUID) -> IngestionResult:
        start_time = datetime.now()
        document_data = self._read_document(file_path)
        
        chunks = await self.chunker.chunk_document(
            content=document_data["content"],
            title=document_data["title"],
            source=os.path.relpath(file_path, self.documents_folder)
        )
        
        if not chunks:
            return IngestionResult(
                document_id="", 
                title=document_data["title"], 
                success=False,
                chunks_created=0,
                entities_extracted=0,
                relationships_created=0,
                processing_time_ms=0,
                errors=["No chunks created"]
            )

        embedded_chunks = await self.embedder.embed_chunks(chunks)
        
        document_id = await self._save_to_postgres(
            document_data["title"],
            os.path.relpath(file_path, self.documents_folder),
            document_data["content"],
            embedded_chunks,
            document_data.get("metadata", {}),
            tenant_id
        )

        graph_result = {"episodes_created": 0, "errors": []}
        if not self.config.skip_graph_building:
            graph_result = await self.graph_builder.add_document_to_graph(
                chunks=embedded_chunks,
                document_title=document_data["title"],
                document_source=os.path.relpath(file_path, self.documents_folder),
                tenant_id=tenant_id
            )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        return IngestionResult(
            document_id=str(document_id),
            title=document_data["title"],
            success=True,
            chunks_created=len(chunks),
            entities_extracted=0, # Placeholder
            relationships_created=graph_result.get("episodes_created", 0),
            processing_time_ms=processing_time,
            errors=graph_result.get("errors", [])
        )



    def _read_document(self, file_path: str) -> Dict[str, Any]:
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == '.docx':
            return self.docx_processor.process_docx_file(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return {"title": os.path.splitext(os.path.basename(file_path))[0], "content": content}

    async def _get_tenant_id_from_slug(self, slug: str) -> UUID:
        async with db_pool.acquire() as conn:
            tenant = await conn.fetchrow("SELECT id FROM accounts_tenant WHERE slug = $1", slug)
            if tenant:
                return tenant['id']
            raise ValueError(f"Tenant with slug '{slug}' not found.")

    async def _save_to_postgres(self, title: str, source: str, content: str, chunks: List[DocumentChunk], metadata: Dict[str, Any], tenant_id: UUID) -> UUID:
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                document_result = await conn.fetchrow(
                    "INSERT INTO documents (tenant_id, title, source, content, metadata) VALUES ($1, $2, $3, $4, $5) RETURNING id",
                    tenant_id, title, source, content, json.dumps(metadata)
                )
                document_id = document_result["id"]
                for chunk in chunks:
                    embedding_data = '[' + ','.join(map(str, chunk.embedding)) + ']' if hasattr(chunk, 'embedding') and chunk.embedding else None
                    await conn.execute(
                        "INSERT INTO chunks (tenant_id, document_id, content, embedding, chunk_index, metadata) VALUES ($1, $2, $3, $4::vector, $5, $6)",
                        tenant_id, document_id, chunk.content, embedding_data, chunk.index, json.dumps(chunk.metadata)
                    )
                return document_id

    async def _clean_databases(self):
        logger.warning("Cleaning existing data from databases...")
        async with db_pool.acquire() as conn:
            await conn.execute("TRUNCATE TABLE documents, chunks, rag_engine_chatmessage, rag_engine_chatsession RESTART IDENTITY CASCADE")
        await self.graph_builder.clear_graph()
        logger.info("Databases cleaned.")

async def main():
    parser = argparse.ArgumentParser(description="Ingest documents.")
    parser.add_argument("--clean", action="store_true", help="Clean existing data.")
    parser.add_argument("--documents-dir", type=str, default="documents", help="Directory containing documents to ingest.")
    parser.add_argument("--tenant-slug", type=str, default="default", help="Slug of the tenant to ingest documents for.")
    args = parser.parse_args()
    
    config = IngestionConfig()
    pipeline = DocumentIngestionPipeline(config=config, documents_folder=args.documents_dir, clean_before_ingest=args.clean)
    await pipeline.ingest_documents(tenant_slug=args.tenant_slug)
    await pipeline.close()

if __name__ == "__main__":
    asyncio.run(main())
