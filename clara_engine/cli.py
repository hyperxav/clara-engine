"""Command line interface for Clara Engine."""

import asyncio
import os
import sys
from typing import Optional
import click
import structlog
from dotenv import load_dotenv

from clara_engine.core.engine import ClaraEngine, EngineConfig
from clara_engine.models import ClientCreate, ClientUpdate
from clara_engine.db import Database

# Configure logging
logger = structlog.get_logger()

# Load environment variables
load_dotenv()

@click.group()
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
def cli(debug: bool):
    """Clara Engine - Multi-tenant AI Twitter Bot Platform."""
    if debug:
        # Configure debug logging
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(min_level="DEBUG")
        )

@cli.command()
@click.option("--redis-url", default="redis://localhost:6379/0", help="Redis URL for rate limiting")
@click.option("--check-interval", default=60, help="Scheduler check interval in seconds")
@click.option("--batch-size", default=10, help="Maximum tweets to process in parallel")
def start(redis_url: str, check_interval: int, batch_size: int):
    """Start the Clara Engine."""
    try:
        config = EngineConfig(
            redis_url=redis_url,
            scheduler={"check_interval": check_interval, "batch_size": batch_size}
        )
        engine = ClaraEngine(config)
        
        # Run the engine
        asyncio.run(engine.start())
        
    except KeyboardInterrupt:
        click.echo("\nShutting down gracefully...")
        asyncio.run(engine.shutdown())
    except Exception as e:
        click.echo(f"Error starting engine: {e}", err=True)
        sys.exit(1)

@cli.group()
def client():
    """Manage Twitter clients."""
    pass

@client.command(name="list")
@click.option("--active-only/--all", default=True, help="Show only active clients")
def list_clients(active_only: bool):
    """List all registered clients."""
    try:
        db = Database()
        clients = db.get_active_clients() if active_only else db.get_all_clients()
        
        if not clients:
            click.echo("No clients found.")
            return
            
        for client in clients:
            status = "🟢" if client.active else "⚫️"
            last_post = client.last_posted_at.strftime("%Y-%m-%d %H:%M:%S") if client.last_posted_at else "Never"
            click.echo(f"{status} {client.name} (ID: {client.id})")
            click.echo(f"  Last posted: {last_post}")
            click.echo(f"  Timezone: {client.timezone}")
            click.echo(f"  Posting hours: {', '.join(map(str, client.posting_hours))}")
            click.echo()
            
    except Exception as e:
        click.echo(f"Error listing clients: {e}", err=True)
        sys.exit(1)

@client.command()
@click.argument("name")
@click.option("--persona", prompt=True, help="Persona prompt for the client")
@click.option("--twitter-key", prompt=True, help="Twitter API key")
@click.option("--twitter-secret", prompt=True, hide_input=True, help="Twitter API secret")
@click.option("--access-token", prompt=True, help="Twitter access token")
@click.option("--access-secret", prompt=True, hide_input=True, help="Twitter access token secret")
@click.option("--timezone", default="UTC", help="Client timezone")
@click.option("--posting-hours", help="Comma-separated list of posting hours (0-23)")
def add(
    name: str,
    persona: str,
    twitter_key: str,
    twitter_secret: str,
    access_token: str,
    access_secret: str,
    timezone: str,
    posting_hours: Optional[str]
):
    """Add a new client."""
    try:
        hours = [int(h) for h in posting_hours.split(",")] if posting_hours else []
        
        client = ClientCreate(
            name=name,
            persona_prompt=persona,
            twitter_key=twitter_key,
            twitter_secret=twitter_secret,
            access_token=access_token,
            access_secret=access_secret,
            timezone=timezone,
            posting_hours=hours
        )
        
        db = Database()
        created = db.create_client(client)
        
        click.echo(f"Successfully created client {created.name} (ID: {created.id})")
        
    except Exception as e:
        click.echo(f"Error creating client: {e}", err=True)
        sys.exit(1)

@client.command()
@click.argument("client_id")
@click.option("--name", help="New client name")
@click.option("--persona", help="New persona prompt")
@click.option("--active/--inactive", help="Set client active status")
@click.option("--timezone", help="New timezone")
@click.option("--posting-hours", help="New comma-separated list of posting hours (0-23)")
def update(
    client_id: str,
    name: Optional[str],
    persona: Optional[str],
    active: Optional[bool],
    timezone: Optional[str],
    posting_hours: Optional[str]
):
    """Update an existing client."""
    try:
        updates = ClientUpdate(
            name=name,
            persona_prompt=persona,
            active=active,
            timezone=timezone,
            posting_hours=[int(h) for h in posting_hours.split(",")] if posting_hours else None
        )
        
        db = Database()
        updated = db.update_client(client_id, updates)
        
        if updated:
            click.echo(f"Successfully updated client {updated.name}")
        else:
            click.echo(f"Client {client_id} not found", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error updating client: {e}", err=True)
        sys.exit(1)

@client.command()
@click.argument("client_id")
@click.option("--force/--no-force", default=False, help="Force deletion without confirmation")
def remove(client_id: str, force: bool):
    """Remove a client."""
    try:
        if not force:
            if not click.confirm(f"Are you sure you want to delete client {client_id}?"):
                click.echo("Operation cancelled.")
                return
        
        db = Database()
        if db.delete_client(client_id):
            click.echo(f"Successfully deleted client {client_id}")
        else:
            click.echo(f"Client {client_id} not found", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error deleting client: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option("--watch/--no-watch", default=False, help="Watch status in real-time")
@click.option("--interval", default=5, help="Refresh interval in seconds for watch mode")
def status(watch: bool, interval: int):
    """Show Clara Engine status."""
    async def check_status():
        try:
            engine = ClaraEngine()
            while True:
                status = await engine.health_check()
                click.clear()
                click.echo("Clara Engine Status")
                click.echo("==================")
                click.echo(f"Running: {'🟢' if status.running else '🔴'}")
                click.echo(f"Scheduler: {'🟢' if status.scheduler_running else '🔴'}")
                click.echo(f"Active Clients: {status.active_clients}")
                click.echo("\nComponent Health:")
                for component, healthy in status.components_healthy.items():
                    click.echo(f"  {component}: {'🟢' if healthy else '🔴'}")
                click.echo("\nMetrics:")
                for key, value in status.metrics.items():
                    click.echo(f"  {key}: {value}")
                    
                if not watch:
                    break
                    
                await asyncio.sleep(interval)
                
        except Exception as e:
            click.echo(f"Error checking status: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(check_status())

if __name__ == "__main__":
    cli() 