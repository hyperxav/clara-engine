# OpenAI Integration API Reference

The OpenAI integration provides a robust interface for interacting with OpenAI's API, including completion generation, prompt management, response validation, and caching.

## OpenAIClient

The main client for interacting with OpenAI's API.

### Configuration

```python
from clara_engine.openai.client import OpenAIConfig, OpenAIClient

config = OpenAIConfig(
    api_key="your-api-key",
    model="gpt-4",
    max_tokens=150,
    temperature=0.7,
    cache_enabled=True,
    cache_ttl=3600,
    cache_similarity=0.95,
    cache_size=1000
)

client = OpenAIClient(config)
await client.initialize()
```

### Methods

#### `async def initialize() -> None`
Initialize the OpenAI client and validate the connection.

```python
await client.initialize()
```

#### `async def generate_completion(prompt: str, metadata: Optional[Dict[str, str]] = None) -> str`
Generate a completion for a given prompt.

```python
response = await client.generate_completion(
    prompt="Generate a tweet about AI",
    metadata={"category": "technology"}
)
```

#### `async def close() -> None`
Close the client connection.

```python
await client.close()
```

### Properties

- `token_count: int` - Total number of tokens used
- `request_count: int` - Total number of requests made
- `cache_stats: Optional[Dict[str, int]]` - Cache statistics if enabled

## PromptManager

Manages prompt templates and generation.

### Usage

```python
from clara_engine.openai.prompts import PromptManager, PromptTemplate

manager = PromptManager()

# Add custom template
template = PromptTemplate(
    name="custom_tweet",
    template="Generate a tweet about {{ topic }} in a {{ tone }} tone",
    max_length=280
)
manager.add_template(template)

# Render prompt
prompt = manager.render_prompt(
    "custom_tweet",
    {
        "topic": "artificial intelligence",
        "tone": "professional"
    }
)
```

### Methods

#### `add_template(template: PromptTemplate) -> None`
Add a new prompt template.

#### `get_template(name: str) -> PromptTemplate`
Get a prompt template by name.

#### `render_prompt(template_name: str, variables: Dict[str, Any]) -> str`
Render a prompt using a template.

## ResponseValidator

Validates generated responses against defined rules.

### Configuration

```python
from clara_engine.openai.validators import ValidationConfig, ResponseValidator

config = ValidationConfig(
    max_tokens=150,
    max_length=280,
    content_filter=True,
    profanity_threshold=0.5,
    sentiment_threshold=-0.3
)

validator = ResponseValidator(config)
```

### Methods

#### `async def validate(response: str) -> ValidationResult`
Validate a response against all configured rules.

```python
result = await validator.validate("Generated tweet text")
if result.valid:
    print("Tweet is valid")
else:
    print("Validation errors:", result.errors)
```

#### `add_rule(rule: ValidationRule) -> None`
Add a custom validation rule.

```python
rule = ValidationRule(
    name="custom_rule",
    enabled=True,
    severity="error",
    parameters={"min_length": 10}
)
validator.add_rule(rule)
```

## Rate Limiting

The OpenAI integration includes Redis-based rate limiting.

### Configuration

```python
from clara_engine.openai.rate_limiter import RateLimitConfig, RedisRateLimiter

config = RateLimitConfig(
    requests_per_second=1.0,
    daily_limit=50,
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
    # Make API request
else:
    print(f"Rate limited, retry after {info.retry_after} seconds")
```

#### `async def acquire(client_id: str) -> RateLimitInfo`
Acquire a rate limit token (blocking).

## Caching

The OpenAI integration includes semantic caching for responses.

### Configuration

Cache configuration is part of `OpenAIConfig`:

```python
config = OpenAIConfig(
    # ... other settings ...
    cache_enabled=True,
    cache_ttl=3600,  # 1 hour
    cache_similarity=0.95,
    cache_size=1000
)
```

### Cache Behavior

- Responses are cached based on prompt similarity
- Cache hits require similarity score > threshold
- LRU eviction when size limit reached
- TTL-based expiration

## Error Handling

The OpenAI integration includes comprehensive error handling:

```python
try:
    response = await client.generate_completion("prompt")
except Exception as e:
    if isinstance(e, RateLimitExceeded):
        # Handle rate limit
        retry_after = e.retry_after
    elif isinstance(e, ValidationError):
        # Handle validation failure
        errors = e.errors
    else:
        # Handle other errors
        logger.error("OpenAI error", error=str(e))
```

## Metrics

The OpenAI integration exports various metrics:

### Prometheus Metrics

- `clara_openai_requests_total` - Total API requests
- `clara_openai_tokens_total` - Total tokens used
- `clara_openai_errors_total` - Error count by type
- `clara_openai_cache_hits_total` - Cache hit count
- `clara_openai_cache_misses_total` - Cache miss count
- `clara_openai_rate_limit_remaining` - Remaining rate limit
- `clara_openai_response_time_seconds` - API response time

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
   async with OpenAIClient(config) as client:
       response = await client.generate_completion("prompt")
   ```

2. **Error Handling**
   ```python
   try:
       response = await client.generate_completion("prompt")
   except Exception as e:
       logger.error("OpenAI error", error=str(e))
       # Implement retry or fallback
   ```

3. **Rate Limiting**
   ```python
   async with limiter.acquire("client_id"):
       response = await client.generate_completion("prompt")
   ```

4. **Validation**
   ```python
   result = await validator.validate(response)
   if not result.valid:
       logger.warning("Validation failed", errors=result.errors)
       # Handle invalid response
   ```

## Example Usage

Complete example of using the OpenAI integration:

```python
async def generate_tweet(topic: str, tone: str) -> str:
    # Initialize components
    config = OpenAIConfig(api_key="your-key")
    client = OpenAIClient(config)
    manager = PromptManager()
    validator = ResponseValidator()
    
    try:
        # Initialize client
        await client.initialize()
        
        # Generate prompt
        prompt = manager.render_prompt(
            "tweet_generation",
            {"topic": topic, "tone": tone}
        )
        
        # Generate completion
        response = await client.generate_completion(prompt)
        
        # Validate response
        result = await validator.validate(response)
        if not result.valid:
            raise ValueError(f"Invalid response: {result.errors}")
        
        return response
        
    finally:
        await client.close()
``` 