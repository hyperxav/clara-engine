"""Rate limiting implementation for OpenAI API requests."""

import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import aioredis
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)

class RateLimitConfig(BaseModel):
    """Configuration for rate limiting."""
    requests_per_second: float = Field(default=1.0, description="Maximum requests per second")
    daily_limit: int = Field(default=50, description="Maximum requests per day")
    burst_size: int = Field(default=5, description="Maximum burst size for token bucket")
    key_prefix: str = Field(default="openai", description="Redis key prefix")

class RateLimitInfo(BaseModel):
    """Information about current rate limit status."""
    remaining_tokens: float
    remaining_daily: int
    reset_at: datetime
    window_start: datetime
    is_limited: bool = False
    retry_after: Optional[float] = None

class RedisRateLimiter:
    """Redis-based rate limiter using token bucket algorithm."""

    def __init__(
        self,
        redis_url: str,
        config: Optional[RateLimitConfig] = None
    ) -> None:
        """Initialize the rate limiter.
        
        Args:
            redis_url: Redis connection URL
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        self.redis = aioredis.from_url(redis_url)
        self._script_loaded = False
        self._lua_script = """
        local key = KEYS[1]
        local daily_key = KEYS[2]
        local now = tonumber(ARGV[1])
        local rate = tonumber(ARGV[2])
        local burst = tonumber(ARGV[3])
        local daily_limit = tonumber(ARGV[4])
        local window_size = 86400  -- 24 hours in seconds

        -- Get current bucket state
        local bucket = redis.call('hmget', key, 'tokens', 'last_update')
        local tokens = tonumber(bucket[1] or burst)
        local last_update = tonumber(bucket[2] or 0)

        -- Calculate token replenishment
        local delta = math.max(0, now - last_update)
        local new_tokens = math.min(burst, tokens + (delta * rate))

        -- Check daily limit
        local daily_count = tonumber(redis.call('get', daily_key) or 0)
        if daily_count >= daily_limit then
            return {new_tokens, daily_count, 0}  -- Daily limit exceeded
        end

        -- Try to consume a token
        if new_tokens >= 1 then
            -- Update bucket
            redis.call('hmset', key, 'tokens', new_tokens - 1, 'last_update', now)
            -- Increment daily counter
            redis.call('incr', daily_key)
            -- Set TTL for daily counter if new
            if daily_count == 0 then
                local window_start = math.floor(now / window_size) * window_size
                local ttl = window_start + window_size - now
                redis.call('expire', daily_key, math.ceil(ttl))
            end
            return {new_tokens - 1, daily_count + 1, 1}  -- Success
        end

        return {new_tokens, daily_count, 0}  -- Rate limited
        """
        
        logger.info(
            "Initialized rate limiter",
            rate=self.config.requests_per_second,
            daily_limit=self.config.daily_limit,
            burst_size=self.config.burst_size
        )

    async def _load_script(self) -> None:
        """Load the Lua script into Redis."""
        if not self._script_loaded:
            self._script_sha = await self.redis.script_load(self._lua_script)
            self._script_loaded = True

    def _get_keys(self, client_id: str) -> tuple[str, str]:
        """Get Redis keys for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Tuple of (bucket_key, daily_key)
        """
        prefix = self.config.key_prefix
        return (
            f"{prefix}:bucket:{client_id}",
            f"{prefix}:daily:{client_id}"
        )

    async def check_limit(self, client_id: str) -> RateLimitInfo:
        """Check if a request would be rate limited.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Rate limit information
        """
        now = time.time()
        bucket_key, daily_key = self._get_keys(client_id)
        
        # Ensure script is loaded
        await self._load_script()
        
        # Run rate limiting script
        tokens, daily_count, allowed = await self.redis.evalsha(
            self._script_sha,
            keys=[bucket_key, daily_key],
            args=[
                now,
                self.config.requests_per_second,
                self.config.burst_size,
                self.config.daily_limit
            ]
        )
        
        # Calculate window info
        window_size = 86400  # 24 hours in seconds
        window_start = datetime.fromtimestamp(
            int(now / window_size) * window_size
        )
        reset_at = window_start + timedelta(days=1)
        
        # Calculate retry after if limited
        retry_after = None
        if allowed == 0:
            if daily_count >= self.config.daily_limit:
                retry_after = (reset_at - datetime.now()).total_seconds()
            else:
                retry_after = (1.0 - tokens) / self.config.requests_per_second
        
        return RateLimitInfo(
            remaining_tokens=tokens,
            remaining_daily=self.config.daily_limit - daily_count,
            reset_at=reset_at,
            window_start=window_start,
            is_limited=allowed == 0,
            retry_after=retry_after
        )

    async def acquire(self, client_id: str) -> RateLimitInfo:
        """Attempt to acquire a rate limit token.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Rate limit information
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        info = await self.check_limit(client_id)
        if info.is_limited:
            logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                retry_after=info.retry_after,
                remaining_daily=info.remaining_daily
            )
            raise RateLimitExceeded(
                f"Rate limit exceeded for client {client_id}",
                retry_after=info.retry_after
            )
        return info

    async def close(self) -> None:
        """Close the Redis connection."""
        await self.redis.close()


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[float] = None) -> None:
        """Initialize the exception.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
        """
        super().__init__(message)
        self.retry_after = retry_after 