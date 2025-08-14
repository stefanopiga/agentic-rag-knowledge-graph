"""
Streaming DOCX processor per file grandi.
Elaborazione paragrafo per paragrafo per ottimizzare memoria e timeout.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Iterator, Tuple
from pathlib import Path
import re
import time
from dataclasses import dataclass

from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table

logger = logging.getLogger(__name__)


@dataclass
class DocumentSection:
    """Sezione di documento per elaborazione streaming."""
    content: str
    section_type: str  # paragraph, table, heading
    position: int
    metadata: Dict[str, Any]


class StreamingDOCXProcessor:
    """Processore DOCX ottimizzato per file grandi con elaborazione streaming."""
    
    def __init__(self, 
                 max_section_size: int = 2000,
                 compression_enabled: bool = True,
                 timeout_per_section: int = 30):
        """
        Initialize streaming processor.
        
        Args:
            max_section_size: Dimensione massima sezione (caratteri)
            compression_enabled: Abilita compressione pre-elaborazione
            timeout_per_section: Timeout per sezione (secondi)
        """
        self.max_section_size = max_section_size
        self.compression_enabled = compression_enabled
        self.timeout_per_section = timeout_per_section
    
    def process_docx_streaming(self, file_path: str) -> Iterator[DocumentSection]:
        """
        Process DOCX file with streaming approach.
        
        Args:
            file_path: Path to DOCX file
            
        Yields:
            DocumentSection objects for progressive processing
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DOCX file not found: {file_path}")
        
        logger.info(f"🔄 Streaming processing DOCX: {file_path}")
        
        try:
            doc = Document(file_path)
            file_metadata = self._extract_file_metadata(doc, file_path)
            
            position = 0
            section_count = 0
            
            # Process document elements one by one
            for element in doc.element.body:
                start_time = time.time()
                
                try:
                    section = self._process_element(element, position, file_metadata)
                    
                    if section and section.content.strip():
                        # Apply compression if enabled
                        if self.compression_enabled:
                            section.content = self._compress_content(section.content)
                        
                        # Skip if still too large after compression
                        if len(section.content) > self.max_section_size:
                            logger.warning(f"Section {position} too large ({len(section.content)} chars), splitting...")
                            yield from self._split_large_section(section)
                        else:
                            yield section
                        
                        section_count += 1
                        position += len(section.content)
                    
                    # Check timeout per section
                    elapsed = time.time() - start_time
                    if elapsed > self.timeout_per_section:
                        logger.warning(f"Section processing timeout ({elapsed:.1f}s), continuing...")
                    
                except Exception as e:
                    logger.warning(f"Failed to process element at position {position}: {e}")
                    continue
            
            logger.info(f"✅ Streaming completed: {section_count} sections, {position} total chars")
            
        except Exception as e:
            logger.error(f"Streaming processing failed for {file_path}: {e}")
            raise
    
    def _process_element(self, element, position: int, file_metadata: Dict) -> Optional[DocumentSection]:
        """Process single document element."""
        
        # Handle paragraphs
        if element.tag.endswith('p'):
            paragraph = Paragraph(element, None)
            content = paragraph.text.strip()
            
            if content:
                section_type = "heading" if self._is_heading(paragraph) else "paragraph"
                
                return DocumentSection(
                    content=content,
                    section_type=section_type,
                    position=position,
                    metadata={
                        **file_metadata,
                        "section_type": section_type,
                        "position": position,
                        "length": len(content)
                    }
                )
        
        # Handle tables
        elif element.tag.endswith('tbl'):
            table = Table(element, None)
            content = self._extract_table_content(table)
            
            if content:
                return DocumentSection(
                    content=content,
                    section_type="table",
                    position=position,
                    metadata={
                        **file_metadata,
                        "section_type": "table",
                        "position": position,
                        "length": len(content)
                    }
                )
        
        return None
    
    def _compress_content(self, content: str) -> str:
        """
        Compress content removing redundant formatting and whitespace.
        
        Args:
            content: Original content
            
        Returns:
            Compressed content
        """
        if not self.compression_enabled:
            return content
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove repeated punctuation
        content = re.sub(r'[.]{3,}', '...', content)
        content = re.sub(r'[-]{3,}', '---', content)
        
        # Remove empty parentheses/brackets
        content = re.sub(r'\(\s*\)', '', content)
        content = re.sub(r'\[\s*\]', '', content)
        
        # Compress medical abbreviations (preserve meaning)
        medical_expansions = {
            r'\b(Art|Artic|Articol)\b': 'Articolazione',
            r'\b(Musc|Muscol)\b': 'Muscolo', 
            r'\b(Lig|Ligam)\b': 'Legamento',
            r'\b(Tend|Tendin)\b': 'Tendine'
        }
        
        for pattern, replacement in medical_expansions.items():
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        return content.strip()
    
    def _split_large_section(self, section: DocumentSection) -> Iterator[DocumentSection]:
        """Split large section into smaller pieces."""
        content = section.content
        max_size = self.max_section_size
        
        # Try to split on sentences first
        sentences = re.split(r'[.!?]+\s+', content)
        
        current_chunk = ""
        chunk_count = 0
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    yield DocumentSection(
                        content=current_chunk.strip(),
                        section_type=f"{section.section_type}_split",
                        position=section.position + chunk_count * max_size,
                        metadata={
                            **section.metadata,
                            "split_part": chunk_count,
                            "is_split": True
                        }
                    )
                    chunk_count += 1
                
                current_chunk = sentence + ". "
        
        # Add final chunk
        if current_chunk:
            yield DocumentSection(
                content=current_chunk.strip(),
                section_type=f"{section.section_type}_split",
                position=section.position + chunk_count * max_size,
                metadata={
                    **section.metadata,
                    "split_part": chunk_count,
                    "is_split": True
                }
            )
    
    def _extract_file_metadata(self, doc: Document, file_path: str) -> Dict[str, Any]:
        """Extract basic file metadata."""
        file_size = os.path.getsize(file_path)
        
        return {
            "file_path": file_path,
            "file_type": "docx",
            "file_size": file_size,
            "file_name": Path(file_path).name,
            "processing_mode": "streaming",
            "compression_enabled": self.compression_enabled
        }
    
    def _is_heading(self, paragraph: Paragraph) -> bool:
        """Check if paragraph is a heading."""
        if hasattr(paragraph.style, 'name'):
            style_name = paragraph.style.name.lower()
            return ('heading' in style_name or 
                   'title' in style_name or
                   paragraph.text.isupper())
        return False
    
    def _extract_table_content(self, table: Table) -> str:
        """Extract content from table."""
        content_parts = []
        
        for row in table.rows:
            row_content = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                if cell_text:
                    row_content.append(cell_text)
            
            if row_content:
                content_parts.append(" | ".join(row_content))
        
        return "\n".join(content_parts)


def create_streaming_docx_processor() -> StreamingDOCXProcessor:
    """Create streaming DOCX processor with optimized settings."""
    return StreamingDOCXProcessor(
        max_section_size=2000,      # Sezioni più piccole
        compression_enabled=True,    # Compressione attiva
        timeout_per_section=30      # Timeout per sezione
    )