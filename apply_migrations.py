"""Script to apply database migrations to Supabase."""
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

def apply_migrations():
    """Apply migrations in the correct order."""
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: Missing Supabase credentials")
        return
    
    print(f"Connecting to Supabase at {url}")
    
    try:
        # Initialize Supabase client
        client: Client = create_client(url, key)
        
        # Migration files in order
        migrations = [
            "002_add_exec_sql_function.sql",  # Must be first as other migrations depend on it
            "001_initial_schema.sql",
        ]
        
        # Apply each migration
        for migration in migrations:
            migration_path = Path("migrations") / migration
            
            if not migration_path.exists():
                print(f"Error: Migration file not found: {migration_path}")
                continue
                
            print(f"\nApplying migration: {migration}")
            print(f"Reading from: {migration_path.absolute()}")
            
            # Read migration file
            with open(migration_path, "r") as f:
                sql = f.read()
            
            # Split into individual statements
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            print(f"Found {len(statements)} SQL statements to execute")
            
            # Execute each statement
            for i, statement in enumerate(statements, 1):
                try:
                    print(f"\nExecuting SQL statement {i}/{len(statements)}:")
                    print("-" * 80)
                    print(statement)
                    print("-" * 80)
                    
                    result = client.rpc('exec_sql', {'sql': statement}).execute()
                    
                    # Pretty print the result
                    result_str = json.dumps(result.data, indent=2) if result.data else "No data returned"
                    print(f"\nResult: {result_str}")
                    
                except Exception as e:
                    print(f"Error executing statement {i}: {e}")
                    if hasattr(e, 'response'):
                        print(f"Response: {e.response.text if hasattr(e.response, 'text') else e.response}")
                    # Continue with next statement
            
        print("\nMigrations completed!")
        
    except Exception as e:
        print(f"Error applying migrations: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text if hasattr(e.response, 'text') else e.response}")

if __name__ == "__main__":
    apply_migrations() 