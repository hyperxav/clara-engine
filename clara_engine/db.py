"""Database client for Clara Engine."""

import os
from typing import List, Optional
from uuid import UUID

from dotenv import load_dotenv
from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from .models import Client as ClientModel
from .models import ClientCreate, ClientUpdate, Tweet, TweetCreate, TweetUpdate

# Load environment variables
load_dotenv()

class Database:
    """Database client for Clara Engine."""

    def __init__(self) -> None:
        """Initialize database client."""
        url: str = os.environ.get("SUPABASE_URL", "")
        key: str = os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            raise ValueError("Missing Supabase credentials")
        
        options = ClientOptions(
            postgrest_client_timeout=60,  # 60 seconds timeout
            headers={"X-Client-Info": "clara-engine/0.1.0"}
        )
        
        self.client: Client = create_client(url, key, options)

    def _serialize_model(self, model) -> dict:
        """Serialize a model to a dict, converting UUIDs to strings."""
        data = model.model_dump()
        # Convert UUID fields to strings
        for key, value in data.items():
            if isinstance(value, UUID):
                data[key] = str(value)
        return data

    def get_client(self, client_id: UUID) -> Optional[ClientModel]:
        """Get a client by ID."""
        response = self.client.table("clients").select("*").eq("id", str(client_id)).single().execute()
        return ClientModel.model_validate(response.data) if response.data else None

    def get_active_clients(self) -> List[ClientModel]:
        """Get all active clients."""
        response = self.client.table("clients").select("*").eq("active", True).execute()
        return [ClientModel.model_validate(client) for client in response.data]

    def create_client(self, client: ClientCreate) -> ClientModel:
        """Create a new client."""
        response = self.client.table("clients").insert(self._serialize_model(client)).execute()
        return ClientModel.model_validate(response.data[0])

    def update_client(self, client_id: UUID, client: ClientUpdate) -> Optional[ClientModel]:
        """Update a client."""
        response = self.client.table("clients").update(
            self._serialize_model(client)
        ).eq("id", str(client_id)).execute()
        return ClientModel.model_validate(response.data[0]) if response.data else None

    def delete_client(self, client_id: UUID) -> bool:
        """Delete a client."""
        response = self.client.table("clients").delete().eq("id", str(client_id)).execute()
        return bool(response.data)

    def get_tweet(self, tweet_id: UUID) -> Optional[Tweet]:
        """Get a tweet by ID."""
        response = self.client.table("tweets").select("*").eq("id", str(tweet_id)).single().execute()
        return Tweet.model_validate(response.data) if response.data else None

    def get_client_tweets(self, client_id: UUID, limit: int = 100) -> List[Tweet]:
        """Get tweets for a client."""
        response = self.client.table("tweets").select("*").eq(
            "client_id", str(client_id)
        ).order("created_at", desc=True).limit(limit).execute()
        return [Tweet.model_validate(tweet) for tweet in response.data]

    def create_tweet(self, tweet: TweetCreate) -> Tweet:
        """Create a new tweet."""
        response = self.client.table("tweets").insert(self._serialize_model(tweet)).execute()
        return Tweet.model_validate(response.data[0])

    def update_tweet(self, tweet_id: UUID, tweet: TweetUpdate) -> Optional[Tweet]:
        """Update a tweet."""
        response = self.client.table("tweets").update(
            self._serialize_model(tweet)
        ).eq("id", str(tweet_id)).execute()
        return Tweet.model_validate(response.data[0]) if response.data else None

    def get_pending_tweets(self, limit: int = 10) -> List[Tweet]:
        """Get pending tweets."""
        response = self.client.table("tweets").select("*").eq(
            "status", "pending"
        ).order("created_at").limit(limit).execute()
        return [Tweet.model_validate(tweet) for tweet in response.data] 