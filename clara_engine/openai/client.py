"""OpenAI client implementation for Clara Engine."""

import os
from typing import Optional, Dict, Any
from openai import AsyncOpenAI, AsyncAzureOpenAI
from pydantic import BaseModel, Field
import structlog

from .cache import PromptCache

logger = structlog.get_logger(__name__)

class OpenAIConfig(BaseModel):
    """Configuration for OpenAI client."""
    api_key: str = Field(..., description="OpenAI API key")
    model: str = Field(default="gpt-3.5-turbo", description="Model to use for completions")
    max_tokens: int = Field(default=150, description="Maximum tokens per request")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    azure_endpoint: Optional[str] = Field(default=None, description="Azure OpenAI endpoint if using Azure")
    cache_enabled: bool = Field(default=True, description="Whether to enable prompt caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    cache_similarity: float = Field(default=0.95, description="Minimum similarity for cache hits")
    cache_size: int = Field(default=1000, description="Maximum cache size")

class OpenAIClient:
    """Client for interacting with OpenAI API."""

    def __init__(self, config: Optional[OpenAIConfig] = None) -> None:
        """Initialize the OpenAI client.
        
        Args:
            config: OpenAI configuration. If not provided, will load from environment.
        """
        self.config = config or self._load_config()
        self.client: Optional[AsyncOpenAI | AsyncAzureOpenAI] = None
        self._token_count: int = 0
        self._request_count: int = 0
        
        # Initialize cache if enabled
        self._cache: Optional[PromptCache] = None
        if self.config.cache_enabled:
            self._cache = PromptCache(
                max_size=self.config.cache_size,
                similarity_threshold=self.config.cache_similarity,
                ttl_seconds=self.config.cache_ttl
            )
            logger.info(
                "Initialized prompt cache",
                size=self.config.cache_size,
                similarity=self.config.cache_similarity,
                ttl=self.config.cache_ttl
            )

    @staticmethod
    def _load_config() -> OpenAIConfig:
        """Load configuration from environment variables."""
        return OpenAIConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "150")),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            azure_endpoint=os.getenv("OPENAI_AZURE_ENDPOINT"),
            cache_enabled=os.getenv("OPENAI_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl=int(os.getenv("OPENAI_CACHE_TTL", "3600")),
            cache_similarity=float(os.getenv("OPENAI_CACHE_SIMILARITY", "0.95")),
            cache_size=int(os.getenv("OPENAI_CACHE_SIZE", "1000"))
        )

    async def initialize(self) -> None:
        """Initialize the OpenAI client asynchronously."""
        if self.config.azure_endpoint:
            self.client = AsyncAzureOpenAI(
                api_key=self.config.api_key,
                azure_endpoint=self.config.azure_endpoint,
            )
        else:
            self.client = AsyncOpenAI(api_key=self.config.api_key)
        
        # Validate connection
        try:
            models = await self.client.models.list()
            logger.info(
                "OpenAI client initialized",
                model=self.config.model,
                available_models=len(models.data)
            )
        except Exception as e:
            logger.error("Failed to initialize OpenAI client", error=str(e))
            raise

    async def close(self) -> None:
        """Close the client connection."""
        if self.client:
            await self.client.close()
            self.client = None

    async def generate_completion(
        self,
        prompt: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate a completion for a prompt.
        
        Args:
            prompt: The prompt to generate a completion for
            metadata: Optional metadata to store with cached responses
            
        Returns:
            The generated completion text
            
        Raises:
            ValueError: If client is not initialized
        """
        if not self.client:
            raise ValueError("Client not initialized. Call initialize() first.")
            
        # Check cache first if enabled
        if self._cache:
            cached = self._cache.get(prompt)
            if cached:
                logger.info("Using cached response", prompt=prompt)
                return cached
        
        # Generate new completion
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            completion = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Update usage stats
            self._update_usage(tokens_used)
            
            # Cache response if enabled
            if self._cache:
                self._cache.put(prompt, completion, metadata)
                
            return completion
            
        except Exception as e:
            logger.error(
                "Failed to generate completion",
                error=str(e),
                prompt=prompt
            )
            raise

    @property
    def token_count(self) -> int:
        """Get the total number of tokens used."""
        return self._token_count

    @property
    def request_count(self) -> int:
        """Get the total number of requests made."""
        return self._request_count

    @property
    def cache_stats(self) -> Optional[Dict[str, int]]:
        """Get cache statistics if enabled."""
        return self._cache.get_stats() if self._cache else None

    def _update_usage(self, tokens: int) -> None:
        """Update token usage statistics."""
        self._token_count += tokens
        self._request_count += 1
        logger.debug(
            "Updated usage statistics",
            total_tokens=self._token_count,
            total_requests=self._request_count
        ) 