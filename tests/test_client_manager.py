"""Tests for client manager."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
import uuid
import pytz

from clara_engine.clients.manager import ClientManager, ClientContext
from clara_engine.models import Client as ClientModel
from clara_engine.twitter.real_client import RealTwitterClient
from clara_engine.openai.client import OpenAIClient
from clara_engine.openai.prompts import PromptManager
from clara_engine.openai.validators import ResponseValidator

@pytest.fixture
def mock_db():
    """Create mock database."""
    db = Mock()
    db.get_active_clients = Mock()
    db.get_client = Mock()
    return db

@pytest.fixture
def mock_twitter_client():
    """Create mock Twitter client."""
    return Mock(spec=RealTwitterClient)

@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    client = Mock(spec=OpenAIClient)
    client.initialize = AsyncMock()
    client.close = AsyncMock()
    return client

@pytest.fixture
def mock_prompt_manager():
    """Create mock prompt manager."""
    return Mock(spec=PromptManager)

@pytest.fixture
def mock_validator():
    """Create mock validator."""
    return Mock(spec=ResponseValidator)

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
async def manager(mock_db):
    """Create client manager."""
    return ClientManager(mock_db)

@pytest.mark.asyncio
async def test_initialization(manager, mock_db, test_client):
    """Test manager initialization."""
    mock_db.get_active_clients.return_value = [test_client]
    
    with patch("clara_engine.clients.manager.RealTwitterClient"), \
         patch("clara_engine.clients.manager.OpenAIClient"), \
         patch("clara_engine.clients.manager.PromptManager"), \
         patch("clara_engine.clients.manager.ResponseValidator"):
        
        await manager.initialize()
        
        mock_db.get_active_clients.assert_called_once()
        assert len(manager._clients) == 1

@pytest.mark.asyncio
async def test_add_client(
    manager, test_client, mock_twitter_client,
    mock_openai_client, mock_prompt_manager, mock_validator
):
    """Test adding a client."""
    with patch("clara_engine.clients.manager.RealTwitterClient",
              return_value=mock_twitter_client), \
         patch("clara_engine.clients.manager.OpenAIClient",
               return_value=mock_openai_client), \
         patch("clara_engine.clients.manager.PromptManager",
               return_value=mock_prompt_manager), \
         patch("clara_engine.clients.manager.ResponseValidator",
               return_value=mock_validator):
        
        await manager.add_client(test_client)
        
        assert str(test_client.id) in manager._clients
        context = manager._clients[str(test_client.id)]
        assert isinstance(context, ClientContext)
        assert context.client_id == str(test_client.id)
        assert context.active == test_client.active
        
        mock_openai_client.initialize.assert_called_once()

@pytest.mark.asyncio
async def test_remove_client(manager, test_client, mock_openai_client):
    """Test removing a client."""
    # Add a test client first
    client_id = str(test_client.id)
    context = ClientContext(
        client_id=client_id,
        twitter_client=Mock(),
        openai_client=mock_openai_client,
        prompt_manager=Mock(),
        validator=Mock(),
        active=True
    )
    manager._clients[client_id] = context
    
    # Remove the client
    await manager.remove_client(client_id)
    
    assert client_id not in manager._clients
    mock_openai_client.close.assert_called_once()

def test_get_client(manager, test_client):
    """Test getting a client by ID."""
    client_id = str(test_client.id)
    context = ClientContext(
        client_id=client_id,
        twitter_client=Mock(),
        openai_client=Mock(),
        prompt_manager=Mock(),
        validator=Mock(),
        active=True
    )
    manager._clients[client_id] = context
    
    result = manager.get_client(client_id)
    assert result == context

def test_get_active_clients(manager):
    """Test getting active clients."""
    # Add mix of active and inactive clients
    contexts = {
        "active1": ClientContext(
            client_id="active1",
            twitter_client=Mock(),
            openai_client=Mock(),
            prompt_manager=Mock(),
            validator=Mock(),
            active=True
        ),
        "active2": ClientContext(
            client_id="active2",
            twitter_client=Mock(),
            openai_client=Mock(),
            prompt_manager=Mock(),
            validator=Mock(),
            active=True
        ),
        "inactive": ClientContext(
            client_id="inactive",
            twitter_client=Mock(),
            openai_client=Mock(),
            prompt_manager=Mock(),
            validator=Mock(),
            active=False
        )
    }
    manager._clients = contexts
    
    active = manager.get_active_clients()
    assert len(active) == 2
    assert all(c.active for c in active)

def test_get_clients_due_for_tweet(manager, mock_db, test_client):
    """Test getting clients due for tweets."""
    client_id = str(test_client.id)
    
    # Mock current time to 9:00 UTC (in client's posting schedule)
    current_time = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
    
    with patch("clara_engine.clients.manager.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = current_time
        
        # Setup test client
        context = ClientContext(
            client_id=client_id,
            twitter_client=Mock(),
            openai_client=Mock(),
            prompt_manager=Mock(),
            validator=Mock(),
            active=True,
            last_tweet_at=None  # No previous tweet
        )
        manager._clients[client_id] = context
        
        # Mock database response
        mock_db.get_client.return_value = test_client
        
        # Get due clients
        due_clients = manager.get_clients_due_for_tweet()
        assert len(due_clients) == 1
        assert due_clients[0].client_id == client_id

@pytest.mark.asyncio
async def test_close(manager, mock_openai_client):
    """Test closing all clients."""
    # Add some test clients
    contexts = {
        "client1": ClientContext(
            client_id="client1",
            twitter_client=Mock(),
            openai_client=mock_openai_client,
            prompt_manager=Mock(),
            validator=Mock(),
            active=True
        ),
        "client2": ClientContext(
            client_id="client2",
            twitter_client=Mock(),
            openai_client=mock_openai_client,
            prompt_manager=Mock(),
            validator=Mock(),
            active=True
        )
    }
    manager._clients = contexts
    
    await manager.close()
    
    assert len(manager._clients) == 0
    assert mock_openai_client.close.call_count == 2 