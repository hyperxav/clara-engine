"""Database models for Clara Engine."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
import pytz


class ClientBase(BaseModel):
    """Base model for client configuration."""

    name: str
    persona_prompt: str
    twitter_key: str
    twitter_secret: str
    access_token: str
    access_secret: str
    posting_hours: List[int] = Field(default_factory=list)
    timezone: str = "UTC"
    vector_index_name: Optional[str] = None
    active: bool = True

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate that the timezone is valid."""
        if v not in pytz.all_timezones:
            raise ValueError("Invalid timezone")
        return v

    @field_validator("posting_hours")
    @classmethod
    def validate_posting_hours(cls, v: List[int]) -> List[int]:
        """Validate posting hours are between 0 and 23."""
        if not all(0 <= hour <= 23 for hour in v):
            raise ValueError("Posting hours must be between 0 and 23")
        return v


class ClientCreate(ClientBase):
    """Model for creating a new client."""

    pass


class ClientUpdate(BaseModel):
    """Model for updating an existing client."""

    name: Optional[str] = None
    persona_prompt: Optional[str] = None
    twitter_key: Optional[str] = None
    twitter_secret: Optional[str] = None
    access_token: Optional[str] = None
    access_secret: Optional[str] = None
    posting_hours: Optional[List[int]] = None
    timezone: Optional[str] = None
    vector_index_name: Optional[str] = None
    active: Optional[bool] = None


class Client(ClientBase):
    """Model for a client with all fields."""

    id: UUID = Field(default_factory=uuid4)
    last_posted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class TweetBase(BaseModel):
    """Base model for tweets."""

    tweet_text: str
    client_id: UUID
    tweet_url: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate tweet status."""
        if v not in ["pending", "posted", "failed"]:
            raise ValueError("Invalid status")
        return v


class TweetCreate(TweetBase):
    """Model for creating a new tweet."""

    pass


class TweetUpdate(BaseModel):
    """Model for updating an existing tweet."""

    tweet_url: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None


class Tweet(TweetBase):
    """Model for a tweet with all fields."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime
    posted_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    } 