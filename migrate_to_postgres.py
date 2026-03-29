"""
Migration Script: SQLite to PostgreSQL
======================================
This script helps migrate data from SQLite to PostgreSQL.
Run this AFTER setting up your PostgreSQL database.
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
SQLITE_DB = "backend/database/travel_buddy.db"
POSTGRES_URL = os.getenv("DATABASE_URL")

def migrate_table(sqlite_conn, postgres_conn, table_name, columns):
    """Migrate a single table from SQLite to PostgreSQL"""
    print(f"\n📦 Migrating table: {table_name}")
    
    # Fetch data from SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"   ⚠️  No data found in {table_name}")
        return
    
    # Insert into PostgreSQL
    postgres_cursor = postgres_conn.cursor()
    placeholders = ', '.join(['%s'] * len(columns))
    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    try:
        postgres_cursor.executemany(query, rows)
        postgres_conn.commit()
        print(f"   ✅ Migrated {len(rows)} rows")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        postgres_conn.rollback()

def main():
    """Main migration function"""
    print("="*70)
    print("🚀 SQLite to PostgreSQL Migration")
    print("="*70)
    
    # Check if SQLite database exists
    if not os.path.exists(SQLITE_DB):
        print(f"❌ SQLite database not found: {SQLITE_DB}")
        return
    
    # Check if PostgreSQL URL is set
    if not POSTGRES_URL:
        print("❌ DATABASE_URL not set in environment variables")
        return
    
    print(f"\n📂 SQLite DB: {SQLITE_DB}")
    print(f"🐘 PostgreSQL: {POSTGRES_URL[:50]}...")
    
    # Connect to databases
    print("\n🔌 Connecting to databases...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    postgres_conn = psycopg2.connect(POSTGRES_URL)
    
    print("✅ Connected successfully")
    
    # Migrate tables in order (respecting foreign keys)
    tables_to_migrate = [
        # Users first
        ("users", ["id", "first_name", "last_name", "email", "password_hash", "created_at"]),
        
        # Travel plans
        ("travel_plans", ["id", "created_at", "updated_at", "user_query", "session_id", 
                         "status", "version", "destination", "duration_days", 
                         "execution_time_ms", "llm_tokens_used", "agents_called",
                         "display_text", "display_format", "error_message"]),
        
        # Budgets
        ("budgets", ["id", "plan_id", "transport", "accommodation", "food", 
                    "activities", "miscellaneous", "total", "leftover", "currency", "created_at"]),
        
        # Itinerary days
        ("itinerary_days", ["id", "plan_id", "day_number", "date", "total_cost", "created_at"]),
        
        # Activities
        ("activities", ["id", "day_id", "time", "title", "description", "cost", 
                       "duration_minutes", "location_name", "location_latitude", 
                       "location_longitude", "location_address", "created_at"]),
        
        # Activity tips
        ("activity_tips", ["id", "activity_id", "tip"]),
        
        # Maps
        ("maps", ["id", "plan_id", "url", "total_locations", "html_content", "created_at"]),
        
        # Map locations
        ("map_locations", ["id", "map_id", "name", "latitude", "longitude", 
                          "day", "time", "description", "image_url"]),
        
        # Knowledge queries
        ("knowledge_queries", ["id", "created_at", "question", "answer", "confidence",
                              "session_id", "execution_time_ms", "display_text"]),
        
        # Knowledge sources
        ("knowledge_sources", ["id", "query_id", "source_name", "page_number", "relevance_score"]),
        
        # Conversation history
        ("conversation_history", ["id", "session_id", "message_number", "role", 
                                 "content", "plan_id", "created_at"]),
        
        # Password reset OTPs
        ("password_reset_otps", ["id", "email", "otp", "created_at", "expires_at", "used"]),
    ]
    
    print("\n" + "="*70)
    print("📊 Starting Migration")
    print("="*70)
    
    for table_name, columns in tables_to_migrate:
        try:
            migrate_table(sqlite_conn, postgres_conn, table_name, columns)
        except Exception as e:
            print(f"❌ Failed to migrate {table_name}: {e}")
    
    # Close connections
    sqlite_conn.close()
    postgres_conn.close()
    
    print("\n" + "="*70)
    print("✅ Migration Complete!")
    print("="*70)
    print("\n💡 Next steps:")
    print("   1. Verify data in PostgreSQL")
    print("   2. Test your application")
    print("   3. Deploy to Vercel")

if __name__ == "__main__":
    main()
