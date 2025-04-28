"""Configuration routes for the Clara Engine API."""

from fastapi import APIRouter, HTTPException, Request
from clara_engine.api.models.api import StatusResponse, ConfigUpdate
from clara_engine.core.engine import ClaraEngine
from datetime import datetime, timezone

router = APIRouter(prefix="/config", tags=["config"])

@router.get("/status", response_model=StatusResponse)
async def get_status(request: Request) -> StatusResponse:
    """Get the current status of the Clara Engine.
    
    Returns:
        StatusResponse: Current engine status including state, uptime,
            active clients, component health and rate limits.
    
    Raises:
        HTTPException: If there is an error getting the status.
    """
    try:
        engine: ClaraEngine = request.app.state.engine
        
        # Calculate uptime
        uptime = (datetime.now(timezone.utc) - engine.start_time).total_seconds()
        
        # Get number of active clients
        active_clients = len(await engine.client_manager.get_active_clients())
        
        return StatusResponse(
            state=engine.state,
            uptime=uptime,
            active_clients=active_clients,
            component_health=await engine.get_component_health(),
            rate_limits=await engine.get_rate_limits()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting engine status: {str(e)}"
        )

@router.put("/update")
async def update_config(request: Request, config: ConfigUpdate):
    """Update configuration for a client.
    
    Args:
        config: Configuration update parameters
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If client is not found or there is an error updating config
    """
    try:
        engine: ClaraEngine = request.app.state.engine
        
        await engine.client_manager.update_client_config(
            client_id=config.client_id,
            tweet_interval=config.tweet_interval,
            max_tweets_per_day=config.max_tweets_per_day,
            active=config.active,
            prompt_config=config.prompt_config,
            metadata=config.metadata
        )
        
        return {"message": f"Successfully updated config for client {config.client_id}"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Client not found: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error updating client config: {str(e)}"
        )