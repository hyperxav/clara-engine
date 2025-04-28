"""Tweet scheduling and automation."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
import structlog
from pydantic import BaseModel, Field

from clara_engine.clients.manager import ClientManager, ClientContext
from clara_engine.twitter.generator import TweetGenerator
from clara_engine.twitter.client import TwitterError, TwitterRateLimitError
from clara_engine.db import Database
from clara_engine.models import Tweet as TweetModel, TweetCreate

logger = structlog.get_logger(__name__)

class SchedulerConfig(BaseModel):
    """Configuration for tweet scheduler."""
    check_interval: int = Field(
        default=60,
        description="How often to check for due tweets (in seconds)"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed tweets"
    )
    retry_delay: int = Field(
        default=300,
        description="Delay between retries (in seconds)"
    )
    batch_size: int = Field(
        default=10,
        description="Maximum number of tweets to process in parallel"
    )

class TweetScheduler:
    """Manages automated tweet posting."""
    
    def __init__(
        self,
        client_manager: ClientManager,
        db: Database,
        config: Optional[SchedulerConfig] = None
    ) -> None:
        """Initialize the tweet scheduler.
        
        Args:
            client_manager: Manager for client contexts
            db: Database instance
            config: Optional scheduler configuration
        """
        self.client_manager = client_manager
        self.db = db
        self.config = config or SchedulerConfig()
        
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self.logger = logger.bind(component="scheduler")
        
    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            self.logger.warning("Scheduler already running")
            return
            
        self._running = True
        self._task = asyncio.create_task(self._run())
        self.logger.info(
            "Scheduler started",
            check_interval=self.config.check_interval,
            batch_size=self.config.batch_size
        )
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running:
            return
            
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            
        self.logger.info("Scheduler stopped")
    
    async def _run(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                # Get clients due for tweets
                due_clients = self.client_manager.get_clients_due_for_tweet()
                
                if due_clients:
                    self.logger.info(
                        "Processing due clients",
                        count=len(due_clients)
                    )
                    
                    # Process in batches
                    for i in range(0, len(due_clients), self.config.batch_size):
                        batch = due_clients[i:i + self.config.batch_size]
                        await asyncio.gather(
                            *(self._process_client(client) for client in batch)
                        )
                
                # Wait for next check
                await asyncio.sleep(self.config.check_interval)
                
            except Exception as e:
                self.logger.error("Error in scheduler loop", error=str(e))
                await asyncio.sleep(self.config.check_interval)
    
    async def _process_client(self, context: ClientContext) -> None:
        """Process a single client's tweet generation and posting.
        
        Args:
            context: Client context to process
        """
        client_id = context.client_id
        logger = self.logger.bind(client_id=client_id)
        
        try:
            # Get client data
            client = self.db.get_client(client_id)
            if not client:
                logger.error("Client not found in database")
                return
                
            # Create tweet generator
            generator = TweetGenerator(
                context.openai_client,
                context.prompt_manager,
                context.validator
            )
            
            # Generate tweet
            tweet_text = await generator.generate_tweet(
                topic=client.persona_prompt
            )
            
            # Create tweet record
            tweet = self.db.create_tweet(TweetCreate(
                client_id=client.id,
                tweet_text=tweet_text,
                status="pending"
            ))
            
            # Post tweet with retries
            tweet_id = await self._post_with_retries(
                context,
                tweet,
                logger
            )
            
            if tweet_id:
                # Update tweet record
                self.db.update_tweet(
                    tweet.id,
                    {
                        "status": "posted",
                        "tweet_url": f"https://twitter.com/i/web/status/{tweet_id}",
                        "posted_at": datetime.utcnow()
                    }
                )
                
                # Update client's last tweet time
                self.db.update_client(
                    client.id,
                    {"last_posted_at": datetime.utcnow()}
                )
                
                # Update context
                context.last_tweet_at = datetime.utcnow()
                
                logger.info(
                    "Tweet posted successfully",
                    tweet_id=tweet_id
                )
            
        except Exception as e:
            logger.error(
                "Failed to process client",
                error=str(e)
            )
    
    async def _post_with_retries(
        self,
        context: ClientContext,
        tweet: TweetModel,
        logger: structlog.BoundLogger
    ) -> Optional[str]:
        """Post a tweet with retries.
        
        Args:
            context: Client context
            tweet: Tweet to post
            logger: Bound logger instance
            
        Returns:
            Tweet ID if successful, None otherwise
        """
        for attempt in range(self.config.max_retries):
            try:
                return await context.twitter_client.post_tweet(tweet.tweet_text)
                
            except TwitterRateLimitError as e:
                logger.warning(
                    "Rate limit exceeded",
                    attempt=attempt + 1,
                    reset_at=e.reset_at
                )
                
                # Update tweet status
                self.db.update_tweet(
                    tweet.id,
                    {
                        "status": "failed",
                        "error_message": f"Rate limit exceeded. Reset at: {e.reset_at}"
                    }
                )
                
                # Wait for rate limit reset if this isn't the last attempt
                if attempt < self.config.max_retries - 1 and e.reset_at:
                    wait_time = (e.reset_at - datetime.utcnow()).total_seconds()
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                
            except TwitterError as e:
                logger.error(
                    "Error posting tweet",
                    attempt=attempt + 1,
                    error=str(e)
                )
                
                # Update tweet status
                self.db.update_tweet(
                    tweet.id,
                    {
                        "status": "failed",
                        "error_message": str(e)
                    }
                )
                
                # Wait before retry
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
        
        return None 