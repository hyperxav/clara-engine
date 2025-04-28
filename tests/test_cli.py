"""Tests for Clara Engine CLI."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from click.testing import CliRunner
from clara_engine.cli import cli
from clara_engine.models import Client, Tweet
from datetime import datetime, timezone
import uuid

@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()

@pytest.fixture
def mock_engine():
    """Create mock engine."""
    engine = Mock()
    engine.start = AsyncMock()
    engine.shutdown = AsyncMock()
    engine.health_check = AsyncMock()
    return engine

@pytest.fixture
def mock_db():
    """Create mock database."""
    db = Mock()
    db.get_active_clients = Mock()
    db.get_all_clients = Mock()
    db.create_client = Mock()
    db.update_client = Mock()
    db.delete_client = Mock()
    return db

def test_cli_help(runner):
    """Test CLI help output."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Clara Engine - Multi-tenant AI Twitter Bot Platform" in result.output

def test_cli_debug_flag(runner):
    """Test debug flag configuration."""
    with patch("structlog.configure") as mock_configure:
        result = runner.invoke(cli, ["--debug"])
        assert result.exit_code == 0
        mock_configure.assert_called_once()

def test_start_command(runner, mock_engine):
    """Test start command with default options."""
    with patch("clara_engine.cli.ClaraEngine", return_value=mock_engine):
        result = runner.invoke(cli, ["start"])
        assert result.exit_code == 0
        mock_engine.start.assert_called_once()

def test_start_command_with_options(runner, mock_engine):
    """Test start command with custom options."""
    with patch("clara_engine.cli.ClaraEngine", return_value=mock_engine):
        result = runner.invoke(cli, [
            "start",
            "--redis-url", "redis://custom:6379/1",
            "--check-interval", "30",
            "--batch-size", "5"
        ])
        assert result.exit_code == 0
        mock_engine.start.assert_called_once()

def test_start_command_keyboard_interrupt(runner, mock_engine):
    """Test graceful shutdown on keyboard interrupt."""
    mock_engine.start = AsyncMock(side_effect=KeyboardInterrupt)
    
    with patch("clara_engine.cli.ClaraEngine", return_value=mock_engine):
        result = runner.invoke(cli, ["start"])
        assert result.exit_code == 0
        mock_engine.shutdown.assert_called_once()

def test_list_clients_command(runner, mock_db):
    """Test listing clients."""
    # Create test clients
    clients = [
        Client(
            id=uuid.uuid4(),
            name="Test Client 1",
            persona_prompt="Test persona",
            twitter_key="key1",
            twitter_secret="secret1",
            access_token="token1",
            access_secret="secret1",
            posting_hours=[9, 15, 21],
            timezone="UTC",
            active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        Client(
            id=uuid.uuid4(),
            name="Test Client 2",
            persona_prompt="Test persona",
            twitter_key="key2",
            twitter_secret="secret2",
            access_token="token2",
            access_secret="secret2",
            posting_hours=[10, 16, 22],
            timezone="America/New_York",
            active=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    ]
    
    mock_db.get_active_clients.return_value = [c for c in clients if c.active]
    mock_db.get_all_clients.return_value = clients
    
    with patch("clara_engine.cli.Database", return_value=mock_db):
        # Test active-only (default)
        result = runner.invoke(cli, ["client", "list"])
        assert result.exit_code == 0
        assert "Test Client 1" in result.output
        assert "Test Client 2" not in result.output
        
        # Test all clients
        result = runner.invoke(cli, ["client", "list", "--all"])
        assert result.exit_code == 0
        assert "Test Client 1" in result.output
        assert "Test Client 2" in result.output

def test_add_client_command(runner, mock_db):
    """Test adding a new client."""
    test_client = Client(
        id=uuid.uuid4(),
        name="New Client",
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
    mock_db.create_client.return_value = test_client
    
    with patch("clara_engine.cli.Database", return_value=mock_db):
        result = runner.invoke(cli, [
            "client", "add",
            "New Client",
            "--persona", "Test persona",
            "--twitter-key", "key",
            "--twitter-secret", "secret",
            "--access-token", "token",
            "--access-secret", "secret",
            "--timezone", "UTC",
            "--posting-hours", "9,15,21"
        ])
        assert result.exit_code == 0
        assert "Successfully created client" in result.output
        mock_db.create_client.assert_called_once()

def test_update_client_command(runner, mock_db):
    """Test updating a client."""
    test_client = Client(
        id=uuid.uuid4(),
        name="Updated Client",
        persona_prompt="Updated persona",
        twitter_key="key",
        twitter_secret="secret",
        access_token="token",
        access_secret="secret",
        posting_hours=[10, 16, 22],
        timezone="America/New_York",
        active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_db.update_client.return_value = test_client
    
    with patch("clara_engine.cli.Database", return_value=mock_db):
        result = runner.invoke(cli, [
            "client", "update",
            str(test_client.id),
            "--name", "Updated Client",
            "--persona", "Updated persona",
            "--timezone", "America/New_York",
            "--posting-hours", "10,16,22",
            "--active"
        ])
        assert result.exit_code == 0
        assert "Successfully updated client" in result.output
        mock_db.update_client.assert_called_once()

def test_remove_client_command_with_confirmation(runner, mock_db):
    """Test removing a client with confirmation."""
    mock_db.delete_client.return_value = True
    
    with patch("clara_engine.cli.Database", return_value=mock_db):
        result = runner.invoke(cli, ["client", "remove", "test-id"], input="y\n")
        assert result.exit_code == 0
        assert "Successfully removed client" in result.output
        mock_db.delete_client.assert_called_once_with("test-id")

def test_remove_client_command_cancelled(runner, mock_db):
    """Test cancelling client removal."""
    with patch("clara_engine.cli.Database", return_value=mock_db):
        result = runner.invoke(cli, ["client", "remove", "test-id"], input="n\n")
        assert result.exit_code == 0
        assert "Operation cancelled" in result.output
        mock_db.delete_client.assert_not_called()

def test_status_command(runner, mock_engine):
    """Test status command."""
    mock_engine.health_check.return_value.running = True
    mock_engine.health_check.return_value.scheduler_running = True
    mock_engine.health_check.return_value.active_clients = 2
    mock_engine.health_check.return_value.components_healthy = {
        "scheduler": True,
        "database": True
    }
    mock_engine.health_check.return_value.metrics = {
        "tweets_sent": 100,
        "errors": 0
    }
    
    with patch("clara_engine.cli.ClaraEngine", return_value=mock_engine):
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "Clara Engine Status" in result.output
        assert "Running: ✓" in result.output
        assert "Active Clients: 2" in result.output 