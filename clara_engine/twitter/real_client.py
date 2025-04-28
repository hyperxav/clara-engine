"""Real Twitter client implementation using Tweepy."""

import os
from typing import Optional, List
from datetime import datetime
import tweepy
import structlog
from pydantic import BaseModel, Field

from .client import TwitterClient, TwitterError, TwitterRateLimitError, Tweet

logger = structlog.get_logger(__name__)

class TwitterConfig(BaseModel):
    """Configuration for Twitter client."""
    api_key: str = Field(..., description="Twitter API key")
    api_secret: str = Field(..., description="Twitter API secret")
    access_token: str = Field(..., description="Twitter access token")
    access_secret: str = Field(..., description="Twitter access token secret")
    wait_on_rate_limit: bool = Field(default=True, description="Whether to wait when rate limited")

class RealTwitterClient(TwitterClient):
    """Real implementation of TwitterClient using Tweepy."""
    
    def __init__(self, config: Optional[TwitterConfig] = None) -> None:
        """Initialize the Twitter client.
        
        Args:
            config: Twitter configuration. If not provided, will load from environment.
        """
        self.config = config or self._load_config()
        self.client = self._initialize_client()
        self.logger = logger.bind(component="twitter_client")
        
    @staticmethod
    def _load_config() -> TwitterConfig:
        """Load configuration from environment variables."""
        return TwitterConfig(
            api_key=os.getenv("TWITTER_API_KEY", ""),
            api_secret=os.getenv("TWITTER_API_SECRET", ""),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN", ""),
            access_secret=os.getenv("TWITTER_ACCESS_SECRET", ""),
            wait_on_rate_limit=os.getenv("TWITTER_WAIT_ON_RATE_LIMIT", "true").lower() == "true"
        )
        
    def _initialize_client(self) -> tweepy.Client:
        """Initialize the Tweepy client."""
        try:
            client = tweepy.Client(
                consumer_key=self.config.api_key,
                consumer_secret=self.config.api_secret,
                access_token=self.config.access_token,
                access_token_secret=self.config.access_secret,
                wait_on_rate_limit=self.config.wait_on_rate_limit
            )
            
            # Verify credentials
            client.get_me()
            
            self.logger.info("Twitter client initialized successfully")
            return client
            
        except tweepy.TweepyException as e:
            self.logger.error("Failed to initialize Twitter client", error=str(e))
            raise TwitterError(f"Failed to initialize Twitter client: {e}")
    
    async def post_tweet(self, text: str) -> str:
        """Post a tweet.
        
        Args:
            text: The tweet text to post
            
        Returns:
            str: The ID of the posted tweet
            
        Raises:
            TwitterError: If posting fails
            TwitterRateLimitError: If rate limit is exceeded
        """
        try:
            response = self.client.create_tweet(text=text)
            tweet_id = str(response.data["id"])
            
            self.logger.info(
                "Tweet posted successfully",
                tweet_id=tweet_id,
                length=len(text)
            )
            
            return tweet_id
            
        except tweepy.TooManyRequests as e:
            reset_time = datetime.fromtimestamp(int(e.response.headers["x-rate-limit-reset"]))
            self.logger.warning(
                "Rate limit exceeded",
                reset_at=reset_time.isoformat()
            )
            raise TwitterRateLimitError(reset_at=reset_time)
            
        except tweepy.TweepyException as e:
            self.logger.error("Failed to post tweet", error=str(e))
            raise TwitterError(f"Failed to post tweet: {e}")
    
    async def media_upload(self, path: str) -> str:
        """Upload media for a tweet.
        
        Args:
            path: Path to the media file
            
        Returns:
            str: The media ID
            
        Raises:
            TwitterError: If upload fails
        """
        try:
            # Create upload auth
            auth = tweepy.OAuth1UserHandler(
                self.config.api_key,
                self.config.api_secret,
                self.config.access_token,
                self.config.access_secret
            )
            
            # Initialize upload API
            api = tweepy.API(auth)
            
            # Upload media
            media = api.media_upload(filename=path)
            media_id = str(media.media_id)
            
            self.logger.info(
                "Media uploaded successfully",
                media_id=media_id,
                path=path
            )
            
            return media_id
            
        except tweepy.TweepyException as e:
            self.logger.error("Failed to upload media", error=str(e))
            raise TwitterError(f"Failed to upload media: {e}")
    
    def get_tweet(self, tweet_id: str) -> Optional[Tweet]:
        """Get a tweet by ID.
        
        Args:
            tweet_id: The tweet ID to fetch
            
        Returns:
            Tweet if found, None otherwise
            
        Raises:
            TwitterError: If fetching fails
        """
        try:
            response = self.client.get_tweet(
                id=tweet_id,
                expansions=["attachments.media_ids"],
                tweet_fields=["created_at"]
            )
            
            if not response.data:
                return None
                
            tweet_data = response.data
            
            return Tweet(
                id=str(tweet_data.id),
                text=tweet_data.text,
                created_at=tweet_data.created_at,
                media_ids=[
                    str(media.id) 
                    for media in (response.includes.get("media", []) or [])
                ]
            )
            
        except tweepy.TweepyException as e:
            self.logger.error("Failed to get tweet", error=str(e))
            raise TwitterError(f"Failed to get tweet: {e}") 