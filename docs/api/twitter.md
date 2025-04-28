# Twitter Integration API Reference

The Twitter integration provides a robust interface for interacting with Twitter's API v2, including tweet posting, rate limiting, and error handling.

## TwitterClient

The main client for interacting with Twitter's API.

### Configuration

```python
from clara_engine.twitter.client import TwitterConfig, TwitterClient

config = TwitterConfig(
    api_key="your-api-key",
    api_secret="your-api-secret",
    access_token="your-access-token",
    access_token_secret="your-access-token-secret",
    retry_attempts=3,
    retry_delay=5,
    rate_limit_buffer=0.1
)

client = TwitterClient(config)
await client.initialize()
```

### Methods

#### `async def initialize() -> None`
Initialize the Twitter client and validate credentials.

```python
await client.initialize()
```

#### `async def post_tweet(text: str, metadata: Optional[Dict[str, str]] = None) -> TweetResponse`
Post a tweet to Twitter.

```python
response = await client.post_tweet(
    text="Hello, Twitter! #AI",
    metadata={"category": "greeting"}
)
print(f"Tweet posted with ID: {response.tweet_id}")
```

#### `async def delete_tweet(tweet_id: str) -> bool`
Delete a tweet by ID.

```python
success = await client.delete_tweet("1234567890")
```

#### `async def close() -> None`
Close the client connection.

```python
await client.close()
```

### Properties

- `rate_limit_info: RateLimitInfo` - Current rate limit status
- `request_count: int` - Total number of requests made
- `error_count: int` - Total number of errors encountered

## Rate Limiting

The Twitter integration includes Redis-based rate limiting.

### Configuration

```python
from clara_engine.twitter.rate_limiter import RateLimitConfig, RedisRateLimiter

config = RateLimitConfig(
    tweets_per_hour=50,
    tweets_per_day=200,
    burst_size=5
)

limiter = RedisRateLimiter(
    redis_url="redis://localhost:6379/0",
    config=config
)
```

### Methods

#### `async def check_limit(client_id: str) -> RateLimitInfo`
Check if a client has available rate limit.

```python
info = await limiter.check_limit("client_123")
if not info.is_limited:
    # Post tweet
else:
    print(f"Rate limited, retry after {info.retry_after} seconds")
```

#### `async def acquire(client_id: str) -> RateLimitInfo`
Acquire a rate limit token (blocking).

## Error Handling

The Twitter integration includes comprehensive error handling:

```python
try:
    response = await client.post_tweet("Hello, Twitter!")
except Exception as e:
    if isinstance(e, RateLimitExceeded):
        # Handle rate limit
        retry_after = e.retry_after
    elif isinstance(e, TwitterAPIError):
        # Handle API error
        error_code = e.code
        error_message = e.message
    else:
        # Handle other errors
        logger.error("Twitter error", error=str(e))
```

### Error Types

- `RateLimitExceeded` - Twitter API rate limit exceeded
- `TwitterAPIError` - General Twitter API error
- `TwitterAuthError` - Authentication error
- `TwitterNetworkError` - Network connectivity issues
- `TwitterValidationError` - Tweet content validation error

## Mock Client

For testing and development, a mock Twitter client is provided:

```python
from clara_engine.twitter.mock import MockTwitterClient

client = MockTwitterClient()
await client.initialize()

# Post tweet (no actual API calls made)
response = await client.post_tweet("Test tweet")
```

### Mock Features

- Simulates API responses
- Tracks rate limits
- Records tweet history
- Configurable error scenarios

## Metrics

The Twitter integration exports various metrics:

### Prometheus Metrics

- `clara_twitter_tweets_total` - Total tweets posted
- `clara_twitter_errors_total` - Error count by type
- `clara_twitter_rate_limit_remaining` - Remaining rate limit
- `clara_twitter_response_time_seconds` - API response time

### Usage Example

```python
from prometheus_client import start_http_server

# Start metrics server
start_http_server(9090)

# Metrics are automatically collected during client usage
```

## Best Practices

1. **Resource Management**
   ```python
   async with TwitterClient(config) as client:
       response = await client.post_tweet("Hello, Twitter!")
   ```

2. **Error Handling**
   ```python
   try:
       response = await client.post_tweet("Hello, Twitter!")
   except Exception as e:
       logger.error("Twitter error", error=str(e))
       # Implement retry or fallback
   ```

3. **Rate Limiting**
   ```python
   async with limiter.acquire("client_id"):
       response = await client.post_tweet("Hello, Twitter!")
   ```

4. **Content Validation**
   ```python
   if len(tweet_text) > 280:
       raise TwitterValidationError("Tweet exceeds character limit")
   ```

## Example Usage

Complete example of using the Twitter integration:

```python
async def post_scheduled_tweet(client_id: str, tweet_text: str) -> TweetResponse:
    # Initialize components
    config = TwitterConfig(api_key="your-key")
    client = TwitterClient(config)
    limiter = RedisRateLimiter()
    
    try:
        # Initialize client
        await client.initialize()
        
        # Check rate limit
        async with limiter.acquire(client_id):
            # Post tweet with retry logic
            for attempt in range(3):
                try:
                    response = await client.post_tweet(tweet_text)
                    return response
                except TwitterAPIError as e:
                    if attempt == 2:  # Last attempt
                        raise
                    await asyncio.sleep(5)  # Wait before retry
                    
    finally:
        await client.close()
```

## Testing

The Twitter integration includes comprehensive test utilities:

```python
from clara_engine.twitter.testing import TwitterTestClient

# Create test client
client = TwitterTestClient()

# Configure mock responses
client.add_mock_response(
    method="post_tweet",
    response=TweetResponse(tweet_id="123", text="Test tweet")
)

# Use in tests
response = await client.post_tweet("Test tweet")
assert response.tweet_id == "123"
```

### Test Utilities

- Mock responses
- Rate limit simulation
- Error scenario testing
- Request history tracking 