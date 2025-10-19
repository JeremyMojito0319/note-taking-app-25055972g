import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import OperationalError

# Load environment variables from .env file
load_dotenv()

def test_supabase_connection():
    """Test connection to Supabase database."""
    DATABASE_URL = os.environ.get('DATABASE_URL')

    if not DATABASE_URL:
        print("Error: DATABASE_URL is not set in the environment variables.")
        return

    # Replace 'postgres://' with 'postgresql://' for compatibility with psycopg2
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    try:
        # Attempt to connect to the database
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        print("Success: Connected to the Supabase database.")
    except OperationalError as e:
        print("Error: Failed to connect to the Supabase database.")
        print("Details:", e)

if __name__ == "__main__":
    test_supabase_connection()