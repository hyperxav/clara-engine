"""Tests for tweet scheduler."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
import uuid
import asyncio

from clara_engine.core.scheduler import TweetScheduler, SchedulerConfig
from clara_engine.clients.manager import ClientContext
from clara_engine.twitter.client import TwitterError, TwitterRateLimitError
from clara_engine.models import Client as ClientModel, Tweet

@pytest.fixture
def mock_client_manager():
    """Create mock client manager."""
    manager = Mock()
    manager.get_clients_due_for_tweet = Mock()
    return manager

@pytest.fixture
def mock_db():
    """Create mock database."""
    db = Mock()
    db.get_client = Mock()
    db.create_tweet = Mock()
    db.update_tweet = Mock()
    db.update_client = Mock()
    return db

@pytest.fixture
def mock_twitter_client():
    """Create mock Twitter client."""
    client = Mock()
    client.post_tweet = AsyncMock()
    return client

@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    client = Mock()
    client.generate_completion = AsyncMock()
    return client

@pytest.fixture
def mock_prompt_manager():
    """Create mock prompt manager."""
    return Mock()

@pytest.fixture
def mock_validator():
    """Create mock validator."""
    return Mock()

@pytest.fixture
def test_client():
    """Create test client model."""
    return ClientModel(
        id=uuid.uuid4(),
        name="Test Client",
        persona_prompt="Test persona",
        twitter_key="key",
        twitter_secret="secret",
        access_token="token",
        access_secret="secret",
        posting_hours=[9, 15, 21],
        timezone="UTC",
        active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def test_context(mock_twitter_client, mock_openai_client, mock_prompt_manager, mock_validator):
    """Create test client context."""
    return ClientContext(
        client_id="test_client",
        twitter_client=mock_twitter_client,
        openai_client=mock_openai_client,
        prompt_manager=mock_prompt_manager,
        validator=mock_validator,
        active=True
    )

@pytest.fixture
def scheduler(mock_client_manager, mock_db):
    """Create scheduler instance."""
    config = SchedulerConfig(
        check_interval=1,
        max_retries=2,
        retry_delay=1,
        batch_size=5
    )
    return TweetScheduler(mock_client_manager, mock_db, config)

@pytest.mark.asyncio
async def test_scheduler_start_stop(scheduler):
    """Test starting and stopping the scheduler."""
    # Start scheduler
    await scheduler.start()
    assert scheduler._running is True
    assert scheduler._task is not None
    
    # Try starting again
    await scheduler.start()  # Should log warning
    
    # Stop scheduler
    await scheduler.stop()
    assert scheduler._running is False
    assert scheduler._task is None

@pytest.mark.asyncio
async def test_process_client_success(
    scheduler, test_client, test_context, mock_db, mock_twitter_client
):
    """Test successful client processing."""
    # Setup mocks
    mock_db.get_client.return_value = test_client
    mock_twitter_client.post_tweet.return_value = "tweet_123"
    
    tweet = Tweet(
        id=uuid.uuid4(),
        client_id=test_client.id,
        tweet_text="Test tweet",
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    mock_db.create_tweet.return_value = tweet
    
    # Process client
    await scheduler._process_client(test_context)
    
    # Verify tweet was created and posted
    mock_db.create_tweet.assert_called_once()
    mock_twitter_client.post_tweet.assert_called_once_with("Test tweet")
    
    # Verify updates
    mock_db.update_tweet.assert_called_once()
    mock_db.update_client.assert_called_once()
    assert test_context.last_tweet_at is not None

@pytest.mark.asyncio
async def test_process_client_rate_limit(
    scheduler, test_client, test_context, mock_db, mock_twitter_client
):
    """Test client processing with rate limit error."""
    # Setup mocks
    mock_db.get_client.return_value = test_client
    reset_time = datetime.now(timezone.utc)
    mock_twitter_client.post_tweet.side_effect = [
        TwitterRateLimitError(reset_time),
        "tweet_123"
    ]
    
    tweet = Tweet(
        id=uuid.uuid4(),
        client_id=test_client.id,
        tweet_text="Test tweet",
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    mock_db.create_tweet.return_value = tweet
    
    # Process client
    await scheduler._process_client(test_context)
    
    # Verify retries
    assert mock_twitter_client.post_tweet.call_count == 2
    assert mock_db.update_tweet.call_count == 2  # One failure, one success

@pytest.mark.asyncio
async def test_process_client_error(
    scheduler, test_client, test_context, mock_db, mock_twitter_client
):
    """Test client processing with error."""
    # Setup mocks
    mock_db.get_client.return_value = test_client
    mock_twitter_client.post_tweet.side_effect = TwitterError("API error")
    
    tweet = Tweet(
        id=uuid.uuid4(),
        client_id=test_client.id,
        tweet_text="Test tweet",
        status="pending",
        created_at=datetime.now(timezone.utc)
    )
    mock_db.create_tweet.return_value = tweet
    
    # Process client
    await scheduler._process_client(test_context)
    
    # Verify retries and failure
    assert mock_twitter_client.post_tweet.call_count == scheduler.config.max_retries
    mock_db.update_tweet.assert_called_with(
        tweet.id,
        {
            "status": "failed",
            "error_message": "API error"
        }
    )

@pytest.mark.asyncio
async def test_scheduler_batch_processing(scheduler, test_context, mock_client_manager):
    """Test batch processing of clients."""
    # Setup multiple clients
    clients = [test_context] * 7  # 7 clients (more than batch_size)
    mock_client_manager.get_clients_due_for_tweet.return_value = clients
    
    # Start scheduler
    await scheduler.start()
    
    # Let it run for a short time
    await asyncio.sleep(2)
    
    # Stop scheduler
    await scheduler.stop()
    
    # Verify batching
    mock_client_manager.get_clients_due_for_tweet.assert_called()
    # Should have processed all clients in two batches (5 + 2) 