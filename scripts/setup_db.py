"""Script to set up the database using Supabase REST API."""

import os
from pathlib import Path
from dotenv import load_dotenv
import requests
import json

def setup_database():
    """Set up the database with required functions and permissions."""
    load_dotenv()
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: Missing Supabase credentials")
        return False
    
    try:
        # Read the SQL file
        migrations_dir = Path(__file__).parent.parent / "migrations"
        with open(migrations_dir / "002_add_exec_sql_function.sql", "r") as f:
            sql = f.read()
        
        print("\nCreating exec_sql function...")
        print("-" * 80)
        print(sql)
        print("-" * 80)
        
        # Prepare the request
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        # Make the request to execute SQL
        response = requests.post(
            f"{url}/rest/v1/rpc/exec_sql",
            headers=headers,
            json={"sql": sql}
        )
        
        if response.status_code == 200:
            print("exec_sql function created successfully!")
            return True
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

if __name__ == "__main__":
    setup_database() 