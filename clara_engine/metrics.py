"""Metrics collection and monitoring for Clara Engine."""

import asyncio
from typing import Dict, Any, Optional
from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server
from prometheus_client.registry import CollectorRegistry
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

class MetricsConfig(BaseModel):
    """Configuration for metrics collection."""
    enabled: bool = Field(default=True, description="Whether metrics collection is enabled")
    port: int = Field(default=9090, description="Port to expose metrics on")
    prefix: str = Field(default="clara", description="Prefix for metric names")
    collection_interval: int = Field(default=15, description="Metrics collection interval in seconds")

class MetricsCollector:
    """Collector for Clara Engine metrics."""
    
    def __init__(self, config: Optional[MetricsConfig] = None) -> None:
        """Initialize metrics collector.
        
        Args:
            config: Optional metrics configuration
        """
        self.config = config or MetricsConfig()
        self.registry = CollectorRegistry()
        self._setup_metrics()
        self._running = False
        self.logger = logger.bind(component="metrics")
        
    def _setup_metrics(self) -> None:
        """Set up Prometheus metrics."""
        prefix = self.config.prefix
        
        # System metrics
        self.uptime = Gauge(
            f"{prefix}_uptime_seconds",
            "Time since Clara Engine started",
            registry=self.registry
        )
        
        self.active_clients = Gauge(
            f"{prefix}_active_clients",
            "Number of active clients",
            registry=self.registry
        )
        
        # Tweet metrics
        self.tweets_sent = Counter(
            f"{prefix}_tweets_sent_total",
            "Total number of tweets sent",
            ["client_id"],
            registry=self.registry
        )
        
        self.tweet_errors = Counter(
            f"{prefix}_tweet_errors_total",
            "Total number of tweet errors",
            ["client_id", "error_type"],
            registry=self.registry
        )
        
        self.tweet_generation_time = Histogram(
            f"{prefix}_tweet_generation_seconds",
            "Time taken to generate tweets",
            ["client_id"],
            registry=self.registry
        )
        
        # Rate limit metrics
        self.twitter_rate_limit = Gauge(
            f"{prefix}_twitter_rate_limit_remaining",
            "Remaining Twitter API rate limit",
            ["client_id"],
            registry=self.registry
        )
        
        self.openai_rate_limit = Gauge(
            f"{prefix}_openai_rate_limit_remaining",
            "Remaining OpenAI API rate limit",
            registry=self.registry
        )
        
        # Component health
        self.component_health = Gauge(
            f"{prefix}_component_health",
            "Health status of components (1=healthy, 0=unhealthy)",
            ["component"],
            registry=self.registry
        )
        
        # System info
        self.system_info = Info(
            f"{prefix}_system_info",
            "Clara Engine system information",
            registry=self.registry
        )
        
    async def start(self) -> None:
        """Start metrics collection and exposition."""
        if self.config.enabled:
            try:
                # Start Prometheus HTTP server
                start_http_server(
                    port=self.config.port,
                    registry=self.registry
                )
                
                self.logger.info(
                    "Started metrics server",
                    port=self.config.port
                )
                
                self._running = True
                
            except Exception as e:
                self.logger.error(
                    "Failed to start metrics server",
                    error=str(e)
                )
                raise
                
    async def stop(self) -> None:
        """Stop metrics collection."""
        self._running = False
        self.logger.info("Stopped metrics collection")
        
    def record_tweet_sent(self, client_id: str) -> None:
        """Record a successful tweet."""
        self.tweets_sent.labels(client_id=client_id).inc()
        
    def record_tweet_error(self, client_id: str, error_type: str) -> None:
        """Record a tweet error."""
        self.tweet_errors.labels(
            client_id=client_id,
            error_type=error_type
        ).inc()
        
    def observe_generation_time(self, client_id: str, seconds: float) -> None:
        """Record tweet generation time."""
        self.tweet_generation_time.labels(
            client_id=client_id
        ).observe(seconds)
        
    def set_rate_limits(self, client_id: str, twitter_remaining: int, openai_remaining: int) -> None:
        """Update rate limit metrics."""
        self.twitter_rate_limit.labels(
            client_id=client_id
        ).set(twitter_remaining)
        self.openai_rate_limit.set(openai_remaining)
        
    def update_component_health(self, component: str, healthy: bool) -> None:
        """Update component health status."""
        self.component_health.labels(
            component=component
        ).set(1 if healthy else 0)
        
    def set_active_clients(self, count: int) -> None:
        """Update active clients count."""
        self.active_clients.set(count)
        
    def update_system_info(self, info: Dict[str, Any]) -> None:
        """Update system information."""
        self.system_info.info(info)
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics values.
        
        Returns:
            Dict containing current metric values
        """
        return {
            "active_clients": self.active_clients._value.get(),
            "tweets_sent": {
                client_id: counter._value.get()
                for client_id, counter in self.tweets_sent._metrics.items()
            },
            "tweet_errors": {
                f"{client_id}_{error_type}": counter._value.get()
                for (client_id, error_type), counter in self.tweet_errors._metrics.items()
            },
            "component_health": {
                component: gauge._value.get()
                for component, gauge in self.component_health._metrics.items()
            }
        } 