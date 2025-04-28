"""Tests for tweet generator."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from clara_engine.twitter.generator import TweetGenerator, TweetGenerationConfig
from clara_engine.openai.client import OpenAIClient
from clara_engine.openai.prompts import PromptManager
from clara_engine.openai.validators import ResponseValidator, ValidationResult
from clara_engine.knowledge.base import KnowledgeBase, KnowledgeEntry

@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    client = Mock(spec=OpenAIClient)
    client.generate_completion = AsyncMock()
    return client

@pytest.fixture
def mock_prompts():
    """Mock prompt manager."""
    manager = Mock(spec=PromptManager)
    template = Mock()
    template.render = Mock(return_value="Test prompt")
    manager.get_template.return_value = template
    return manager

@pytest.fixture
def mock_validator():
    """Mock response validator."""
    validator = Mock(spec=ResponseValidator)
    validator.validate = AsyncMock(return_value=ValidationResult(valid=True))
    return validator

@pytest.fixture
def mock_knowledge_base():
    """Mock knowledge base."""
    kb = Mock(spec=KnowledgeBase)
    kb.search = Mock(return_value=[
        KnowledgeEntry(id="1", content="Context 1"),
        KnowledgeEntry(id="2", content="Context 2"),
        KnowledgeEntry(id="3", content="Context 3"),
        KnowledgeEntry(id="4", content="Context 4")
    ])
    return kb

@pytest.fixture
def generator(
    mock_openai: Mock,
    mock_prompts: Mock,
    mock_validator: Mock,
    mock_knowledge_base: Mock
):
    """Create tweet generator with mocked dependencies."""
    return TweetGenerator(
        openai_client=mock_openai,
        prompt_manager=mock_prompts,
        validator=mock_validator,
        knowledge_base=mock_knowledge_base
    )

@pytest.mark.asyncio
async def test_generate_tweet_with_knowledge_base(generator: TweetGenerator):
    """Test tweet generation with knowledge base context."""
    # Setup completion response
    completion = Mock()
    completion.choices = [Mock(text="Generated tweet")]
    generator.openai.generate_completion.return_value = completion
    
    # Generate tweet
    tweet = await generator.generate_tweet(
        topic="test topic",
        metadata_filter={"category": "tech"}
    )
    
    # Verify knowledge base was queried
    generator.knowledge_base.search.assert_called_once_with(
        query="test topic",
        metadata_filter={"category": "tech"}
    )
    
    # Verify prompt includes context
    template = generator.prompts.get_template.return_value
    template.render.assert_called_once()
    args = template.render.call_args[1]
    assert len(args["context_entries"]) == 3  # Default max_context_entries
    assert args["context_entries"] == ["Context 1", "Context 2", "Context 3"]

@pytest.mark.asyncio
async def test_generate_tweet_without_knowledge_base():
    """Test tweet generation without knowledge base."""
    generator = TweetGenerator(
        openai_client=Mock(spec=OpenAIClient),
        prompt_manager=Mock(spec=PromptManager),
        validator=Mock(spec=ResponseValidator),
        config=TweetGenerationConfig(use_knowledge_base=False)
    )
    
    # Setup mocks
    completion = Mock()
    completion.choices = [Mock(text="Generated tweet")]
    generator.openai.generate_completion = AsyncMock(return_value=completion)
    
    template = Mock()
    template.render = Mock(return_value="Test prompt")
    generator.prompts.get_template.return_value = template
    
    generator.validator.validate = AsyncMock(return_value=ValidationResult(valid=True))
    
    # Generate tweet
    tweet = await generator.generate_tweet(topic="test topic")
    
    # Verify prompt excludes context
    template.render.assert_called_once()
    args = template.render.call_args[1]
    assert len(args["context_entries"]) == 0

@pytest.mark.asyncio
async def test_generate_tweet_with_custom_config(
    mock_openai: Mock,
    mock_prompts: Mock,
    mock_validator: Mock,
    mock_knowledge_base: Mock
):
    """Test tweet generation with custom config."""
    config = TweetGenerationConfig(
        max_context_entries=2,
        temperature=0.5,
        max_tokens=50
    )
    
    generator = TweetGenerator(
        openai_client=mock_openai,
        prompt_manager=mock_prompts,
        validator=mock_validator,
        knowledge_base=mock_knowledge_base,
        config=config
    )
    
    # Setup completion response
    completion = Mock()
    completion.choices = [Mock(text="Generated tweet")]
    generator.openai.generate_completion.return_value = completion
    
    # Generate tweet
    tweet = await generator.generate_tweet(topic="test topic")
    
    # Verify only 2 context entries used
    template = generator.prompts.get_template.return_value
    template.render.assert_called_once()
    args = template.render.call_args[1]
    assert len(args["context_entries"]) == 2
    
    # Verify custom config used
    generator.openai.generate_completion.assert_called_once()
    args = generator.openai.generate_completion.call_args[1]
    assert args["temperature"] == 0.5
    assert args["max_tokens"] == 50

@pytest.mark.asyncio
async def test_generate_tweet_validation_failure(generator: TweetGenerator):
    """Test tweet generation with validation failure."""
    # Setup mocks
    completion = Mock()
    completion.choices = [Mock(text="Invalid tweet")]
    generator.openai.generate_completion.return_value = completion
    
    generator.validator.validate = AsyncMock(return_value=ValidationResult(
        valid=False,
        errors=["Tweet too long"],
        warnings=["Contains hashtag"]
    ))
    
    # Attempt generation
    with pytest.raises(ValueError) as exc:
        await generator.generate_tweet(topic="test topic")
    
    assert "Failed to generate valid tweet" in str(exc.value)
    assert generator.openai.generate_completion.call_count == 3  # Default max attempts

@pytest.mark.asyncio
async def test_generate_tweet_with_previous_tweets(generator: TweetGenerator):
    """Test tweet generation with previous tweets context."""
    # Setup completion response
    completion = Mock()
    completion.choices = [Mock(text="Generated tweet")]
    generator.openai.generate_completion.return_value = completion
    
    previous_tweets = [
        "First tweet",
        "Second tweet"
    ]
    
    # Generate tweet
    tweet = await generator.generate_tweet(
        topic="test topic",
        previous_tweets=previous_tweets
    )
    
    # Verify prompt includes previous tweets
    template = generator.prompts.get_template.return_value
    template.render.assert_called_once()
    args = template.render.call_args[1]
    assert args["previous_tweets"] == previous_tweets 