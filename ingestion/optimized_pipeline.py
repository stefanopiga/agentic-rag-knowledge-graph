"""
Pipeline ottimizzata per gestione file grandi con elaborazione progressiva.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .streaming_docx_processor import StreamingDOCXProcessor, DocumentSection
from .chunker import DocumentChunk, ChunkingConfig
from .section_recovery_manager import create_section_recovery_manager

logger = logging.getLogger(__name__)


class OptimizedIngestionPipeline:
    """Pipeline ottimizzata per file grandi con processing intelligente."""
    
    def __init__(self, 
                 streaming_processor: StreamingDOCXProcessor,
                 chunker,
                 embedder,
                 graph_builder,
                 streaming_threshold: int = 5 * 1024 * 1024):  # 5MB
        """
        Initialize optimized pipeline.
        
        Args:
            streaming_threshold: Soglia dimensione file per streaming (bytes)
        """
        self.streaming_processor = streaming_processor
        self.chunker = chunker
        self.embedder = embedder
        self.graph_builder = graph_builder
        self.streaming_threshold = streaming_threshold
        self.section_recovery = create_section_recovery_manager()
    
    async def process_large_document(self, file_path: str, document_status_id: int) -> Dict[str, Any]:
        """
        Process large document with streaming approach.
        
        Args:
            file_path: Path to document
            
        Returns:
            Processing results
        """
        file_size = os.path.getsize(file_path)
        use_streaming = file_size > self.streaming_threshold
        
        logger.info(f"📄 Processing {Path(file_path).name}: {file_size/1024/1024:.1f}MB")
        logger.info(f"🔄 Mode: {'Streaming' if use_streaming else 'Standard'}")
        
        # Initialize section recovery manager
        await self.section_recovery.initialize()
        
        if use_streaming:
            return await self._process_streaming(file_path, document_status_id)
        else:
            return await self._process_standard(file_path, document_status_id)
    
    async def _process_streaming(self, file_path: str, document_status_id: int) -> Dict[str, Any]:
        """Process document with streaming approach."""
        
        total_chunks = 0
        total_entities = 0
        total_episodes = 0
        errors = []
        processed_sections = 0
        
        try:
            # Process document sections progressively with granular tracking
            for section in self.streaming_processor.process_docx_streaming(file_path):
                processed_sections += 1
                
                # Track section for recovery
                section_id = await self.section_recovery.track_section(
                    document_status_id=document_status_id,
                    section_position=section.position,
                    section_type=section.section_type,
                    content=section.content,
                    metadata=section.metadata
                )
                
                try:
                    # Update section status to processing
                    await self.section_recovery.update_section_status(section_id, 'processing')
                    
                    # Create chunks from section
                    section_chunks = await self._create_section_chunks(section)
                    
                    if section_chunks:
                        # Process chunks batch by batch
                        batch_results = await self._process_chunks_batch(
                            section_chunks, 
                            f"{Path(file_path).stem}_section_{processed_sections}"
                        )
                        
                        # Update section status to completed
                        await self.section_recovery.update_section_status(
                            section_id, 
                            'completed',
                            chunks_created=batch_results.get('chunks_created', 0),
                            entities_extracted=batch_results.get('entities_extracted', 0),
                            graph_episodes_created=batch_results.get('episodes_created', 0)
                        )
                        
                        total_chunks += batch_results.get('chunks_created', 0)
                        total_entities += batch_results.get('entities_extracted', 0)
                        total_episodes += batch_results.get('episodes_created', 0)
                        
                        if batch_results.get('errors'):
                            errors.extend(batch_results['errors'])
                    
                    # Log progress every 10 sections
                    if processed_sections % 10 == 0:
                        logger.info(f"📊 Progress: {processed_sections} sections, {total_chunks} chunks created")
                
                except Exception as e:
                    error_msg = f"Section {processed_sections} failed: {str(e)}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    
                    # Update section status to failed with error message
                    await self.section_recovery.update_section_status(
                        section_id, 
                        'failed',
                        error_message=error_msg
                    )
                    continue  # Continue with next section
            
            logger.info(f"✅ Streaming completed: {processed_sections} sections processed")
            
            return {
                'success': True,
                'chunks_created': total_chunks,
                'entities_extracted': total_entities,
                'episodes_created': total_episodes,
                'sections_processed': processed_sections,
                'errors': errors
            }
        
        except Exception as e:
            logger.error(f"Streaming processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'chunks_created': total_chunks,
                'sections_processed': processed_sections,
                'errors': errors + [str(e)]
            }
    
    async def _create_section_chunks(self, section: DocumentSection) -> List[DocumentChunk]:
        """Create chunks from document section."""
        
        try:
            # Use chunker to create chunks from section
            chunks = await self.chunker.chunk_document(
                content=section.content,
                title=f"Section_{section.position}",
                source=section.metadata.get('file_path', 'unknown'),
                metadata=section.metadata
            )
            
            return chunks
        
        except Exception as e:
            logger.warning(f"Failed to chunk section at position {section.position}: {e}")
            return []
    
    async def _process_chunks_batch(self, chunks: List[DocumentChunk], batch_name: str) -> Dict[str, Any]:
        """Process batch of chunks."""
        
        try:
            # Generate embeddings
            embeddings_created = 0
            for chunk in chunks:
                try:
                    # Generate embedding for chunk
                    embedding = await self.embedder.generate_embedding(chunk.content)
                    chunk.embedding = embedding
                    embeddings_created += 1
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for chunk: {e}")
            
            # Add to knowledge graph (if enabled)
            episodes_created = 0
            if hasattr(self.graph_builder, 'add_chunks_to_graph'):
                try:
                    graph_result = await self.graph_builder.add_chunks_to_graph(chunks)
                    episodes_created = graph_result.get('episodes_created', 0)
                except Exception as e:
                    logger.warning(f"Failed to add chunks to graph: {e}")
            
            return {
                'chunks_created': len(chunks),
                'embeddings_created': embeddings_created,
                'episodes_created': episodes_created,
                'errors': []
            }
        
        except Exception as e:
            return {
                'chunks_created': 0,
                'embeddings_created': 0,
                'episodes_created': 0,
                'errors': [str(e)]
            }
    
    async def _process_standard(self, file_path: str) -> Dict[str, Any]:
        """Process document with standard approach for smaller files."""
        # Implement standard processing here
        # This would use the existing docx_processor approach
        return {
            'success': True,
            'chunks_created': 0,
            'entities_extracted': 0,
            'episodes_created': 0,
            'mode': 'standard'
        }


def create_optimized_pipeline(streaming_processor, chunker, embedder, graph_builder) -> OptimizedIngestionPipeline:
    """Create optimized pipeline."""
    return OptimizedIngestionPipeline(
        streaming_processor=streaming_processor,
        chunker=chunker, 
        embedder=embedder,
        graph_builder=graph_builder,
        streaming_threshold=5 * 1024 * 1024  # 5MB
    )