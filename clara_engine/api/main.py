"""Main FastAPI application module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from clara_engine.api.routes import tweets, config, status
from clara_engine.api.middleware.auth import SupabaseAuthMiddleware
from clara_engine.api.middleware.limiter import setup_limiter

app = FastAPI(
    title="Clara Engine API",
    description="API for Clara Engine Twitter bot platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Supabase auth middleware
app.add_middleware(SupabaseAuthMiddleware)

@app.on_event("startup")
async def startup():
    """Initialize rate limiter on startup."""
    await setup_limiter(app)

# Include routers
app.include_router(tweets.router, prefix="/v1", tags=["tweets"])
app.include_router(config.router, prefix="/v1", tags=["config"])
app.include_router(status.router, prefix="/v1", tags=["status"])

def custom_openapi():
    """Customize OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Clara Engine API",
        version="1.0.0",
        description="API for Clara Engine Twitter bot platform",
        routes=app.routes,
    )
    
    # Add security scheme for JWT
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi 