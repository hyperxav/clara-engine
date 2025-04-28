# Clara Engine API Documentation

## Overview

Clara Engine provides a RESTful API for managing AI-powered Twitter bots. This API allows you to:
- Manage client configurations
- Monitor tweet generation and posting
- Check system status and health
- Configure rate limits and schedules

## Authentication

Clara Engine uses Supabase JWT tokens for authentication. All API requests must include a valid JWT token in the Authorization header:

```bash
Authorization: Bearer <your_jwt_token>
```

See [Authentication Guide](./authentication.md) for detailed setup instructions.

## Rate Limiting

The API implements rate limiting to ensure fair usage:
- 60 requests per minute per client
- Rate limit headers included in responses
- Separate limits for tweet generation and posting

See [Rate Limiting Guide](./rate-limiting.md) for more details.

## API Endpoints

### Tweets
- [GET /v1/tweets](./endpoints/tweets.md#list-tweets) - List tweets
- [GET /v1/tweets/{tweet_id}](./endpoints/tweets.md#get-tweet) - Get tweet details
- [DELETE /v1/tweets/{tweet_id}](./endpoints/tweets.md#delete-tweet) - Delete a scheduled tweet

### Configuration
- [GET /v1/config/status](./endpoints/config.md#get-status) - Get engine status
- [PUT /v1/config/update](./endpoints/config.md#update-config) - Update client configuration

### Status
- [GET /v1/status](./endpoints/status.md#get-status) - Get system health status

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages in a consistent format:

```json
{
  "detail": "Error description",
  "code": "ERROR_CODE",
  "params": {}
}
```

See [Error Reference](./errors.md) for a complete list of error codes.

## SDKs and Tools

- [Postman Collection](./tools/clara-engine.postman_collection.json)
- [Python SDK](./sdk/python.md)
- [TypeScript SDK](./sdk/typescript.md)

## Best Practices

- Always handle rate limit errors with exponential backoff
- Monitor rate limit headers to avoid hitting limits
- Use webhook endpoints for asynchronous operations
- Implement proper error handling for all API calls

## Support

If you encounter any issues or need help:
1. Check the [Troubleshooting Guide](../troubleshooting/README.md)
2. Search existing [GitHub Issues](https://github.com/yourusername/clara-engine/issues)
3. Create a new issue if your problem is not already reported 