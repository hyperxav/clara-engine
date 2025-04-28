"""Rate limiting middleware using FastAPI-Limiter."""

import os
from typing import Callable
from fastapi import FastAPI, Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import aioredis
import structlog

logger = structlog.get_logger()

async def setup_limiter(app: FastAPI):
    """Set up rate limiting with Redis.
    
    Args:
        app: The FastAPI application instance
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        redis = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        await FastAPILimiter.init(redis)
        logger.info("Rate limiter initialized", redis_url=redis_url)
    except Exception as e:
        logger.error("Failed to initialize rate limiter", error=str(e))
        raise

def rate_limit() -> Callable:
    """Create rate limit dependency.
    
    Returns:
        Rate limiter dependency for routes
    """
    return RateLimiter(
        times=60,  # Number of requests
        minutes=1,  # Time window
        key_func=lambda r: r.state.client_id  # Use client_id from auth
    )

# Export rate limit dependency
limiter = rate_limit() 