"""
Quick script to test PostgreSQL database connection.
Run with: python test_db_connection.py
"""

import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/empeff")

print("Testing PostgreSQL connection...")
print(f"Connecting to: {database_url.replace(':postgres@', ':****@')}")  # Hide password

try:
    # Parse the DATABASE_URL
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    # Test query
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    
    print("✅ SUCCESS! Connected to PostgreSQL")
    print(f"PostgreSQL version: {db_version[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print("❌ ERROR: Could not connect to database")
    print(f"Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure PostgreSQL is running")
    print("2. Check your .env file has correct DATABASE_URL")
    print("3. Verify username/password are correct")
    print("4. Ensure database 'empeff' exists")
