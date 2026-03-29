"""
PostgreSQL Connection Test
==========================
Quick test to verify PostgreSQL connection and schema.
"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def test_connection():
    """Test PostgreSQL connection and list tables"""
    print("="*70)
    print("🧪 Testing PostgreSQL Connection")
    print("="*70)
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set in .env file")
        print("\nAdd this to your .env:")
        print("DATABASE_URL=postgresql://user:password@host:port/dbname")
        return False
    
    print(f"\n🔌 Connecting to: {DATABASE_URL[:50]}...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("✅ Connection successful!\n")
        
        # List all tables
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print(f"📊 Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("⚠️  No tables found. Run schema initialization:")
            print("   python -c \"from backend.database.db_manager import TravelBuddyDB; TravelBuddyDB()\"")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("✅ PostgreSQL is ready!")
        print("="*70)
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check DATABASE_URL format")
        print("   2. Verify database credentials")
        print("   3. Ensure PostgreSQL server is running")
        print("   4. Check firewall/network settings")
        return False

if __name__ == "__main__":
    test_connection()
