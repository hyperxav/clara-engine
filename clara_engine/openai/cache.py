"""Cache implementation for OpenAI prompts."""

from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import hashlib
from collections import OrderedDict
import numpy as np
from pydantic import BaseModel, Field
import structlog
from sentence_transformers import SentenceTransformer

logger = structlog.get_logger(__name__)

class CacheEntry(BaseModel):
    """Entry in the prompt cache."""
    prompt: str = Field(..., description="Original prompt text")
    response: str = Field(..., description="Cached response")
    embedding: List[float] = Field(..., description="Prompt embedding for similarity comparison")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Entry creation time")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="Last access time")
    access_count: int = Field(default=0, description="Number of times this entry was accessed")

class PromptCache:
    """Cache for OpenAI prompts with semantic similarity matching."""

    def __init__(
        self,
        max_size: int = 1000,
        similarity_threshold: float = 0.95,
        ttl_seconds: int = 3600,
        model_name: str = "all-MiniLM-L6-v2"
    ) -> None:
        """Initialize the prompt cache.
        
        Args:
            max_size: Maximum number of entries to store
            similarity_threshold: Minimum cosine similarity for a cache hit
            ttl_seconds: Time-to-live for cache entries in seconds
            model_name: Name of the sentence transformer model to use
        """
        self.max_size = max_size
        self.similarity_threshold = similarity_threshold
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._model = SentenceTransformer(model_name)
        
        # Statistics
        self._hits = 0
        self._misses = 0
        
        logger.info(
            "Initialized prompt cache",
            max_size=max_size,
            similarity_threshold=similarity_threshold,
            ttl_seconds=ttl_seconds,
            model=model_name
        )

    def _compute_embedding(self, text: str) -> List[float]:
        """Compute embedding for text using sentence transformer.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        embedding = self._model.encode([text])[0]
        return embedding.tolist()

    def _compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry has expired.
        
        Args:
            entry: Cache entry to check
            
        Returns:
            True if expired, False otherwise
        """
        return (datetime.utcnow() - entry.created_at) > self.ttl

    def _find_similar_entry(self, prompt: str, embedding: List[float]) -> Optional[Tuple[str, CacheEntry]]:
        """Find a similar prompt in the cache.
        
        Args:
            prompt: Prompt to find similar entry for
            embedding: Embedding of the prompt
            
        Returns:
            Tuple of (cache_key, entry) if found, None otherwise
        """
        for key, entry in self._cache.items():
            if not self._is_expired(entry):
                similarity = self._compute_similarity(embedding, entry.embedding)
                if similarity >= self.similarity_threshold:
                    logger.debug(
                        "Found similar prompt",
                        similarity=similarity,
                        original=entry.prompt,
                        new=prompt
                    )
                    return key, entry
        return None

    def get(self, prompt: str) -> Optional[str]:
        """Get a response from the cache.
        
        Args:
            prompt: Prompt to look up
            
        Returns:
            Cached response if found, None otherwise
        """
        # Compute embedding for similarity search
        embedding = self._compute_embedding(prompt)
        
        # Look for exact match first
        key = hashlib.sha256(prompt.encode()).hexdigest()
        entry = self._cache.get(key)
        
        # If no exact match, look for similar prompt
        if entry is None or self._is_expired(entry):
            similar = self._find_similar_entry(prompt, embedding)
            if similar:
                key, entry = similar
            else:
                self._misses += 1
                logger.debug("Cache miss", prompt=prompt)
                return None
        
        # Update entry stats
        entry.last_accessed = datetime.utcnow()
        entry.access_count += 1
        self._cache.move_to_end(key)
        self._hits += 1
        
        logger.debug(
            "Cache hit",
            prompt=prompt,
            cached_prompt=entry.prompt,
            access_count=entry.access_count
        )
        
        return entry.response

    def put(self, prompt: str, response: str, metadata: Optional[Dict[str, str]] = None) -> None:
        """Add a prompt-response pair to the cache.
        
        Args:
            prompt: Prompt text
            response: Response text
            metadata: Optional metadata to store with the entry
        """
        # Compute key and embedding
        key = hashlib.sha256(prompt.encode()).hexdigest()
        embedding = self._compute_embedding(prompt)
        
        # Create cache entry
        entry = CacheEntry(
            prompt=prompt,
            response=response,
            embedding=embedding,
            metadata=metadata or {}
        )
        
        # Add to cache
        self._cache[key] = entry
        self._cache.move_to_end(key)
        
        # Evict oldest entries if cache is full
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)
            
        logger.debug(
            "Added cache entry",
            prompt=prompt,
            cache_size=len(self._cache)
        )

    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.info("Cleared prompt cache")

    @property
    def size(self) -> int:
        """Get current number of entries in cache."""
        return len(self._cache)

    @property
    def hit_ratio(self) -> float:
        """Get cache hit ratio."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": self.hit_ratio
        } 