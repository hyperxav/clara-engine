"""Knowledge base integration for Clara Engine."""

from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
import numpy as np

logger = structlog.get_logger(__name__)

class KnowledgeEntry(BaseModel):
    """A single entry in the knowledge base."""
    id: str = Field(..., description="Unique identifier for the entry")
    content: str = Field(..., description="The actual content/text of the entry")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding of content")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Entry creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Entry last update time")

class KnowledgeBaseConfig(BaseModel):
    """Configuration for knowledge base."""
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Model to use for text embeddings"
    )
    similarity_threshold: float = Field(
        default=0.7,
        description="Minimum similarity score for relevant entries"
    )
    max_results: int = Field(
        default=5,
        description="Maximum number of entries to return in search"
    )
    cache_embeddings: bool = Field(
        default=True,
        description="Whether to cache computed embeddings"
    )

class KnowledgeBase:
    """Knowledge base for storing and retrieving contextual information."""
    
    def __init__(self, config: Optional[KnowledgeBaseConfig] = None):
        """Initialize knowledge base.
        
        Args:
            config: Optional configuration for the knowledge base
        """
        self.config = config or KnowledgeBaseConfig()
        self.entries: Dict[str, KnowledgeEntry] = {}
        self._model = None
        self.logger = logger.bind(component="knowledge_base")
        
    @property
    def model(self) -> SentenceTransformer:
        """Get or initialize the embedding model."""
        if self._model is None:
            self.logger.info(
                "Initializing embedding model",
                model=self.config.embedding_model
            )
            self._model = SentenceTransformer(self.config.embedding_model)
        return self._model
        
    def _compute_embedding(self, text: str) -> List[float]:
        """Compute embedding for text."""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
        
    def _compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
        
    def add_entry(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> KnowledgeEntry:
        """Add a new entry to the knowledge base.
        
        Args:
            content: The text content to add
            metadata: Optional metadata for the entry
            
        Returns:
            The created knowledge entry
        """
        entry_id = str(len(self.entries) + 1)  # Simple sequential IDs
        
        entry = KnowledgeEntry(
            id=entry_id,
            content=content,
            metadata=metadata or {},
            embedding=self._compute_embedding(content) if self.config.cache_embeddings else None
        )
        
        self.entries[entry_id] = entry
        self.logger.info(
            "Added knowledge entry",
            entry_id=entry_id,
            content_length=len(content)
        )
        
        return entry
        
    def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get an entry by ID."""
        return self.entries.get(entry_id)
        
    def update_entry(
        self,
        entry_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[KnowledgeEntry]:
        """Update an existing entry.
        
        Args:
            entry_id: ID of entry to update
            content: Optional new content
            metadata: Optional new metadata
            
        Returns:
            The updated entry or None if not found
        """
        entry = self.entries.get(entry_id)
        if not entry:
            return None
            
        if content is not None:
            entry.content = content
            if self.config.cache_embeddings:
                entry.embedding = self._compute_embedding(content)
                
        if metadata is not None:
            entry.metadata.update(metadata)
            
        entry.updated_at = datetime.utcnow()
        self.logger.info("Updated knowledge entry", entry_id=entry_id)
        
        return entry
        
    def remove_entry(self, entry_id: str) -> bool:
        """Remove an entry from the knowledge base."""
        if entry_id in self.entries:
            del self.entries[entry_id]
            self.logger.info("Removed knowledge entry", entry_id=entry_id)
            return True
        return False
        
    def search(self, query: str, metadata_filter: Optional[Dict[str, Any]] = None) -> List[KnowledgeEntry]:
        """Search for relevant entries.
        
        Args:
            query: Search query text
            metadata_filter: Optional metadata to filter results
            
        Returns:
            List of relevant entries sorted by similarity
        """
        query_embedding = self._compute_embedding(query)
        results = []
        
        for entry in self.entries.values():
            # Apply metadata filter if specified
            if metadata_filter:
                if not all(entry.metadata.get(k) == v for k, v in metadata_filter.items()):
                    continue
                    
            # Compute similarity
            entry_embedding = entry.embedding or self._compute_embedding(entry.content)
            similarity = self._compute_similarity(query_embedding, entry_embedding)
            
            if similarity >= self.config.similarity_threshold:
                results.append((similarity, entry))
                
        # Sort by similarity and return top results
        results.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in results[:self.config.max_results]]
        
    def clear(self) -> None:
        """Clear all entries from the knowledge base."""
        self.entries.clear()
        self.logger.info("Cleared knowledge base") 