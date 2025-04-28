"""Twitter client interface and mock implementation."""

from typing import Protocol, List, Optional
from datetime import datetime
import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

class Tweet(BaseModel):
    """Tweet data model."""
    id: str
    text: str
    created_at: datetime
    media_ids: List[str] = []

class TwitterClient(Protocol):
    """Protocol defining the Twitter client interface."""
    
    async def post_tweet(self, text: str) -> str:
        """Post a tweet.
        
        Args:
            text: The tweet text to post
            
        Returns:
            str: The ID of the posted tweet
            
        Raises:
            TwitterError: If posting fails
        """
        ...
        
    async def media_upload(self, path: str) -> str:
        """Upload media for a tweet.
        
        Args:
            path: Path to the media file
            
        Returns:
            str: The media ID
            
        Raises:
            TwitterError: If upload fails
        """
        ...

class TwitterError(Exception):
    """Base class for Twitter client errors."""
    pass

class TwitterRateLimitError(TwitterError):
    """Raised when Twitter rate limit is exceeded."""
    def __init__(self, reset_at: Optional[datetime] = None):
        self.reset_at = reset_at
        super().__init__(f"Twitter rate limit exceeded. Reset at: {reset_at}")

class MockTwitterClient:
    """Mock implementation of TwitterClient for testing."""
    
    def __init__(self):
        """Initialize the mock client."""
        self._tweets: List[Tweet] = []
        self._media_ids: List[str] = []
        self._rate_limit_remaining = 300  # Twitter's default rate limit
        
    async def post_tweet(self, text: str) -> str:
        """Mock tweet posting."""
        if self._rate_limit_remaining <= 0:
            raise TwitterRateLimitError(
                reset_at=datetime.utcnow()
            )
            
        tweet = Tweet(
            id=f"mock_tweet_{len(self._tweets) + 1}",
            text=text,
            created_at=datetime.utcnow()
        )
        self._tweets.append(tweet)
        self._rate_limit_remaining -= 1
        
        logger.info(
            "Mock tweet posted",
            tweet_id=tweet.id,
            text=text,
            rate_limit_remaining=self._rate_limit_remaining
        )
        
        return tweet.id
        
    async def media_upload(self, path: str) -> str:
        """Mock media upload."""
        media_id = f"mock_media_{len(self._media_ids) + 1}"
        self._media_ids.append(media_id)
        
        logger.info(
            "Mock media uploaded",
            media_id=media_id,
            path=path
        )
        
        return media_id
        
    def reset_rate_limit(self):
        """Reset rate limit for testing."""
        self._rate_limit_remaining = 300
        
    def get_tweet(self, tweet_id: str) -> Optional[Tweet]:
        """Get a tweet by ID for test verification."""
        return next(
            (t for t in self._tweets if t.id == tweet_id),
            None
        ) 