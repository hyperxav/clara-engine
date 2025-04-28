"""Tests for the database client."""

import uuid
from datetime import datetime, timezone

import pytest
from dotenv import load_dotenv

from clara_engine.db import Database
from clara_engine.models import ClientCreate, TweetCreate

# Load test environment variables
load_dotenv()

@pytest.fixture
def db():
    """Create a database client for testing."""
    return Database()

@pytest.fixture
def client_data():
    """Create test client data."""
    return ClientCreate(
        name="Test Client",
        persona_prompt="A test persona that tweets about testing",
        twitter_key="test_key",
        twitter_secret="test_secret",
        access_token="test_token",
        access_secret="test_secret",
        posting_hours=[9, 15, 21],
        timezone="UTC"
    )

@pytest.fixture
def tweet_data():
    """Create test tweet data."""
    return TweetCreate(
        tweet_text="This is a test tweet",
        client_id=uuid.uuid4(),
        status="pending"
    )

def test_create_client(db, client_data):
    """Test creating a new client."""
    client = db.create_client(client_data)
    assert client.name == client_data.name
    assert client.persona_prompt == client_data.persona_prompt
    assert client.twitter_key == client_data.twitter_key
    assert client.posting_hours == client_data.posting_hours
    assert client.timezone == client_data.timezone
    assert client.active is True
    assert isinstance(client.id, uuid.UUID)
    assert isinstance(client.created_at, datetime)
    assert isinstance(client.updated_at, datetime)

def test_get_client(db, client_data):
    """Test getting a client by ID."""
    created = db.create_client(client_data)
    retrieved = db.get_client(created.id)
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == created.name

def test_get_active_clients(db, client_data):
    """Test getting all active clients."""
    db.create_client(client_data)
    clients = db.get_active_clients()
    assert len(clients) > 0
    assert all(client.active for client in clients)

def test_create_tweet(db, client_data, tweet_data):
    """Test creating a new tweet."""
    client = db.create_client(client_data)
    tweet_data.client_id = client.id
    tweet = db.create_tweet(tweet_data)
    assert tweet.tweet_text == tweet_data.tweet_text
    assert tweet.client_id == client.id
    assert tweet.status == "pending"
    assert isinstance(tweet.id, uuid.UUID)
    assert isinstance(tweet.created_at, datetime)

def test_get_client_tweets(db, client_data, tweet_data):
    """Test getting tweets for a client."""
    client = db.create_client(client_data)
    tweet_data.client_id = client.id
    db.create_tweet(tweet_data)
    tweets = db.get_client_tweets(client.id)
    assert len(tweets) > 0
    assert all(tweet.client_id == client.id for tweet in tweets)

def test_get_pending_tweets(db, client_data, tweet_data):
    """Test getting pending tweets."""
    client = db.create_client(client_data)
    tweet_data.client_id = client.id
    db.create_tweet(tweet_data)
    tweets = db.get_pending_tweets()
    assert len(tweets) > 0
    assert all(tweet.status == "pending" for tweet in tweets) 