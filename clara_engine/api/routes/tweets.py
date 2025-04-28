"""Tweet routes for the Clara Engine API."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from clara_engine.api.models.api import Tweet, TweetList
from clara_engine.api.middleware.limiter import limiter
from clara_engine.core.engine import ClaraEngine
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/tweets", tags=["tweets"])

@router.get(
    "",
    response_model=TweetList,
    dependencies=[Depends(limiter)],
    description="Get a list of tweets for the authenticated client"
)
async def list_tweets(
    status: Optional[str] = Query(None, description="Filter by tweet status"),
    limit: int = Query(10, description="Number of tweets to return", ge=1, le=100),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    engine: ClaraEngine = Depends()
) -> TweetList:
    """Get a list of tweets."""
    try:
        tweets = await engine.get_tweets(status=status, limit=limit, offset=offset)
        total = await engine.get_tweet_count(status=status)
        return TweetList(tweets=tweets, total=total)
    except Exception as e:
        logger.error("Failed to get tweets", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get tweets")

@router.get(
    "/{tweet_id}",
    response_model=Tweet,
    dependencies=[Depends(limiter)],
    description="Get a specific tweet by ID"
)
async def get_tweet(tweet_id: str, engine: ClaraEngine = Depends()) -> Tweet:
    """Get a specific tweet."""
    try:
        tweet = await engine.get_tweet(tweet_id)
        if not tweet:
            raise HTTPException(status_code=404, detail="Tweet not found")
        return tweet
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get tweet", tweet_id=tweet_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get tweet")

@router.delete(
    "/{tweet_id}",
    status_code=204,
    dependencies=[Depends(limiter)],
    description="Delete a scheduled tweet"
)
async def delete_tweet(tweet_id: str, engine: ClaraEngine = Depends()) -> None:
    """Delete a scheduled tweet."""
    try:
        success = await engine.delete_tweet(tweet_id)
        if not success:
            raise HTTPException(status_code=404, detail="Tweet not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete tweet", tweet_id=tweet_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete tweet") 