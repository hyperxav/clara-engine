"""Tests for prompt cache functionality."""

import pytest
from datetime import datetime, timedelta
from clara_engine.openai.cache import PromptCache, CacheEntry

@pytest.fixture
def cache():
    """Create a cache instance for testing."""
    return PromptCache(
        max_size=5,
        similarity_threshold=0.9,
        ttl_seconds=60,
        model_name="all-MiniLM-L6-v2"
    )

def test_cache_initialization(cache):
    """Test cache initialization."""
    assert cache.max_size == 5
    assert cache.similarity_threshold == 0.9
    assert cache.size == 0
    assert cache.hit_ratio == 0.0

def test_exact_match_caching(cache):
    """Test exact match cache operations."""
    # Add entry
    prompt = "What is the meaning of life?"
    response = "42"
    cache.put(prompt, response)
    
    # Verify size
    assert cache.size == 1
    
    # Get exact match
    result = cache.get(prompt)
    assert result == response
    
    # Check stats
    assert cache.hit_ratio == 1.0
    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 0

def test_similar_prompt_matching(cache):
    """Test similar prompt matching."""
    # Add original entry
    original = "What is the meaning of life?"
    response = "42"
    cache.put(original, response)
    
    # Try similar prompt
    similar = "Tell me the meaning of life"
    result = cache.get(similar)
    assert result == response
    
    # Try dissimilar prompt
    dissimilar = "What is the weather today?"
    result = cache.get(dissimilar)
    assert result is None

def test_cache_eviction(cache):
    """Test cache size limit and eviction."""
    # Fill cache
    for i in range(6):
        cache.put(f"prompt{i}", f"response{i}")
    
    # Verify size
    assert cache.size == 5
    
    # Verify oldest entry was evicted
    result = cache.get("prompt0")
    assert result is None
    
    # Verify newest entries remain
    result = cache.get("prompt5")
    assert result == "response5"

def test_cache_expiration(cache):
    """Test cache entry expiration."""
    prompt = "test prompt"
    response = "test response"
    
    # Add entry with short TTL
    cache = PromptCache(ttl_seconds=1)
    cache.put(prompt, response)
    
    # Verify immediate retrieval
    assert cache.get(prompt) == response
    
    # Wait for expiration
    import time
    time.sleep(1.1)
    
    # Verify expired entry not returned
    assert cache.get(prompt) is None

def test_cache_metadata(cache):
    """Test metadata storage and retrieval."""
    prompt = "test prompt"
    response = "test response"
    metadata = {"source": "test", "type": "query"}
    
    # Add entry with metadata
    cache.put(prompt, response, metadata)
    
    # Get entry
    result = cache.get(prompt)
    assert result == response
    
    # Verify metadata in cache
    entry = next(iter(cache._cache.values()))
    assert entry.metadata == metadata

def test_cache_clear(cache):
    """Test cache clearing."""
    # Add some entries
    cache.put("prompt1", "response1")
    cache.put("prompt2", "response2")
    
    # Clear cache
    cache.clear()
    
    # Verify cache is empty
    assert cache.size == 0
    assert cache.hit_ratio == 0.0
    
    # Verify entries are gone
    assert cache.get("prompt1") is None
    assert cache.get("prompt2") is None

def test_cache_statistics(cache):
    """Test cache statistics tracking."""
    # Add entry
    cache.put("prompt", "response")
    
    # Generate hits
    cache.get("prompt")
    cache.get("prompt")
    
    # Generate misses
    cache.get("missing1")
    cache.get("missing2")
    
    # Check stats
    stats = cache.get_stats()
    assert stats["hits"] == 2
    assert stats["misses"] == 2
    assert stats["size"] == 1
    assert stats["hit_ratio"] == 0.5

def test_embedding_computation(cache):
    """Test embedding computation."""
    # Get embeddings for different texts
    text1 = "This is a test"
    text2 = "This is another test"
    text3 = "Something completely different"
    
    emb1 = cache._compute_embedding(text1)
    emb2 = cache._compute_embedding(text2)
    emb3 = cache._compute_embedding(text3)
    
    # Check embedding format
    assert isinstance(emb1, list)
    assert all(isinstance(x, float) for x in emb1)
    
    # Check similarity scores
    sim12 = cache._compute_similarity(emb1, emb2)
    sim13 = cache._compute_similarity(emb1, emb3)
    
    # Similar texts should have higher similarity
    assert sim12 > sim13

def test_cache_entry_model():
    """Test CacheEntry model."""
    entry = CacheEntry(
        prompt="test",
        response="response",
        embedding=[0.1, 0.2, 0.3],
        metadata={"type": "test"},
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow(),
        access_count=1
    )
    
    assert entry.prompt == "test"
    assert entry.response == "response"
    assert len(entry.embedding) == 3
    assert entry.metadata["type"] == "test"
    assert isinstance(entry.created_at, datetime)
    assert isinstance(entry.last_accessed, datetime)
    assert entry.access_count == 1 