"""Tests for configuration routes."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from clara_engine.api.models.api import EngineState, StatusResponse, ConfigUpdate
from clara_engine.core.engine import ClaraEngine
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.fixture
def mock_engine():
    """Create a mock engine instance."""
    engine = MagicMock(spec=ClaraEngine)
    engine.state = EngineState.RUNNING
    engine.start_time = datetime.now(timezone.utc)
    engine.get_component_health.return_value = {
        "scheduler": {
            "status": True,
            "message": "Healthy",
            "last_check": datetime.now(timezone.utc).isoformat()
        }
    }
    engine.get_rate_limits.return_value = {
        "twitter": 100.0,
        "openai": 200.0
    }
    engine.client_manager.get_active_clients.return_value = [MagicMock()]
    return engine

@pytest.fixture
def test_client(mock_engine):
    """Create a test client with mocked dependencies."""
    from clara_engine.api.app import app
    app.state.engine = mock_engine
    return TestClient(app)

async def test_get_status(test_client, mock_engine):
    """Test getting engine status."""
    response = test_client.get("/config/status")
    assert response.status_code == 200
    
    data = response.json()
    assert data["state"] == EngineState.RUNNING
    assert isinstance(data["uptime"], float)
    assert data["active_clients"] == 1
    assert "scheduler" in data["component_health"]
    assert "twitter" in data["rate_limits"]
    assert "openai" in data["rate_limits"]

async def test_get_status_error(test_client, mock_engine):
    """Test getting status when engine raises an error."""
    mock_engine.get_component_health.side_effect = Exception("Test error")
    
    response = test_client.get("/config/status")
    assert response.status_code == 500
    assert "error" in response.json()

async def test_update_config(test_client, mock_engine):
    """Test updating client configuration."""
    config_update = {
        "client_id": "test-client",
        "tweet_interval": 3600,
        "max_tweets_per_day": 24,
        "active": True,
        "prompt_config": {"temperature": 0.7},
        "metadata": {"category": "tech"}
    }
    
    response = test_client.put("/config/update", json=config_update)
    assert response.status_code == 200
    
    mock_engine.client_manager.update_client_config.assert_called_once_with(
        client_id="test-client",
        tweet_interval=3600,
        max_tweets_per_day=24,
        active=True,
        prompt_config={"temperature": 0.7},
        metadata={"category": "tech"}
    )

async def test_update_config_invalid_client(test_client, mock_engine):
    """Test updating config for non-existent client."""
    mock_engine.client_manager.update_client_config.side_effect = ValueError("Client not found")
    
    config_update = {
        "client_id": "invalid-client",
        "tweet_interval": 3600
    }
    
    response = test_client.put("/config/update", json=config_update)
    assert response.status_code == 404
    assert "error" in response.json()

async def test_update_config_validation_error(test_client):
    """Test updating config with invalid data."""
    config_update = {
        "client_id": "test-client",
        "tweet_interval": -1  # Invalid value
    }
    
    response = test_client.put("/config/update", json=config_update)
    assert response.status_code == 422  # Validation error 