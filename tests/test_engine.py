"""Tests for Clara Engine."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
import signal

from clara_engine.core.engine import ClaraEngine, EngineConfig, EngineStatus

@pytest.fixture
def mock_db():
    """Create mock database."""
    return Mock()

@pytest.fixture
def mock_client_manager():
    """Create mock client manager."""
    manager = Mock()
    manager.initialize = AsyncMock()
    manager.close = AsyncMock()
    manager.get_active_clients = Mock(return_value=[])
    return manager

@pytest.fixture
def mock_rate_limiter():
    """Create mock rate limiter."""
    limiter = Mock()
    limiter.initialize = AsyncMock()
    limiter.close = AsyncMock()
    limiter.check_limit = AsyncMock()
    return limiter

@pytest.fixture
def mock_scheduler():
    """Create mock scheduler."""
    scheduler = Mock()
    scheduler.start = AsyncMock()
    scheduler.stop = AsyncMock()
    return scheduler

@pytest.fixture
def engine(mock_db, mock_client_manager, mock_rate_limiter, mock_scheduler):
    """Create engine instance with mocks."""
    with patch("clara_engine.core.engine.Database", return_value=mock_db), \
         patch("clara_engine.core.engine.ClientManager", return_value=mock_client_manager), \
         patch("clara_engine.core.engine.RedisRateLimiter", return_value=mock_rate_limiter), \
         patch("clara_engine.core.engine.TweetScheduler", return_value=mock_scheduler):
        
        config = EngineConfig(
            redis_url="redis://localhost:6379/1",
            shutdown_timeout=1.0
        )
        return ClaraEngine(config)

@pytest.mark.asyncio
async def test_engine_initialization(engine):
    """Test engine initialization."""
    assert isinstance(engine.config, EngineConfig)
    assert isinstance(engine.status, EngineStatus)
    assert not engine.status.running
    assert not engine.status.scheduler_running
    assert engine.status.active_clients == 0

@pytest.mark.asyncio
async def test_engine_start(engine, mock_rate_limiter, mock_client_manager, mock_scheduler):
    """Test engine startup."""
    # Create task to start engine
    start_task = asyncio.create_task(engine.start())
    
    # Give it time to initialize
    await asyncio.sleep(0.1)
    
    # Verify components initialized
    mock_rate_limiter.initialize.assert_called_once()
    mock_client_manager.initialize.assert_called_once()
    mock_scheduler.start.assert_called_once()
    
    assert engine.status.running
    assert engine.status.scheduler_running
    assert "rate_limiter" in engine.status.components_healthy
    assert "client_manager" in engine.status.components_healthy
    assert "scheduler" in engine.status.components_healthy
    
    # Trigger shutdown
    await engine.shutdown()
    await start_task

@pytest.mark.asyncio
async def test_engine_shutdown(engine, mock_scheduler, mock_rate_limiter, mock_client_manager):
    """Test engine shutdown."""
    # Start engine
    start_task = asyncio.create_task(engine.start())
    await asyncio.sleep(0.1)
    
    # Shutdown
    await engine.shutdown()
    
    # Verify components stopped
    mock_scheduler.stop.assert_called_once()
    mock_rate_limiter.close.assert_called_once()
    mock_client_manager.close.assert_called_once()
    
    assert not engine.status.running
    assert not engine.status.scheduler_running
    
    await start_task

@pytest.mark.asyncio
async def test_signal_handling(engine):
    """Test signal handling."""
    # Start engine
    start_task = asyncio.create_task(engine.start())
    await asyncio.sleep(0.1)
    
    # Simulate SIGTERM
    engine._signal_handler(signal.SIGTERM, None)
    await asyncio.sleep(0.1)
    
    assert not engine.status.running
    await start_task

@pytest.mark.asyncio
async def test_health_check(engine, mock_client_manager, mock_rate_limiter):
    """Test health check functionality."""
    # Setup mocks
    mock_client_manager.get_active_clients.return_value = ["client1", "client2"]
    mock_rate_limiter.check_limit.return_value.is_limited = False
    mock_rate_limiter.check_limit.return_value.remaining_tokens = 100
    
    # Start engine
    start_task = asyncio.create_task(engine.start())
    await asyncio.sleep(0.1)
    
    # Perform health check
    status = await engine.health_check()
    
    assert status.active_clients == 2
    assert status.components_healthy["rate_limiter"]
    assert status.metrics["rate_limit_remaining"] == 100
    assert status.metrics["scheduler_running"] is True
    
    await engine.shutdown()
    await start_task

@pytest.mark.asyncio
async def test_startup_failure(engine, mock_rate_limiter):
    """Test engine startup failure handling."""
    # Make rate limiter fail
    mock_rate_limiter.initialize.side_effect = Exception("Failed to connect")
    
    with pytest.raises(Exception) as exc_info:
        await engine.start()
    
    assert "Failed to connect" in str(exc_info.value)
    assert not engine.status.running

@pytest.mark.asyncio
async def test_shutdown_timeout(engine, mock_scheduler):
    """Test shutdown timeout handling."""
    # Make scheduler stop hang
    mock_scheduler.stop.side_effect = asyncio.sleep(2.0)
    
    # Start engine
    start_task = asyncio.create_task(engine.start())
    await asyncio.sleep(0.1)
    
    # Shutdown should timeout
    await engine.shutdown()
    
    assert not engine.status.running
    mock_scheduler.stop.assert_called_once()
    
    await start_task

@pytest.mark.asyncio
async def test_health_check_failure(engine, mock_client_manager):
    """Test health check failure handling."""
    # Make client manager fail
    mock_client_manager.get_active_clients.side_effect = Exception("Database error")
    
    # Start engine
    start_task = asyncio.create_task(engine.start())
    await asyncio.sleep(0.1)
    
    # Health check should handle error
    status = await engine.health_check()
    assert not status.components_healthy.get("health_check")
    
    await engine.shutdown()
    await start_task 