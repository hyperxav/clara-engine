"""Tests for OpenAI client implementation."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from openai.types.chat import ChatCompletion, ChatCompletionMessage, Choice
from openai.types import CompletionUsage

from clara_engine.openai.client import OpenAIClient, OpenAIConfig

@pytest.fixture
def config():
    """Create a test configuration."""
    return OpenAIConfig(
        api_key="test-key",
        model="gpt-3.5-turbo",
        max_tokens=100,
        temperature=0.5,
        cache_enabled=True,
        cache_ttl=60,
        cache_similarity=0.9,
        cache_size=10
    )

@pytest.fixture
def mock_response():
    """Create a mock OpenAI response."""
    response = MagicMock(spec=ChatCompletion)
    response.choices = [
        Choice(
            finish_reason="stop",
            index=0,
            message=ChatCompletionMessage(
                content="Test response",
                role="assistant"
            )
        )
    ]
    response.usage = CompletionUsage(
        completion_tokens=10,
        prompt_tokens=5,
        total_tokens=15
    )
    return response

@pytest.fixture
async def client(config):
    """Create a test client."""
    client = OpenAIClient(config)
    await client.initialize()
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_client_initialization(client):
    """Test client initialization."""
    assert client.config.api_key == "test-key"
    assert client.config.model == "gpt-3.5-turbo"
    assert client._cache is not None
    assert client._cache.size() == 0

@pytest.mark.asyncio
async def test_client_initialization_from_env():
    """Test client initialization from environment variables."""
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "env-key",
        "OPENAI_MODEL": "gpt-4",
        "OPENAI_MAX_TOKENS": "200",
        "OPENAI_TEMPERATURE": "0.8",
        "OPENAI_CACHE_ENABLED": "true",
        "OPENAI_CACHE_TTL": "120",
        "OPENAI_CACHE_SIMILARITY": "0.85",
        "OPENAI_CACHE_SIZE": "20"
    }):
        client = OpenAIClient()
        assert client.config.api_key == "env-key"
        assert client.config.model == "gpt-4"
        assert client.config.max_tokens == 200
        assert client.config.temperature == 0.8
        assert client.config.cache_enabled is True
        assert client.config.cache_ttl == 120
        assert client.config.cache_similarity == 0.85
        assert client.config.cache_size == 20

@pytest.mark.asyncio
async def test_completion_generation(client, mock_response):
    """Test completion generation."""
    with patch.object(client.client.chat.completions, "create", 
                     AsyncMock(return_value=mock_response)):
        response = await client.generate_completion("Test prompt")
        assert response == "Test response"
        assert client.token_count == 15
        assert client.request_count == 1

@pytest.mark.asyncio
async def test_completion_caching(client, mock_response):
    """Test completion caching."""
    with patch.object(client.client.chat.completions, "create", 
                     AsyncMock(return_value=mock_response)):
        # First request should hit the API
        response1 = await client.generate_completion("Test prompt")
        assert response1 == "Test response"
        assert client.token_count == 15
        assert client.request_count == 1
        
        # Second request should hit the cache
        response2 = await client.generate_completion("Test prompt")
        assert response2 == "Test response"
        assert client.token_count == 15  # Should not increase
        assert client.request_count == 1  # Should not increase
        
        # Cache stats should show one hit
        stats = client.cache_stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1

@pytest.mark.asyncio
async def test_similar_prompt_caching(client, mock_response):
    """Test caching with similar prompts."""
    with patch.object(client.client.chat.completions, "create", 
                     AsyncMock(return_value=mock_response)):
        # First request
        await client.generate_completion("Generate a tweet about cats")
        
        # Similar prompt should hit cache
        response = await client.generate_completion("Generate a tweet about kittens")
        assert response == "Test response"
        assert client.request_count == 1  # Should not increase
        
        # Very different prompt should miss cache
        await client.generate_completion("Write a novel about space travel")
        assert client.request_count == 2

@pytest.mark.asyncio
async def test_cache_with_metadata(client, mock_response):
    """Test caching with metadata."""
    with patch.object(client.client.chat.completions, "create", 
                     AsyncMock(return_value=mock_response)):
        metadata = {"user_id": "123", "context": "test"}
        await client.generate_completion("Test prompt", metadata=metadata)
        
        # Verify metadata is stored
        cached = client._cache.get("Test prompt")
        assert cached == "Test response"

@pytest.mark.asyncio
async def test_error_handling(client):
    """Test error handling during completion generation."""
    with patch.object(client.client.chat.completions, "create", 
                     AsyncMock(side_effect=Exception("API Error"))):
        with pytest.raises(Exception) as exc_info:
            await client.generate_completion("Test prompt")
        assert str(exc_info.value) == "API Error"

@pytest.mark.asyncio
async def test_azure_client_initialization():
    """Test Azure OpenAI client initialization."""
    config = OpenAIConfig(
        api_key="test-key",
        azure_endpoint="https://test.openai.azure.com"
    )
    client = OpenAIClient(config)
    await client.initialize()
    assert client.client is not None
    await client.close()

@pytest.mark.asyncio
async def test_client_cleanup(client):
    """Test client cleanup."""
    await client.close()
    assert client.client is None 