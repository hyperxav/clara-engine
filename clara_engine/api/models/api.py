"""API models for request/response validation."""

from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, conlist
from enum import Enum

class Tweet(BaseModel):
    """Tweet model for API responses."""
    id: str = Field(..., description="Tweet ID")
    text: str = Field(..., description="Tweet text")
    status: str = Field(..., description="Tweet status (pending/posted/failed)")
    created_at: datetime = Field(..., description="Creation timestamp")
    posted_at: Optional[datetime] = Field(None, description="Posting timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class TweetList(BaseModel):
    """List of tweets response."""
    tweets: List[Tweet] = Field(..., description="List of tweets")
    total: int = Field(..., description="Total number of tweets")

class EngineState(str, Enum):
    """Possible states of the engine."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"

class ComponentHealth(BaseModel):
    """Health status of a component."""
    status: bool = Field(..., description="Whether the component is healthy")
    message: Optional[str] = Field(None, description="Optional message about component health")
    last_check: str = Field(..., description="ISO timestamp of last health check")

class StatusResponse(BaseModel):
    """Response model for engine status."""
    state: EngineState = Field(..., description="Current state of the engine")
    uptime: float = Field(..., description="Engine uptime in seconds")
    active_clients: int = Field(..., description="Number of active clients")
    component_health: Dict[str, ComponentHealth] = Field(
        ..., 
        description="Health status of each component"
    )
    rate_limits: Dict[str, float] = Field(
        ..., 
        description="Current rate limits for various operations"
    )

class ConfigUpdate(BaseModel):
    """Model for updating client configuration."""
    client_id: str = Field(..., description="ID of the client to update")
    tweet_interval: Optional[int] = Field(
        None, 
        description="Interval between tweets in seconds",
        gt=0
    )
    max_tweets_per_day: Optional[int] = Field(
        None,
        description="Maximum number of tweets per day",
        gt=0
    )
    active: Optional[bool] = Field(
        None,
        description="Whether the client is active"
    )
    prompt_config: Optional[Dict] = Field(
        None,
        description="Configuration for tweet generation prompts"
    )
    metadata: Optional[Dict] = Field(
        None,
        description="Additional metadata for the client"
    )

class RateLimitInfo(BaseModel):
    """Rate limit information."""
    remaining: int = Field(..., description="Remaining requests in window")
    reset_at: datetime = Field(..., description="Window reset timestamp")
    total: int = Field(60, description="Total requests allowed per window") 