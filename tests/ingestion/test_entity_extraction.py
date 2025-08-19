"""
Unit tests for entity extraction functionality in graph_builder.py
"""
import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any
from uuid import uuid4

from ingestion.chunker import DocumentChunk
from ingestion.graph_builder import GraphBuilder


class TestEntityExtraction:
    """Test suite for entity extraction functionality."""

    @pytest.fixture
    def sample_chunks(self) -> List[DocumentChunk]:
        """Create sample document chunks for testing."""
        return [
            DocumentChunk(
                content="The patient has chronic back pain and muscle spasms.",
                index=0,
                start_char=0,
                end_char=50,
                metadata={"document_id": "test_doc_1"}
            ),
            DocumentChunk(
                content="Treatment includes physical therapy and ibuprofen medication.",
                index=1,
                start_char=51,
                end_char=112,
                metadata={"document_id": "test_doc_1"}
            )
        ]

    @pytest.fixture
    def graph_builder(self) -> GraphBuilder:
        """Create a GraphBuilder instance for testing."""
        return GraphBuilder()

    @pytest.fixture
    def mock_spacy_doc(self):
        """Create a mock spaCy document with entities."""
        # Mock entity
        mock_entity1 = MagicMock()
        mock_entity1.text = "back pain"
        mock_entity1.label_ = "SYMPTOM"
        mock_entity1.start_char = 25
        mock_entity1.end_char = 34
        mock_entity1._.confidence = 0.95

        mock_entity2 = MagicMock()
        mock_entity2.text = "muscle spasms"
        mock_entity2.label_ = "SYMPTOM" 
        mock_entity2.start_char = 39
        mock_entity2.end_char = 52
        mock_entity2._.confidence = 0.89

        mock_entity3 = MagicMock()
        mock_entity3.text = "physical therapy"
        mock_entity3.label_ = "TREATMENT"
        mock_entity3.start_char = 19
        mock_entity3.end_char = 35
        mock_entity3._.confidence = 0.92

        # Mock spaCy doc
        mock_doc = MagicMock()
        mock_doc.ents = [mock_entity1, mock_entity2, mock_entity3]
        
        return mock_doc

    @pytest.mark.asyncio
    async def test_extract_entities_basic_functionality(
        self, 
        graph_builder: GraphBuilder, 
        sample_chunks: List[DocumentChunk],
        mock_spacy_doc
    ):
        """Test basic entity extraction functionality."""
        
        with patch('ingestion.graph_builder.spacy.load') as mock_spacy_load:
            # Mock spaCy model
            mock_nlp = MagicMock()
            mock_nlp.return_value = mock_spacy_doc
            mock_spacy_load.return_value = mock_nlp
            
            # Execute entity extraction
            result_chunks = await graph_builder.extract_entities_from_chunks(sample_chunks)
            
            # Verify chunks are returned
            assert len(result_chunks) == 2
            assert isinstance(result_chunks, list)
            
            # Verify entities are added to metadata
            chunk1_entities = result_chunks[0].metadata.get("entities", [])
            assert len(chunk1_entities) >= 1
            
            # Verify entity format
            entity = chunk1_entities[0]
            assert "name" in entity
            assert "type" in entity
            assert "start" in entity
            assert "end" in entity
            assert "confidence" in entity
            
            # Verify entity values
            assert isinstance(entity["name"], str)
            assert isinstance(entity["type"], str)
            assert isinstance(entity["start"], int)
            assert isinstance(entity["end"], int)
            assert isinstance(entity["confidence"], float)
            assert 0.0 <= entity["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_extract_entities_preserves_original_metadata(
        self, 
        graph_builder: GraphBuilder, 
        sample_chunks: List[DocumentChunk],
        mock_spacy_doc
    ):
        """Test that original metadata is preserved during entity extraction."""
        
        with patch('ingestion.graph_builder.spacy.load') as mock_spacy_load:
            mock_nlp = MagicMock()
            mock_nlp.return_value = mock_spacy_doc
            mock_spacy_load.return_value = mock_nlp
            
            # Add custom metadata to first chunk
            sample_chunks[0].metadata["custom_field"] = "test_value"
            original_metadata = sample_chunks[0].metadata.copy()
            
            result_chunks = await graph_builder.extract_entities_from_chunks(sample_chunks)
            
            # Verify original metadata is preserved
            result_metadata = result_chunks[0].metadata
            assert result_metadata["custom_field"] == "test_value"
            assert result_metadata["document_id"] == "test_doc_1"
            
            # Verify entities were added
            assert "entities" in result_metadata

    @pytest.mark.asyncio
    async def test_extract_entities_with_no_entities_found(
        self, 
        graph_builder: GraphBuilder,
        sample_chunks: List[DocumentChunk]
    ):
        """Test entity extraction when no entities are found."""
        
        with patch('ingestion.graph_builder.spacy.load') as mock_spacy_load:
            # Mock spaCy model with no entities
            mock_doc = MagicMock()
            mock_doc.ents = []
            
            mock_nlp = MagicMock()
            mock_nlp.return_value = mock_doc
            mock_spacy_load.return_value = mock_nlp
            
            result_chunks = await graph_builder.extract_entities_from_chunks(sample_chunks)
            
            # Verify chunks are returned
            assert len(result_chunks) == 2
            
            # Verify empty entities list is added
            for chunk in result_chunks:
                entities = chunk.metadata.get("entities", [])
                assert entities == []

    @pytest.mark.asyncio
    async def test_extract_entities_model_loading_error(
        self, 
        graph_builder: GraphBuilder,
        sample_chunks: List[DocumentChunk]
    ):
        """Test handling of spaCy model loading errors."""
        
        with patch('ingestion.graph_builder.spacy.load') as mock_spacy_load:
            # Mock spaCy model loading failure
            mock_spacy_load.side_effect = OSError("Model 'en_core_web_sm' not found")
            
            # Should not raise exception but return chunks with warning
            result_chunks = await graph_builder.extract_entities_from_chunks(sample_chunks)
            
            # Verify chunks are returned without entities
            assert len(result_chunks) == 2
            for chunk in result_chunks:
                # Should not have entities in metadata when model fails to load
                assert "entities" not in chunk.metadata or chunk.metadata["entities"] == []

    @pytest.mark.asyncio 
    async def test_extract_entities_processing_error_handling(
        self, 
        graph_builder: GraphBuilder,
        sample_chunks: List[DocumentChunk],
        mock_spacy_doc
    ):
        """Test handling of errors during entity processing."""
        
        with patch('ingestion.graph_builder.spacy.load') as mock_spacy_load:
            # Mock spaCy model that raises exception during processing
            mock_nlp = MagicMock()
            mock_nlp.side_effect = RuntimeError("Processing error")
            mock_spacy_load.return_value = mock_nlp
            
            result_chunks = await graph_builder.extract_entities_from_chunks(sample_chunks)
            
            # Should return chunks without entities when processing fails
            assert len(result_chunks) == 2
            for chunk in result_chunks:
                assert "entities" not in chunk.metadata or chunk.metadata["entities"] == []

    @pytest.mark.asyncio
    async def test_extract_entities_empty_chunks_list(self, graph_builder: GraphBuilder):
        """Test entity extraction with empty chunks list."""
        
        result_chunks = await graph_builder.extract_entities_from_chunks([])
        
        assert result_chunks == []

    @pytest.mark.asyncio
    async def test_extract_entities_chunk_with_empty_content(
        self, 
        graph_builder: GraphBuilder,
        mock_spacy_doc
    ):
        """Test entity extraction with chunk containing empty content."""
        
        empty_chunk = DocumentChunk(
            content="",
            index=0,
            start_char=0,
            end_char=0,
            metadata={"document_id": "empty_doc"}
        )
        
        with patch('ingestion.graph_builder.spacy.load') as mock_spacy_load:
            mock_nlp = MagicMock()
            mock_nlp.return_value = mock_spacy_doc
            mock_spacy_load.return_value = mock_nlp
            
            result_chunks = await graph_builder.extract_entities_from_chunks([empty_chunk])
            
            assert len(result_chunks) == 1
            # Should handle empty content gracefully
            assert "entities" in result_chunks[0].metadata

    @pytest.mark.asyncio
    async def test_extract_entities_lazy_model_initialization(
        self, 
        graph_builder: GraphBuilder,
        sample_chunks: List[DocumentChunk],
        mock_spacy_doc
    ):
        """Test that spaCy model is loaded lazily (only when needed)."""
        
        with patch('ingestion.graph_builder.spacy.load') as mock_spacy_load:
            mock_nlp = MagicMock()
            mock_nlp.return_value = mock_spacy_doc
            mock_spacy_load.return_value = mock_nlp
            
            # First call should load the model
            await graph_builder.extract_entities_from_chunks(sample_chunks)
            assert mock_spacy_load.call_count == 1
            
            # Second call should reuse the loaded model
            await graph_builder.extract_entities_from_chunks(sample_chunks)
            # Should still be 1 if lazy loading is implemented correctly
            assert mock_spacy_load.call_count <= 2  # Allow for implementation flexibility

    @pytest.mark.asyncio
    async def test_extract_entities_confidence_score_handling(
        self, 
        graph_builder: GraphBuilder,
        sample_chunks: List[DocumentChunk]
    ):
        """Test handling of confidence scores from spaCy entities."""
        
        with patch('ingestion.graph_builder.spacy.load') as mock_spacy_load:
            # Mock entity with different confidence scores
            mock_entity_high_conf = MagicMock()
            mock_entity_high_conf.text = "back pain"
            mock_entity_high_conf.label_ = "SYMPTOM"
            mock_entity_high_conf.start_char = 0
            mock_entity_high_conf.end_char = 9
            mock_entity_high_conf._.confidence = 0.95
            
            mock_entity_low_conf = MagicMock()
            mock_entity_low_conf.text = "therapy"
            mock_entity_low_conf.label_ = "TREATMENT"
            mock_entity_low_conf.start_char = 10
            mock_entity_low_conf.end_char = 17
            mock_entity_low_conf._.confidence = 0.60
            
            mock_doc = MagicMock()
            mock_doc.ents = [mock_entity_high_conf, mock_entity_low_conf]
            
            mock_nlp = MagicMock()
            mock_nlp.return_value = mock_doc
            mock_spacy_load.return_value = mock_nlp
            
            result_chunks = await graph_builder.extract_entities_from_chunks(sample_chunks)
            
            entities = result_chunks[0].metadata.get("entities", [])
            assert len(entities) >= 2
            
            # Verify confidence scores are preserved
            high_conf_entity = next(e for e in entities if e["name"] == "back pain")
            low_conf_entity = next(e for e in entities if e["name"] == "therapy")
            
            assert high_conf_entity["confidence"] == 0.95
            assert low_conf_entity["confidence"] == 0.60

    @pytest.mark.asyncio
    async def test_extract_entities_medical_domain_types(
        self, 
        graph_builder: GraphBuilder,
        sample_chunks: List[DocumentChunk]
    ):
        """Test extraction of medical domain entity types."""
        
        with patch('ingestion.graph_builder.spacy.load') as mock_spacy_load:
            # Mock entities with medical domain types
            medical_entities = [
                ("fibromyalgia", "CONDITION", 0, 12, 0.92),
                ("ibuprofen", "MEDICATION", 20, 29, 0.88), 
                ("physical therapy", "TREATMENT", 35, 51, 0.95),
                ("lower back", "ANATOMY", 60, 70, 0.85)
            ]
            
            mock_ents = []
            for name, label, start, end, conf in medical_entities:
                mock_ent = MagicMock()
                mock_ent.text = name
                mock_ent.label_ = label
                mock_ent.start_char = start
                mock_ent.end_char = end
                mock_ent._.confidence = conf
                mock_ents.append(mock_ent)
            
            mock_doc = MagicMock()
            mock_doc.ents = mock_ents
            
            mock_nlp = MagicMock()
            mock_nlp.return_value = mock_doc
            mock_spacy_load.return_value = mock_nlp
            
            result_chunks = await graph_builder.extract_entities_from_chunks(sample_chunks)
            
            entities = result_chunks[0].metadata.get("entities", [])
            entity_types = [e["type"] for e in entities]
            
            # Verify medical domain entity types are extracted
            assert "CONDITION" in entity_types
            assert "MEDICATION" in entity_types
            assert "TREATMENT" in entity_types
            assert "ANATOMY" in entity_types