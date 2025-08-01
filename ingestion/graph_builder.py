"""
Knowledge graph builder for extracting entities and relationships.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timezone
import asyncio
import re

from graphiti_core import Graphiti
from dotenv import load_dotenv

from .chunker import DocumentChunk

# Import graph utilities
try:
    from ..agent.graph_utils import GraphitiClient
except ImportError:
    # For direct execution or testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent.graph_utils import GraphitiClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds knowledge graph from document chunks."""
    
    def __init__(self):
        """Initialize graph builder."""
        self.graph_client = GraphitiClient()
        self._initialized = False
    
    async def initialize(self):
        """Initialize graph client."""
        if not self._initialized:
            await self.graph_client.initialize()
            self._initialized = True
    
    async def close(self):
        """Close graph client."""
        if self._initialized:
            await self.graph_client.close()
            self._initialized = False
    
    async def add_document_to_graph(
        self,
        chunks: List[DocumentChunk],
        document_title: str,
        document_source: str,
        document_metadata: Optional[Dict[str, Any]] = None,
        batch_size: int = 3  # Reduced batch size for Graphiti
    ) -> Dict[str, Any]:
        """
        Add document chunks to the knowledge graph.
        
        Args:
            chunks: List of document chunks
            document_title: Title of the document
            document_source: Source of the document
            document_metadata: Additional metadata
            batch_size: Number of chunks to process in each batch
        
        Returns:
            Processing results
        """
        if not self._initialized:
            await self.initialize()
        
        if not chunks:
            return {"episodes_created": 0, "errors": []}
        
        logger.info(f"Adding {len(chunks)} chunks to knowledge graph for document: {document_title}")
        logger.info("⚠️ Large chunks will be truncated to avoid Graphiti token limits.")
        
        # Check for oversized chunks and warn
        oversized_chunks = [i for i, chunk in enumerate(chunks) if len(chunk.content) > 6000]
        if oversized_chunks:
            logger.warning(f"Found {len(oversized_chunks)} chunks over 6000 chars that will be truncated: {oversized_chunks}")
        
        episodes_created = 0
        errors = []
        
        # Process chunks one by one to avoid overwhelming Graphiti
        for i, chunk in enumerate(chunks):
            try:
                # Create episode ID
                episode_id = f"{document_source}_{chunk.index}_{datetime.now().timestamp()}"
                
                # Prepare episode content with size limits
                episode_content = self._prepare_episode_content(
                    chunk,
                    document_title,
                    document_metadata
                )
                
                # Create source description (shorter)
                source_description = f"Document: {document_title} (Chunk: {chunk.index})"
                
                # Add episode to graph
                await self.graph_client.add_episode(
                    episode_id=episode_id,
                    content=episode_content,
                    source=source_description,
                    timestamp=datetime.now(timezone.utc),
                    metadata={
                        "document_title": document_title,
                        "document_source": document_source,
                        "chunk_index": chunk.index,
                        "original_length": len(chunk.content),
                        "processed_length": len(episode_content)
                    }
                )
                
                episodes_created += 1
                logger.info(f"✓ Added episode {episode_id} to knowledge graph ({episodes_created}/{len(chunks)})")
                
                # Small delay between each episode to reduce API pressure
                if i < len(chunks) - 1:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                error_msg = f"Failed to add chunk {chunk.index} to graph: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                
                # Continue processing other chunks even if one fails
                continue
        
        result = {
            "episodes_created": episodes_created,
            "total_chunks": len(chunks),
            "errors": errors
        }
        
        logger.info(f"Graph building complete: {episodes_created} episodes created, {len(errors)} errors")
        return result
    
    def _prepare_episode_content(
        self,
        chunk: DocumentChunk,
        document_title: str,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Prepare episode content with minimal context to avoid token limits.
        
        Args:
            chunk: Document chunk
            document_title: Title of the document
            document_metadata: Additional metadata
        
        Returns:
            Formatted episode content (optimized for Graphiti)
        """
        # Limit chunk content to avoid Graphiti's 8192 token limit
        # Estimate ~4 chars per token, keep content under 6000 chars to leave room for processing
        max_content_length = 6000
        
        content = chunk.content
        if len(content) > max_content_length:
            # Truncate content but try to end at a sentence boundary
            truncated = content[:max_content_length]
            last_sentence_end = max(
                truncated.rfind('. '),
                truncated.rfind('! '),
                truncated.rfind('? ')
            )
            
            if last_sentence_end > max_content_length * 0.7:  # If we can keep 70% and end cleanly
                content = truncated[:last_sentence_end + 1] + " [TRUNCATED]"
            else:
                content = truncated + "... [TRUNCATED]"
            
            logger.warning(f"Truncated chunk {chunk.index} from {len(chunk.content)} to {len(content)} chars for Graphiti")
        
        # Add minimal context (just document title for now)
        if document_title and len(content) < max_content_length - 100:
            episode_content = f"[Doc: {document_title[:50]}]\n\n{content}"
        else:
            episode_content = content
        
        return episode_content
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count (4 chars per token)."""
        return len(text) // 4
    
    def _is_content_too_large(self, content: str, max_tokens: int = 7000) -> bool:
        """Check if content is too large for Graphiti processing."""
        return self._estimate_tokens(content) > max_tokens
    
    async def extract_entities_from_chunks(
        self,
        chunks: List[DocumentChunk],
        extract_anatomical: bool = True,
        extract_pathological: bool = True,
        extract_treatments: bool = True,
        extract_devices: bool = True
    ) -> List[DocumentChunk]:
        """
        Extract medical entities from chunks and add to metadata.
        
        Args:
            chunks: List of document chunks
            extract_anatomical: Whether to extract anatomical structures
            extract_pathological: Whether to extract pathological conditions
            extract_treatments: Whether to extract treatment procedures
            extract_devices: Whether to extract medical devices
        
        Returns:
            Chunks with medical entity metadata added
        """
        logger.info(f"Extracting medical entities from {len(chunks)} chunks")
        
        enriched_chunks = []
        
        for chunk in chunks:
            entities = {
                "anatomical_structures": [],
                "pathological_conditions": [],
                "treatment_procedures": [],
                "medical_devices": []
            }
            
            content = chunk.content
            
            # Extract anatomical structures
            if extract_anatomical:
                entities["anatomical_structures"] = self._extract_anatomical_structures(content)
            
            # Extract pathological conditions
            if extract_pathological:
                entities["pathological_conditions"] = self._extract_pathological_conditions(content)
            
            # Extract treatment procedures
            if extract_treatments:
                entities["treatment_procedures"] = self._extract_treatment_procedures(content)
            
            # Extract medical devices
            if extract_devices:
                entities["medical_devices"] = self._extract_medical_devices(content)
            
            # Create enriched chunk
            enriched_chunk = DocumentChunk(
                content=chunk.content,
                index=chunk.index,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                metadata={
                    **chunk.metadata,
                    "entities": entities,
                    "entity_extraction_date": datetime.now().isoformat()
                },
                token_count=chunk.token_count
            )
            
            # Preserve embedding if it exists
            if hasattr(chunk, 'embedding'):
                enriched_chunk.embedding = chunk.embedding
            
            enriched_chunks.append(enriched_chunk)
        
        logger.info("Entity extraction complete")
        return enriched_chunks
    
    def _extract_anatomical_structures(self, text: str) -> List[str]:
        """Extract anatomical structures from medical text."""
        anatomical_structures = {
            # Upper Limb
            "spalla", "gomito", "polso", "mano",
            
            # Lower Limb  
            "anca", "ginocchio", "caviglia", "piede",
            
            # Spine
            "colonna", "cervicale", "lombare", "toracica", "sacrale", "coccige",
            "vertebra", "vertebre",
            
            # Muscles
            "quadricipite", "bicipite", "tricipite", "deltoide", "trapezio",
            "dorsale", "pettorale", "glutei", "ischiocruali", "gastrocnemio",
            "soleo", "muscolo", "muscoli",
            
            # Bones
            "femore", "tibia", "fibula", "omero", "radio", "ulna",
            "scapola", "clavicola", "bacino", "costola", "sterno",
            "osso", "ossa",
            
            # Soft Tissues
            "legamento", "legamenti", "tendine", "tendini", "cartilagine",
            "menisco", "capsula", "fascia", "nervo", "nervi",
            "articolazione", "articolazioni"
        }
        
        found_structures = set()
        text_lower = text.lower()
        
        for structure in anatomical_structures:
            # Case-insensitive search with word boundaries
            pattern = r'\b' + re.escape(structure.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_structures.add(structure)
        
        return list(found_structures)
    
    def _extract_pathological_conditions(self, text: str) -> List[str]:
        """Extract pathological conditions from medical text."""
        pathological_conditions = {
            # Trauma
            "lesione", "lesioni", "trauma", "traumi", "strappo", "strappi",
            "distorsione", "distorsioni", "frattura", "fratture", 
            "lussazione", "lussazioni", "contusione", "contusioni",
            
            # Inflammatory
            "infiammazione", "infiammazioni", "tendinite", "tendiniti",
            "borsite", "borsiti", "artrite", "artriti", "sinovite", "sinoviti",
            "capsulite", "capsuliti",
            
            # Degenerative  
            "artrosi", "degenerazione", "degenerazioni", "usura",
            "deterioramento", "deterioramenti",
            
            # Symptoms
            "dolore", "dolori", "algia", "algie", "sindrome", "sindromi",
            "syndrome", "discomfort", "fastidio", "rigidità",
            "contrattura", "contratture", "spasmo", "spasmi",
            "edema", "gonfiore", "gonfiori", "instabilità",
            "debolezza", "atrofia", "atrofie", "ipertrofia", "ipertrofie",
            "fibrosi", "aderenza", "aderenze", "cicatrice", "cicatrici",
            "impingement"
        }
        
        found_conditions = set()
        text_lower = text.lower()
        
        for condition in pathological_conditions:
            # Case-insensitive search with word boundaries
            pattern = r'\b' + re.escape(condition.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_conditions.add(condition)
        
        return list(found_conditions)
    
    def _extract_treatment_procedures(self, text: str) -> List[str]:
        """Extract treatment procedures from medical text."""
        treatment_procedures = {
            # Manual Therapy
            "mobilizzazione", "mobilizzazioni", "manipolazione", "manipolazioni",
            "massaggio", "massaggi", "terapia manuale",
            
            # Exercise Therapy
            "esercizio", "esercizi", "rinforzo", "stretching", "allungamento",
            "allungamenti", "propriocezione", "coordinazione", "equilibrio",
            "stabilizzazione", "condizionamento", "conditioning",
            "allenamento", "addestramento",
            
            # Physical Agents
            "ultrasuoni", "laser", "tens", "elettrostimolazione",
            "crioterapia", "termoterapia", "magnetoterapia",
            "onde d'urto", "tecar",
            
            # Rehabilitation
            "riabilitazione", "fisioterapia", "chinesiologia", "kinesiterapia",
            "recupero", "trattamento", "trattamenti", "intervento", "interventi",
            "terapia", "terapie", "cura", "cure", "prevenzione",
            "educazione"
        }
        
        found_procedures = set()
        text_lower = text.lower()
        
        for procedure in treatment_procedures:
            # Case-insensitive search with word boundaries
            pattern = r'\b' + re.escape(procedure.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_procedures.add(procedure)
        
        return list(found_procedures)
    
    def _extract_medical_devices(self, text: str) -> List[str]:
        """Extract medical devices from medical text."""
        medical_devices = {
            # Furniture & Equipment
            "lettino", "lettini", "panca", "panche", "cyclette", "tapis roulant",
            "parallele", "pedana", "pedane", "tavoletta", "tavolette",
            
            # Assessment Tools
            "goniometro", "goniometri", "dinamometro", "dinamometri",
            "bilancia", "bilance", "test", "scala", "scale",
            "marker", "markers", "sensore", "sensori", "monitor", "monitors",
            "display",
            
            # Support Devices
            "tutore", "tutori", "bendaggio", "bendaggi", "ortesi",
            "plantare", "plantari", "supporto", "supporti", "bastone", "bastoni",
            "stampelle", "deambulatore", "deambulatori", "carrozzina", "carrozzine",
            
            # Technology
            "elettrodo", "elettrodi", "sonda", "sonde", "applicatore", "applicatori",
            "manipolo", "manipoli", "testina", "testine",
            
            # Therapeutic Materials
            "fascia", "fasce", "benda", "bende", "ghiaccio", "caldo",
            "compressione", "pesi", "peso", "elastico", "elastici",
            "pallone", "palloni", "specchio", "specchi"
        }
        
        found_devices = set()
        text_lower = text.lower()
        
        for device in medical_devices:
            # Case-insensitive search with word boundaries
            pattern = r'\b' + re.escape(device.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_devices.add(device)
        
        return list(found_devices)
    
    async def clear_graph(self):
        """Clear all data from the knowledge graph."""
        if not self._initialized:
            await self.initialize()
        
        logger.warning("Clearing knowledge graph...")
        await self.graph_client.clear_graph()
        logger.info("Knowledge graph cleared")


class SimpleMedicalEntityExtractor:
    """Simple rule-based medical entity extractor as fallback."""
    
    def __init__(self):
        """Initialize medical entity extractor."""
        self.anatomical_patterns = [
            r'\b(?:ginocchio|caviglia|piede|spalla|gomito|polso|mano|anca)\b',
            r'\b(?:colonna|vertebra|cervicale|lombare|toracica|sacrale)\b',
            r'\b(?:quadricipite|bicipite|tricipite|deltoide|trapezio|glutei)\b',
            r'\b(?:femore|tibia|fibula|omero|radio|ulna|scapola|clavicola)\b',
            r'\b(?:legamento|tendine|cartilagine|menisco|capsula|fascia|nervo)\b'
        ]
        
        self.pathological_patterns = [
            r'\b(?:lesione|trauma|strappo|distorsione|frattura|lussazione)\b',
            r'\b(?:infiammazione|tendinite|borsite|artrite|sinovite|capsulite)\b',
            r'\b(?:artrosi|degenerazione|usura|deterioramento)\b',
            r'\b(?:dolore|algia|sindrome|rigidità|contrattura|spasmo)\b',
            r'\b(?:edema|gonfiore|instabilità|debolezza|atrofia|fibrosi)\b'
        ]
        
        self.treatment_patterns = [
            r'\b(?:mobilizzazione|manipolazione|massaggio|terapia manuale)\b',
            r'\b(?:esercizio|rinforzo|stretching|allungamento|propriocezione)\b',
            r'\b(?:ultrasuoni|laser|tens|elettrostimolazione|crioterapia)\b',
            r'\b(?:riabilitazione|fisioterapia|chinesiologia|recupero)\b'
        ]
        
        self.device_patterns = [
            r'\b(?:tutore|bendaggio|ortesi|plantare|supporto|bastone)\b',
            r'\b(?:goniometro|dinamometro|elettrodo|sonda|applicatore)\b',
            r'\b(?:lettino|panca|cyclette|tapis roulant|pedana|tavoletta)\b'
        ]
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract medical entities using patterns."""
        entities = {
            "anatomical_structures": [],
            "pathological_conditions": [],
            "treatment_procedures": [],
            "medical_devices": []
        }
        
        # Extract anatomical structures
        for pattern in self.anatomical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["anatomical_structures"].extend(matches)
        
        # Extract pathological conditions
        for pattern in self.pathological_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["pathological_conditions"].extend(matches)
        
        # Extract treatment procedures
        for pattern in self.treatment_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["treatment_procedures"].extend(matches)
        
        # Extract medical devices
        for pattern in self.device_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["medical_devices"].extend(matches)
        
        # Remove duplicates and clean up
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities


# Factory function
def create_graph_builder() -> GraphBuilder:
    """Create graph builder instance."""
    return GraphBuilder()


# Example usage
async def main():
    """Example usage of the graph builder."""
    from .chunker import ChunkingConfig, create_chunker
    
    # Create chunker and graph builder
    config = ChunkingConfig(chunk_size=300, use_semantic_splitting=False)
    chunker = create_chunker(config)
    graph_builder = create_graph_builder()
    
    sample_text = """
    La distorsione di caviglia è una delle lesioni più comuni nell'ambito sportivo
    e può coinvolgere i legamenti laterali dell'articolazione. Il trattamento
    iniziale prevede l'applicazione di ghiaccio, il riposo e l'elevazione dell'arto.
    
    La riabilitazione deve includere esercizi di mobilizzazione precoce per
    mantenere il range di movimento, seguiti da rinforzo della muscolatura
    peroneale e propriocezione. L'utilizzo di tutori può essere indicato
    nelle fasi iniziali per proteggere i tessuti lesionati.
    
    La fisioterapia moderna impiega tecniche come ultrasuoni e laserterapia
    per accelerare il processo di guarigione, mentre il massaggio dei tessuti
    molli può ridurre la rigidità e migliorare la vascolarizzazione locale.
    """
    
    # Chunk the document
    chunks = chunker.chunk_document(
        content=sample_text,
        title="Riabilitazione Distorsione Caviglia",
        source="example_medical.md"
    )
    
    print(f"Created {len(chunks)} chunks")
    
    # Extract entities
    enriched_chunks = await graph_builder.extract_entities_from_chunks(chunks)
    
    for i, chunk in enumerate(enriched_chunks):
        print(f"Chunk {i}: {chunk.metadata.get('entities', {})}")
    
    # Add to knowledge graph
    try:
        result = await graph_builder.add_document_to_graph(
            chunks=enriched_chunks,
            document_title="Riabilitazione Distorsione Caviglia",
            document_source="example_medical.md",
            document_metadata={"topic": "riabilitazione", "anatomia": "caviglia", "date": "2024"}
        )
        
        print(f"Graph building result: {result}")
        
    except Exception as e:
        print(f"Graph building failed: {e}")
    
    finally:
        await graph_builder.close()


if __name__ == "__main__":
    asyncio.run(main())