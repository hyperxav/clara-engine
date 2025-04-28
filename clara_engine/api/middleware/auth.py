"""Supabase authentication middleware."""

import os
from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
import structlog

logger = structlog.get_logger()

class SupabaseAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for verifying Supabase JWT tokens."""

    async def dispatch(self, request: Request, call_next):
        """Process the request and verify JWT token.
        
        Args:
            request: The incoming request
            call_next: The next middleware/route handler
            
        Returns:
            Response from the next handler or error response
        """
        # Skip auth for OpenAPI docs
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get JWT from header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication token"}
            )

        token = auth_header.split(" ")[1]
        client_id = await self._verify_token(token)
        
        if not client_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication token"}
            )

        # Add client_id to request state
        request.state.client_id = client_id
        return await call_next(request)

    async def _verify_token(self, token: str) -> Optional[str]:
        """Verify Supabase JWT token.
        
        Args:
            token: The JWT token to verify
            
        Returns:
            Client ID if token is valid, None otherwise
        """
        try:
            # Get Supabase JWT secret
            jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
            if not jwt_secret:
                logger.error("Missing SUPABASE_JWT_SECRET environment variable")
                return None

            # Verify token
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"]
            )

            # Extract client ID from claims
            client_id = payload.get("sub")
            if not client_id:
                logger.error("Missing sub claim in JWT", payload=payload)
                return None

            return client_id

        except JWTError as e:
            logger.error("JWT verification failed", error=str(e))
            return None 