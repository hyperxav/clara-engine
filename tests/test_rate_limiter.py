"""Tests for the rate limiter implementation."""

import pytest
import time
from datetime import datetime, timedelta
import aioredis
from clara_engine.openai.rate_limiter import (
    RedisRateLimiter,
    RateLimitConfig,
    RateLimitExceeded
)

# Test configuration
TEST_REDIS_URL = "redis://localhost:6379/1"  # Use DB 1 for testing
TEST_CLIENT_ID = "test_client"


@pytest.fixture
async def redis():
    """Redis connection fixture."""
    client = aioredis.from_url(TEST_REDIS_URL)
    yield client
    await client.close()


@pytest.fixture
async def rate_limiter():
    """Rate limiter fixture with test configuration."""
    config = RateLimitConfig(
        requests_per_second=2.0,  # 2 requests per second
        daily_limit=5,  # 5 requests per day
        burst_size=3,  # Allow burst of 3 requests
        key_prefix="test"
    )
    limiter = RedisRateLimiter(TEST_REDIS_URL, config)
    yield limiter
    await limiter.close()


@pytest.fixture(autouse=True)
async def cleanup(redis):
    """Clean up Redis test database before and after each test."""
    await redis.flushdb()
    yield
    await redis.flushdb()


async def test_init(rate_limiter):
    """Test rate limiter initialization."""
    assert rate_limiter.config.requests_per_second == 2.0
    assert rate_limiter.config.daily_limit == 5
    assert rate_limiter.config.burst_size == 3
    assert rate_limiter.config.key_prefix == "test"


async def test_check_limit_initial(rate_limiter):
    """Test initial rate limit check."""
    info = await rate_limiter.check_limit(TEST_CLIENT_ID)
    assert info.remaining_tokens == rate_limiter.config.burst_size - 1
    assert info.remaining_daily == rate_limiter.config.daily_limit - 1
    assert not info.is_limited
    assert info.retry_after is None


async def test_burst_limit(rate_limiter):
    """Test burst limit enforcement."""
    # Make burst_size + 1 requests
    for i in range(rate_limiter.config.burst_size):
        info = await rate_limiter.check_limit(TEST_CLIENT_ID)
        assert not info.is_limited

    # Next request should be limited
    info = await rate_limiter.check_limit(TEST_CLIENT_ID)
    assert info.is_limited
    assert info.retry_after is not None
    assert 0 < info.retry_after <= 1.0  # Should need to wait up to 1 second


async def test_daily_limit(rate_limiter):
    """Test daily limit enforcement."""
    # Make daily_limit requests
    for i in range(rate_limiter.config.daily_limit):
        info = await rate_limiter.check_limit(TEST_CLIENT_ID)
        assert not info.is_limited

    # Next request should be limited
    info = await rate_limiter.check_limit(TEST_CLIENT_ID)
    assert info.is_limited
    assert info.retry_after > 0
    # Should need to wait until next day
    assert info.retry_after <= 86400  # 24 hours in seconds


async def test_token_replenishment(rate_limiter):
    """Test token replenishment over time."""
    # Use up burst tokens
    for i in range(rate_limiter.config.burst_size):
        await rate_limiter.check_limit(TEST_CLIENT_ID)

    # Wait for 1 token to be replenished
    wait_time = 1.0 / rate_limiter.config.requests_per_second
    time.sleep(wait_time)

    # Should be able to make one more request
    info = await rate_limiter.check_limit(TEST_CLIENT_ID)
    assert not info.is_limited


async def test_acquire_success(rate_limiter):
    """Test successful token acquisition."""
    info = await rate_limiter.acquire(TEST_CLIENT_ID)
    assert not info.is_limited
    assert info.remaining_tokens == rate_limiter.config.burst_size - 1
    assert info.remaining_daily == rate_limiter.config.daily_limit - 1


async def test_acquire_failure(rate_limiter):
    """Test failed token acquisition."""
    # Use up burst tokens
    for i in range(rate_limiter.config.burst_size):
        await rate_limiter.acquire(TEST_CLIENT_ID)

    # Next acquire should raise
    with pytest.raises(RateLimitExceeded) as exc_info:
        await rate_limiter.acquire(TEST_CLIENT_ID)
    
    assert exc_info.value.retry_after is not None
    assert 0 < exc_info.value.retry_after <= 1.0


async def test_multiple_clients(rate_limiter):
    """Test rate limiting for multiple clients."""
    client1 = "client1"
    client2 = "client2"

    # Client 1 uses all burst tokens
    for i in range(rate_limiter.config.burst_size):
        info = await rate_limiter.check_limit(client1)
        assert not info.is_limited

    # Client 2 should still have full tokens
    info = await rate_limiter.check_limit(client2)
    assert not info.is_limited
    assert info.remaining_tokens == rate_limiter.config.burst_size - 1


async def test_window_reset(rate_limiter, redis):
    """Test daily window reset."""
    # Use up some daily limit
    await rate_limiter.check_limit(TEST_CLIENT_ID)
    
    # Manually expire daily counter
    daily_key = f"{rate_limiter.config.key_prefix}:daily:{TEST_CLIENT_ID}"
    await redis.delete(daily_key)
    
    # Should have fresh daily limit
    info = await rate_limiter.check_limit(TEST_CLIENT_ID)
    assert info.remaining_daily == rate_limiter.config.daily_limit - 1 