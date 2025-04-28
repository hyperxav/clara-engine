"""Core engine that orchestrates all components."""

import asyncio
from typing import Optional, Dict, Any
import signal
import structlog
from pydantic import BaseModel, Field

from clara_engine.db import Database
from clara_engine.clients.manager import ClientManager
from clara_engine.core.scheduler import TweetScheduler, SchedulerConfig
from clara_engine.openai.rate_limiter import RedisRateLimiter, RateLimitConfig

logger = structlog.get_logger(__name__)

class EngineConfig(BaseModel):
    """Configuration for Clara Engine."""
    scheduler: SchedulerConfig = Field(
        default_factory=SchedulerConfig,
        description="Scheduler configuration"
    )
    rate_limiter: RateLimitConfig = Field(
        default_factory=RateLimitConfig,
        description="Rate limiter configuration"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for rate limiting"
    )
    shutdown_timeout: float = Field(
        default=30.0,
        description="Maximum time to wait for graceful shutdown (seconds)"
    )

class EngineStatus(BaseModel):
    """Status of the Clara Engine."""
    running: bool = Field(default=False, description="Whether the engine is running")
    scheduler_running: bool = Field(default=False, description="Whether the scheduler is running")
    active_clients: int = Field(default=0, description="Number of active clients")
    components_healthy: Dict[str, bool] = Field(
        default_factory=dict,
        description="Health status of each component"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Various engine metrics"
    )

class ClaraEngine:
    """Main engine that orchestrates all components."""
    
    def __init__(self, config: Optional[EngineConfig] = None) -> None:
        """Initialize the engine.
        
        Args:
            config: Optional engine configuration
        """
        self.config = config or EngineConfig()
        self.logger = logger.bind(component="engine")
        
        # Initialize components
        self.db = Database()
        self.client_manager = ClientManager(self.db)
        self.rate_limiter = RedisRateLimiter(
            self.config.redis_url,
            self.config.rate_limiter
        )
        self.scheduler = TweetScheduler(
            self.client_manager,
            self.db,
            self.config.scheduler
        )
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Track status
        self._status = EngineStatus()
        self._shutdown_event = asyncio.Event()
    
    def _setup_signal_handlers(self) -> None:
        """Setup handlers for system signals."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)
            
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle system signals."""
        self.logger.info("Received shutdown signal", signal=signum)
        if not self._shutdown_event.is_set():
            asyncio.create_task(self.shutdown())
    
    async def start(self) -> None:
        """Start the engine and all components."""
        try:
            self.logger.info("Starting Clara Engine")
            
            # Initialize rate limiter
            await self.rate_limiter.initialize()
            self._status.components_healthy["rate_limiter"] = True
            
            # Initialize client manager
            await self.client_manager.initialize()
            self._status.active_clients = len(self.client_manager.get_active_clients())
            self._status.components_healthy["client_manager"] = True
            
            # Start scheduler
            await self.scheduler.start()
            self._status.scheduler_running = True
            self._status.components_healthy["scheduler"] = True
            
            self._status.running = True
            self.logger.info(
                "Clara Engine started",
                active_clients=self._status.active_clients
            )
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except Exception as e:
            self.logger.error("Failed to start engine", error=str(e))
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the engine."""
        if not self._status.running:
            return
            
        self.logger.info("Initiating graceful shutdown")
        self._shutdown_event.set()
        
        try:
            # Stop scheduler first
            if self._status.scheduler_running:
                await asyncio.wait_for(
                    self.scheduler.stop(),
                    timeout=self.config.shutdown_timeout / 2
                )
                self._status.scheduler_running = False
            
            # Close rate limiter
            await self.rate_limiter.close()
            
            # Close client connections
            await self.client_manager.close()
            
            self._status.running = False
            self.logger.info("Engine shutdown complete")
            
        except asyncio.TimeoutError:
            self.logger.error(
                "Shutdown timed out",
                timeout=self.config.shutdown_timeout
            )
        except Exception as e:
            self.logger.error(
                "Error during shutdown",
                error=str(e)
            )
    
    async def health_check(self) -> EngineStatus:
        """Check health of all components.
        
        Returns:
            Current engine status
        """
        try:
            # Update active clients count
            self._status.active_clients = len(self.client_manager.get_active_clients())
            
            # Check rate limiter
            rate_limit_info = await self.rate_limiter.check_limit("health_check")
            self._status.components_healthy["rate_limiter"] = not rate_limit_info.is_limited
            
            # Update metrics
            self._status.metrics.update({
                "active_clients": self._status.active_clients,
                "rate_limit_remaining": rate_limit_info.remaining_tokens,
                "scheduler_running": self._status.scheduler_running
            })
            
            return self._status
            
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            self._status.components_healthy["health_check"] = False
            return self._status
    
    @property
    def status(self) -> EngineStatus:
        """Get current engine status."""
        return self._status 