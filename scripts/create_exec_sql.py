"""Script to create the exec_sql function in Supabase."""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def create_exec_sql():
    """Create the exec_sql function in Supabase."""
    # Get Supabase credentials
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: Missing Supabase credentials")
        return False
    
    # Initialize Supabase client
    client: Client = create_client(url, key)
    
    try:
        # Read the function SQL
        migrations_dir = Path(__file__).parent.parent / "migrations"
        with open(migrations_dir / "002_add_exec_sql_function.sql", "r") as f:
            sql = f.read()
        
        print("Creating exec_sql function...")
        print("-" * 80)
        print(sql)
        print("-" * 80)
        
        # Execute the SQL as a single statement
        result = client.rpc('exec_sql', {'sql': sql}).execute()
        print(f"\nResult: {result.data}")
        
        return True
        
    except Exception as e:
        print(f"Error creating exec_sql function: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text if hasattr(e.response, 'text') else e.response}")
        return False

if __name__ == "__main__":
    create_exec_sql() 