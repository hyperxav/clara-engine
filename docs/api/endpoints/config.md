# Configuration Endpoints

## Get Engine Status

Get the current status of the Clara Engine, including uptime, active clients, component health, and rate limits.

```http
GET /v1/config/status
```

### Authentication Required

This endpoint requires a valid JWT token in the Authorization header.

### Response

```json
{
  "state": "running",
  "uptime": 3600.5,
  "active_clients": 5,
  "component_health": {
    "scheduler": {
      "status": true,
      "message": "Healthy",
      "last_check": "2024-02-20T15:30:00Z"
    },
    "twitter": {
      "status": true,
      "message": "Rate limits OK",
      "last_check": "2024-02-20T15:30:00Z"
    },
    "openai": {
      "status": true,
      "message": "API responsive",
      "last_check": "2024-02-20T15:30:00Z"
    }
  },
  "rate_limits": {
    "twitter": 180.0,
    "openai": 3000.0
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| state | string | Current state of the engine (running/stopped/error/starting/stopping) |
| uptime | number | Engine uptime in seconds |
| active_clients | integer | Number of currently active clients |
| component_health | object | Health status of each component |
| rate_limits | object | Current rate limits for various operations |

### Error Responses

| Status Code | Description |
|------------|-------------|
| 401 | Unauthorized - Invalid or missing JWT token |
| 500 | Internal Server Error - Failed to get engine status |

### Example Request

```bash
curl -X GET "http://localhost:8000/v1/config/status" \
  -H "Authorization: Bearer your_jwt_token"
```

## Update Client Configuration

Update configuration settings for a specific client.

```http
PUT /v1/config/update
```

### Authentication Required

This endpoint requires a valid JWT token in the Authorization header.

### Request Body

```json
{
  "client_id": "123e4567-e89b-12d3-a456-426614174000",
  "tweet_interval": 3600,
  "max_tweets_per_day": 24,
  "active": true,
  "prompt_config": {
    "temperature": 0.7,
    "max_tokens": 150
  },
  "metadata": {
    "category": "tech",
    "language": "en"
  }
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| client_id | string | Yes | ID of the client to update |
| tweet_interval | integer | No | Interval between tweets in seconds |
| max_tweets_per_day | integer | No | Maximum number of tweets per day |
| active | boolean | No | Whether the client is active |
| prompt_config | object | No | Configuration for tweet generation prompts |
| metadata | object | No | Additional metadata for the client |

### Response

```json
{
  "message": "Successfully updated config for client 123e4567-e89b-12d3-a456-426614174000"
}
```

### Error Responses

| Status Code | Description |
|------------|-------------|
| 400 | Bad Request - Invalid configuration values |
| 401 | Unauthorized - Invalid or missing JWT token |
| 404 | Not Found - Client not found |
| 500 | Internal Server Error - Failed to update configuration |

### Example Request

```bash
curl -X PUT "http://localhost:8000/v1/config/update" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "123e4567-e89b-12d3-a456-426614174000",
    "tweet_interval": 3600,
    "active": true
  }'
```

### Notes

- All fields except `client_id` are optional
- `tweet_interval` must be greater than 0
- `max_tweets_per_day` must be greater than 0
- Changes take effect immediately
- Previous configuration values are preserved for omitted fields 