"""Tests for Twitter client implementation."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
import tweepy
from clara_engine.twitter.real_client import RealTwitterClient, TwitterConfig
from clara_engine.twitter.client import TwitterError, TwitterRateLimitError

@pytest.fixture
def config():
    """Create test configuration."""
    return TwitterConfig(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_secret="test_secret"
    )

@pytest.fixture
def mock_tweepy_client():
    """Create mock Tweepy client."""
    client = Mock(spec=tweepy.Client)
    client.get_me = Mock()
    client.create_tweet = Mock()
    client.get_tweet = Mock()
    return client

@pytest.fixture
def mock_tweepy_api():
    """Create mock Tweepy API."""
    api = Mock(spec=tweepy.API)
    api.media_upload = Mock()
    return api

@pytest.fixture
def client(config, mock_tweepy_client):
    """Create Twitter client with mocks."""
    with patch("tweepy.Client", return_value=mock_tweepy_client):
        client = RealTwitterClient(config)
        return client

@pytest.mark.asyncio
async def test_initialization_success(config):
    """Test successful client initialization."""
    with patch("tweepy.Client") as mock_client:
        instance = mock_client.return_value
        instance.get_me.return_value = {"data": {"id": "123"}}
        
        client = RealTwitterClient(config)
        assert client.config == config
        assert client.client == instance
        
        instance.get_me.assert_called_once()

@pytest.mark.asyncio
async def test_initialization_failure(config):
    """Test client initialization failure."""
    with patch("tweepy.Client") as mock_client:
        instance = mock_client.return_value
        instance.get_me.side_effect = tweepy.TweepyException("Auth failed")
        
        with pytest.raises(TwitterError) as exc_info:
            RealTwitterClient(config)
        
        assert "Auth failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_post_tweet_success(client, mock_tweepy_client):
    """Test successful tweet posting."""
    mock_tweepy_client.create_tweet.return_value = Mock(
        data={"id": "123456789"}
    )
    
    tweet_id = await client.post_tweet("Test tweet")
    assert tweet_id == "123456789"
    
    mock_tweepy_client.create_tweet.assert_called_once_with(
        text="Test tweet"
    )

@pytest.mark.asyncio
async def test_post_tweet_rate_limit(client, mock_tweepy_client):
    """Test tweet posting with rate limit error."""
    mock_response = Mock()
    mock_response.headers = {"x-rate-limit-reset": "1735689600"}  # Some future timestamp
    
    mock_tweepy_client.create_tweet.side_effect = tweepy.TooManyRequests(response=mock_response)
    
    with pytest.raises(TwitterRateLimitError) as exc_info:
        await client.post_tweet("Test tweet")
    
    assert exc_info.value.reset_at == datetime.fromtimestamp(1735689600)

@pytest.mark.asyncio
async def test_post_tweet_error(client, mock_tweepy_client):
    """Test tweet posting with general error."""
    mock_tweepy_client.create_tweet.side_effect = tweepy.TweepyException("API error")
    
    with pytest.raises(TwitterError) as exc_info:
        await client.post_tweet("Test tweet")
    
    assert "API error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_media_upload_success(client, mock_tweepy_api):
    """Test successful media upload."""
    with patch("tweepy.OAuth1UserHandler"), \
         patch("tweepy.API", return_value=mock_tweepy_api):
        
        mock_media = Mock()
        mock_media.media_id = "789012"
        mock_tweepy_api.media_upload.return_value = mock_media
        
        media_id = await client.media_upload("test.jpg")
        assert media_id == "789012"
        
        mock_tweepy_api.media_upload.assert_called_once_with(
            filename="test.jpg"
        )

@pytest.mark.asyncio
async def test_media_upload_error(client, mock_tweepy_api):
    """Test media upload with error."""
    with patch("tweepy.OAuth1UserHandler"), \
         patch("tweepy.API", return_value=mock_tweepy_api):
        
        mock_tweepy_api.media_upload.side_effect = tweepy.TweepyException("Upload failed")
        
        with pytest.raises(TwitterError) as exc_info:
            await client.media_upload("test.jpg")
        
        assert "Upload failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_get_tweet_success(client, mock_tweepy_client):
    """Test successful tweet retrieval."""
    mock_tweet = Mock()
    mock_tweet.id = 123456789
    mock_tweet.text = "Test tweet"
    mock_tweet.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    mock_response = Mock()
    mock_response.data = mock_tweet
    mock_response.includes = {"media": [Mock(id="987654")]}
    
    mock_tweepy_client.get_tweet.return_value = mock_response
    
    tweet = await client.get_tweet("123456789")
    assert tweet is not None
    assert tweet.id == "123456789"
    assert tweet.text == "Test tweet"
    assert tweet.created_at == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert tweet.media_ids == ["987654"]

@pytest.mark.asyncio
async def test_get_tweet_not_found(client, mock_tweepy_client):
    """Test tweet retrieval when tweet not found."""
    mock_response = Mock()
    mock_response.data = None
    
    mock_tweepy_client.get_tweet.return_value = mock_response
    
    tweet = await client.get_tweet("123456789")
    assert tweet is None

@pytest.mark.asyncio
async def test_get_tweet_error(client, mock_tweepy_client):
    """Test tweet retrieval with error."""
    mock_tweepy_client.get_tweet.side_effect = tweepy.TweepyException("Not found")
    
    with pytest.raises(TwitterError) as exc_info:
        await client.get_tweet("123456789")
    
    assert "Not found" in str(exc_info.value) 