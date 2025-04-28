"""Script to apply database schema to Supabase."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

def apply_schema():
    """Apply database schema to Supabase."""
    # Get Supabase credentials
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: Missing Supabase credentials")
        sys.exit(1)
    
    # Initialize Supabase client
    supabase: Client = create_client(url, key)
    
    try:
        # Read schema file
        schema_path = project_root / "migrations" / "001_initial_schema.sql"
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        
        # Split schema into individual statements
        statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
        
        # Execute each statement
        for statement in statements:
            try:
                print(f"\nExecuting:\n{statement}\n")
                # Use the rpc method to execute raw SQL
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                print("Success!")
            except Exception as e:
                print(f"Error executing statement: {e}")
                continue
        
        print("\nSchema applied successfully!")
        
    except Exception as e:
        print(f"Error applying schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_schema() 