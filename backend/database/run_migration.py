"""
Run database migration to add user_id and PDF columns
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Run the migration SQL script"""
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        sys.exit(1)
    
    print("🔗 Connecting to PostgreSQL database...")
    print(f"   Host: {database_url.split('@')[1].split(':')[0] if '@' in database_url else 'unknown'}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("✅ Connected to database")
        
        # Read migration SQL
        migration_file = os.path.join(os.path.dirname(__file__), 'migrate_add_user_id.sql')
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("\n📝 Running migration...")
        print("=" * 70)
        
        # Execute migration
        cursor.execute(migration_sql)
        conn.commit()
        
        print("✅ Migration completed successfully!")
        print("=" * 70)
        
        # Fetch and display results
        results = cursor.fetchall()
        if results:
            print("\n📊 Verified columns:")
            for row in results:
                print(f"   - {row[0]}: {row[1]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ All done! Database is ready.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_migration()
