"""Test Supabase connection."""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

def test_connection():
    """Test connection to Supabase."""
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: Missing Supabase credentials")
        return
    
    print(f"Testing connection to Supabase at {url}")
    
    try:
        # Initialize Supabase client
        client: Client = create_client(url, key)
        
        # Try a simple query that just selects one column
        response = client.table("clients").select("id").execute()
        
        print("Connection successful!")
        print(f"Query response: {response}")
        
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")

if __name__ == "__main__":
    test_connection() 