"""Client manager for multi-tenant support."""

from typing import Dict, Optional, List
from datetime import datetime
import pytz
import structlog
from pydantic import BaseModel, Field

from clara_engine.db import Database
from clara_engine.models import Client as ClientModel
from clara_engine.twitter.real_client import RealTwitterClient, TwitterConfig
from clara_engine.openai.client import OpenAIClient, OpenAIConfig
from clara_engine.openai.prompts import PromptManager
from clara_engine.openai.validators import ResponseValidator, ValidationConfig

logger = structlog.get_logger(__name__)

class ClientContext(BaseModel):
    """Context for a single client."""
    client_id: str = Field(..., description="Client ID in database")
    twitter_client: RealTwitterClient = Field(..., description="Twitter client instance")
    openai_client: OpenAIClient = Field(..., description="OpenAI client instance")
    prompt_manager: PromptManager = Field(..., description="Prompt manager instance")
    validator: ResponseValidator = Field(..., description="Response validator instance")
    last_tweet_at: Optional[datetime] = Field(default=None, description="Last tweet timestamp")
    active: bool = Field(default=True, description="Whether client is active")

class ClientManager:
    """Manager for handling multiple clients."""
    
    def __init__(self, db: Database) -> None:
        """Initialize the client manager.
        
        Args:
            db: Database instance for client data
        """
        self.db = db
        self._clients: Dict[str, ClientContext] = {}
        self.logger = logger.bind(component="client_manager")
        
    async def initialize(self) -> None:
        """Initialize all active clients from database."""
        try:
            # Get all active clients
            clients = self.db.get_active_clients()
            
            for client in clients:
                await self.add_client(client)
                
            self.logger.info(
                "Initialized client manager",
                client_count=len(self._clients)
            )
            
        except Exception as e:
            self.logger.error("Failed to initialize client manager", error=str(e))
            raise
    
    async def add_client(self, client: ClientModel) -> None:
        """Add a new client.
        
        Args:
            client: Client model from database
        """
        try:
            # Create Twitter client
            twitter_config = TwitterConfig(
                api_key=client.twitter_key,
                api_secret=client.twitter_secret,
                access_token=client.access_token,
                access_secret=client.access_secret
            )
            twitter_client = RealTwitterClient(twitter_config)
            
            # Create OpenAI client
            openai_client = OpenAIClient()
            await openai_client.initialize()
            
            # Create prompt manager with client-specific templates
            prompt_manager = PromptManager()
            prompt_manager.add_template_from_string(
                "persona",
                client.persona_prompt,
                description=f"Persona template for client {client.id}"
            )
            
            # Create validator
            validator = ResponseValidator(ValidationConfig())
            
            # Create context
            context = ClientContext(
                client_id=str(client.id),
                twitter_client=twitter_client,
                openai_client=openai_client,
                prompt_manager=prompt_manager,
                validator=validator,
                last_tweet_at=client.last_posted_at,
                active=client.active
            )
            
            self._clients[str(client.id)] = context
            
            self.logger.info(
                "Added client",
                client_id=client.id,
                name=client.name
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to add client",
                client_id=client.id,
                error=str(e)
            )
            raise
    
    async def remove_client(self, client_id: str) -> None:
        """Remove a client.
        
        Args:
            client_id: ID of client to remove
        """
        if client_id in self._clients:
            context = self._clients[client_id]
            
            # Clean up resources
            await context.openai_client.close()
            
            del self._clients[client_id]
            
            self.logger.info("Removed client", client_id=client_id)
    
    def get_client(self, client_id: str) -> Optional[ClientContext]:
        """Get a client context by ID.
        
        Args:
            client_id: Client ID to get
            
        Returns:
            Client context if found, None otherwise
        """
        return self._clients.get(client_id)
    
    def get_active_clients(self) -> List[ClientContext]:
        """Get all active client contexts.
        
        Returns:
            List of active client contexts
        """
        return [
            context for context in self._clients.values()
            if context.active
        ]
    
    def get_clients_due_for_tweet(self) -> List[ClientContext]:
        """Get clients that are due for a new tweet based on their schedule.
        
        Returns:
            List of client contexts due for tweets
        """
        now = datetime.utcnow()
        due_clients = []
        
        for client_id, context in self._clients.items():
            if not context.active:
                continue
                
            # Get client data from DB for latest schedule
            client = self.db.get_client(client_id)
            if not client:
                continue
            
            # Convert current time to client's timezone
            client_tz = pytz.timezone(client.timezone)
            client_time = now.astimezone(client_tz)
            current_hour = client_time.hour
            
            # Check if current hour is in posting schedule
            if current_hour in client.posting_hours:
                # If no previous tweet or last tweet was in a different hour
                if (not context.last_tweet_at or
                    context.last_tweet_at.astimezone(client_tz).hour != current_hour):
                    due_clients.append(context)
        
        return due_clients
    
    async def close(self) -> None:
        """Clean up all clients."""
        for client_id in list(self._clients.keys()):
            await self.remove_client(client_id)
        
        self.logger.info("Closed all clients") 