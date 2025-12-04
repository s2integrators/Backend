# filepath: migrate_bin.py
import mysql.connector
from app.core.config import DB_CONFIG 

def add_bin_columns():
    print("🔌 Connecting to Database...")
    conn = None
    try:
        # Connect using your existing config
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🛠️  Checking 'resumes' table...")
        
        # 1. Add is_deleted column
        try:
            cursor.execute("SELECT is_deleted FROM resumes LIMIT 1")
            print("   - 'is_deleted' column already exists.")
        except:
            print("   - Adding 'is_deleted' column...")
            cursor.execute("ALTER TABLE resumes ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE")
            
        # 2. Add deleted_at column
        try:
            cursor.execute("SELECT deleted_at FROM resumes LIMIT 1")
            print("   - 'deleted_at' column already exists.")
        except:
            print("   - Adding 'deleted_at' column...")
            cursor.execute("ALTER TABLE resumes ADD COLUMN deleted_at DATETIME NULL")

        # 3. Update existing rows
        print("   - Setting default values for existing records...")
        cursor.execute("UPDATE resumes SET is_deleted = FALSE WHERE is_deleted IS NULL")

        conn.commit()
        print("\n✅ SUCCESS: Database updated! You can now use the Bin.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_bin_columns()
