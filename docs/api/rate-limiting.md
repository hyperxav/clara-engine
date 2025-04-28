# Rate Limiting

Clara Engine implements rate limiting to ensure fair usage and system stability. This guide explains how rate limiting works and how to handle it in your applications.

## Overview

Rate limits are applied at multiple levels:
1. API-level rate limiting (per client)
2. Twitter API rate limiting
3. OpenAI API rate limiting

## API Rate Limits

### Default Limits

- 60 requests per minute per client
- Burst capacity of 5 requests
- Limits are tracked using Redis with a sliding window

### Rate Limit Headers

All API responses include rate limit headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1628776932
```

- `X-RateLimit-Limit`: Maximum requests allowed per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets

### Rate Limit Response

When rate limited, you'll receive a 429 Too Many Requests response:

```json
{
  "detail": "Rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "reset_at": "2024-03-15T10:00:00Z"
}
```

## Twitter API Rate Limits

Clara Engine respects Twitter's rate limits for tweet creation:

- 200 tweets per 3 hours per account
- 50 tweets per 15 minutes per account
- Retweets count towards these limits

### Monitoring Twitter Rate Limits

Check current Twitter rate limit status:

```bash
GET /v1/config/status
```

Response includes Twitter rate limits:
```json
{
  "rate_limits": {
    "twitter": {
      "tweets_remaining": 180,
      "reset_at": "2024-03-15T10:00:00Z"
    }
  }
}
```

## OpenAI API Rate Limits

Clara Engine manages OpenAI API rate limits:

- Tokens per minute limit
- Requests per minute limit
- Cost optimization features

### Monitoring OpenAI Rate Limits

Check current OpenAI rate limit status:

```bash
GET /v1/config/status
```

Response includes OpenAI rate limits:
```json
{
  "rate_limits": {
    "openai": {
      "tokens_remaining": 90000,
      "requests_remaining": 3000,
      "reset_at": "2024-03-15T10:00:00Z"
    }
  }
}
```

## Best Practices

### Handling Rate Limits

1. **Implement Exponential Backoff**
   ```python
   import time
   import random

   def make_request_with_backoff(func, max_retries=5):
       for attempt in range(max_retries):
           try:
               return func()
           except RateLimitError as e:
               if attempt == max_retries - 1:
                   raise
               delay = (2 ** attempt) + random.random()
               time.sleep(delay)
   ```

2. **Monitor Rate Limit Headers**
   ```python
   def check_rate_limits(response):
       remaining = int(response.headers['X-RateLimit-Remaining'])
       if remaining < 10:
           # Consider implementing request queuing
           logger.warning(f"Rate limit running low: {remaining} remaining")
   ```

3. **Implement Request Queuing**
   ```python
   from asyncio import Queue
   
   request_queue = Queue()
   
   async def process_queue():
       while True:
           request = await request_queue.get()
           try:
               await make_request(request)
           except RateLimitError:
               # Re-queue with backoff
               await request_queue.put(request)
               await asyncio.sleep(1)
   ```

### Rate Limit Optimization

1. **Batch Requests**
   - Combine multiple operations into single requests
   - Use bulk endpoints where available

2. **Cache Responses**
   - Cache successful responses
   - Implement cache invalidation strategies

3. **Distribute Load**
   - Spread requests across time windows
   - Implement request prioritization

## Monitoring and Alerts

### Metrics Available

- `clara_rate_limit_remaining`: Gauge of remaining requests
- `clara_rate_limit_exceeded`: Counter of rate limit hits
- `clara_rate_limit_reset`: Timestamp of next reset

### Setting Up Alerts

Configure alerts for:
1. Low remaining rate limits
2. High rate of 429 responses
3. Unusual spikes in request patterns

## Troubleshooting

### Common Issues

1. **Unexpected Rate Limits**
   - Check all rate limit levels (API, Twitter, OpenAI)
   - Verify client authentication
   - Review request patterns

2. **Rate Limit Calculation**
   - Rate limits use UTC timezone
   - Windows are sliding, not fixed
   - Burst limits apply separately

3. **Integration Issues**
   - Verify rate limit header parsing
   - Check retry logic implementation
   - Validate queue processing

### Getting Help

If you encounter rate limiting issues:
1. Check the rate limit status endpoint
2. Review your request logs
3. Contact support with your client ID

## Configuration

### Custom Rate Limits

Enterprise clients can request custom rate limits:
- Higher request limits
- Custom window sizes
- Dedicated rate limit pools

Contact support to discuss custom rate limit options. 