"""Tests for knowledge base functionality."""

import pytest
from unittest.mock import Mock, patch
import numpy as np
from datetime import datetime, timedelta

from clara_engine.knowledge.base import (
    KnowledgeBase,
    KnowledgeBaseConfig,
    KnowledgeEntry
)

@pytest.fixture
def mock_model():
    """Create mock sentence transformer."""
    model = Mock()
    # Mock encode to return simple numpy arrays
    model.encode.return_value = np.array([0.1, 0.2, 0.3])
    return model

@pytest.fixture
def knowledge_base(mock_model):
    """Create knowledge base with mock model."""
    with patch("clara_engine.knowledge.base.SentenceTransformer", return_value=mock_model):
        kb = KnowledgeBase(KnowledgeBaseConfig(
            embedding_model="test-model",
            similarity_threshold=0.7,
            max_results=3,
            cache_embeddings=True
        ))
        return kb

def test_initialization():
    """Test knowledge base initialization."""
    config = KnowledgeBaseConfig(
        embedding_model="custom-model",
        similarity_threshold=0.8,
        max_results=5
    )
    kb = KnowledgeBase(config)
    
    assert kb.config.embedding_model == "custom-model"
    assert kb.config.similarity_threshold == 0.8
    assert kb.config.max_results == 5
    assert len(kb.entries) == 0

def test_add_entry(knowledge_base, mock_model):
    """Test adding entries to knowledge base."""
    # Add entry with content only
    entry1 = knowledge_base.add_entry("Test content 1")
    assert entry1.id == "1"
    assert entry1.content == "Test content 1"
    assert entry1.metadata == {}
    assert entry1.embedding == [0.1, 0.2, 0.3]
    assert isinstance(entry1.created_at, datetime)
    
    # Add entry with metadata
    metadata = {"source": "test", "category": "example"}
    entry2 = knowledge_base.add_entry("Test content 2", metadata)
    assert entry2.id == "2"
    assert entry2.metadata == metadata
    
    assert len(knowledge_base.entries) == 2
    mock_model.encode.assert_called()

def test_get_entry(knowledge_base):
    """Test retrieving entries."""
    entry = knowledge_base.add_entry("Test content")
    
    # Get existing entry
    retrieved = knowledge_base.get_entry(entry.id)
    assert retrieved == entry
    
    # Get non-existent entry
    assert knowledge_base.get_entry("nonexistent") is None

def test_update_entry(knowledge_base, mock_model):
    """Test updating entries."""
    entry = knowledge_base.add_entry("Original content", {"key": "value"})
    original_created = entry.created_at
    
    # Update content
    updated = knowledge_base.update_entry(entry.id, content="Updated content")
    assert updated.content == "Updated content"
    assert updated.created_at == original_created
    assert updated.updated_at > original_created
    assert mock_model.encode.call_count == 2  # Initial + update
    
    # Update metadata
    updated = knowledge_base.update_entry(entry.id, metadata={"new": "value"})
    assert updated.metadata == {"key": "value", "new": "value"}
    
    # Update non-existent entry
    assert knowledge_base.update_entry("nonexistent") is None

def test_remove_entry(knowledge_base):
    """Test removing entries."""
    entry = knowledge_base.add_entry("Test content")
    
    # Remove existing entry
    assert knowledge_base.remove_entry(entry.id) is True
    assert len(knowledge_base.entries) == 0
    
    # Remove non-existent entry
    assert knowledge_base.remove_entry("nonexistent") is False

def test_search_exact_match(knowledge_base, mock_model):
    """Test search with exact content match."""
    # Mock similarity to return 1.0 for exact match
    with patch("clara_engine.knowledge.base.np.dot") as mock_dot:
        mock_dot.return_value = 1.0
        
        entry = knowledge_base.add_entry("Test content")
        results = knowledge_base.search("Test content")
        
        assert len(results) == 1
        assert results[0] == entry

def test_search_with_threshold(knowledge_base):
    """Test search with similarity threshold."""
    knowledge_base.add_entry("First entry")
    knowledge_base.add_entry("Second entry")
    
    # Mock different similarities
    with patch("clara_engine.knowledge.base.np.dot") as mock_dot:
        mock_dot.side_effect = [0.8, 0.6]  # First above threshold, second below
        
        results = knowledge_base.search("test query")
        assert len(results) == 1  # Only one result above threshold

def test_search_with_metadata_filter(knowledge_base):
    """Test search with metadata filtering."""
    knowledge_base.add_entry("Entry 1", {"category": "A"})
    knowledge_base.add_entry("Entry 2", {"category": "B"})
    
    # Mock high similarity for both
    with patch("clara_engine.knowledge.base.np.dot") as mock_dot:
        mock_dot.return_value = 0.9
        
        results = knowledge_base.search("test", metadata_filter={"category": "A"})
        assert len(results) == 1
        assert results[0].metadata["category"] == "A"

def test_search_max_results(knowledge_base):
    """Test search respects max_results limit."""
    # Add more entries than max_results
    for i in range(5):
        knowledge_base.add_entry(f"Entry {i}")
    
    # Mock high similarity for all
    with patch("clara_engine.knowledge.base.np.dot") as mock_dot:
        mock_dot.return_value = 0.9
        
        results = knowledge_base.search("test")
        assert len(results) == knowledge_base.config.max_results

def test_clear(knowledge_base):
    """Test clearing all entries."""
    knowledge_base.add_entry("Entry 1")
    knowledge_base.add_entry("Entry 2")
    
    knowledge_base.clear()
    assert len(knowledge_base.entries) == 0

def test_embedding_caching(mock_model):
    """Test embedding caching behavior."""
    # Test with caching enabled
    kb_cached = KnowledgeBase(KnowledgeBaseConfig(cache_embeddings=True))
    with patch("clara_engine.knowledge.base.SentenceTransformer", return_value=mock_model):
        kb_cached.add_entry("Test content")
        kb_cached.search("query")  # Should use cached embedding
        assert mock_model.encode.call_count == 2  # Once for entry, once for query
    
    # Test with caching disabled
    mock_model.reset_mock()
    kb_nocache = KnowledgeBase(KnowledgeBaseConfig(cache_embeddings=False))
    with patch("clara_engine.knowledge.base.SentenceTransformer", return_value=mock_model):
        kb_nocache.add_entry("Test content")
        kb_nocache.search("query")  # Should recompute embedding
        assert mock_model.encode.call_count == 3  # Once for entry, once for query, once for search 