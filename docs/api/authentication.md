# Authentication Guide

Clara Engine uses [Supabase](https://supabase.com) for authentication. All API requests (except documentation endpoints) must include a valid JWT token in the Authorization header.

## Setup

1. Create a Supabase account and project
2. Configure your environment variables:
   ```bash
   SUPABASE_URL=your_project_url
   SUPABASE_KEY=your_project_key
   SUPABASE_JWT_SECRET=your_jwt_secret
   ```

## Getting a JWT Token

### Using Supabase Client

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'your_project_url',
  'your_project_key'
)

// Sign up
const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure_password'
})

// Sign in
const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure_password'
})

// Get JWT token
const token = signInData.session.access_token
```

### Using Python Client

```python
from supabase import create_client

supabase = create_client(
    'your_project_url',
    'your_project_key'
)

# Sign up
signup_data = supabase.auth.sign_up({
    "email": "user@example.com",
    "password": "secure_password"
})

# Sign in
signin_data = supabase.auth.sign_in_with_password({
    "email": "user@example.com",
    "password": "secure_password"
})

# Get JWT token
token = signin_data.session.access_token
```

## Using the Token

Include the token in the Authorization header for all API requests:

```bash
curl -X GET "http://localhost:8000/v1/config/status" \
  -H "Authorization: Bearer your_jwt_token"
```

## Token Expiration

- Access tokens expire after 1 hour by default
- Use refresh tokens to get new access tokens
- Monitor the `exp` claim in the JWT to handle expiration

### Refreshing Tokens

```javascript
// JavaScript
const { data, error } = await supabase.auth.refreshSession()
const new_token = data.session.access_token
```

```python
# Python
refresh_response = supabase.auth.refresh_session()
new_token = refresh_response.session.access_token
```

## Error Handling

### Common Authentication Errors

| Status Code | Description | Solution |
|------------|-------------|----------|
| 401 | Missing token | Include Authorization header |
| 401 | Invalid token | Check token format and validity |
| 401 | Expired token | Refresh the token |
| 403 | Insufficient permissions | Check user role and permissions |

### Example Error Response

```json
{
  "detail": "Invalid authentication token",
  "code": "AUTH_INVALID_TOKEN"
}
```

## Security Best Practices

1. **Token Storage**
   - Never store tokens in localStorage (XSS vulnerable)
   - Use secure HTTP-only cookies
   - Clear tokens on logout

2. **Token Transmission**
   - Always use HTTPS in production
   - Never log or expose tokens
   - Don't include tokens in URLs

3. **Error Handling**
   - Implement proper token refresh logic
   - Handle authentication errors gracefully
   - Don't expose detailed error information to clients

4. **Rate Limiting**
   - Implement rate limiting for auth endpoints
   - Use exponential backoff for retries
   - Monitor failed authentication attempts

## Testing

### Test Tokens

For development and testing, you can generate test tokens using the Supabase dashboard or CLI:

```bash
supabase tokens new --name "test_token" --exp "24h"
```

### Postman Setup

1. Create an environment variable for your token
2. Add a pre-request script to handle token refresh:
   ```javascript
   if (pm.environment.get('token_expires_at') < Date.now()) {
       // Refresh token logic here
   }
   ```

## Troubleshooting

1. **Token Invalid**
   - Check token format (should be JWT)
   - Verify token hasn't expired
   - Ensure correct project key/URL

2. **Permission Denied**
   - Check user role assignments
   - Verify policy configurations
   - Check row-level security settings

3. **Token Refresh Failed**
   - Check refresh token validity
   - Verify refresh token hasn't expired
   - Ensure correct refresh endpoint

## Support

If you encounter authentication issues:
1. Check the [Supabase Authentication Docs](https://supabase.com/docs/guides/auth)
2. Review your project's auth settings
3. Contact support with your project ID 