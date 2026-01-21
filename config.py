import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "student_management"),
        "port": int(os.getenv("DB_PORT", "3306")),
    }

def get_connection():
    """Get local MySQL connection"""
    try:
        conn = mysql.connector.connect(**get_db_config())
        return conn
    except mysql.connector.Error as e:
        print(f"❌ Local MySQL Error: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Is MySQL running? (Run 'mysql' in terminal)")
        print("2. Check .env file for correct password")
        print("3. Try: sudo service mysql start (Linux/Mac)")
        print("4. Try: net start mysql (Windows)")
        return None

def fetch_details(query, params=None):
    """Execute SELECT query"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        return result
    except Exception as e:
        print(f"❌ Query Error: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def execute_query(query, params=None):
    """Execute INSERT/UPDATE/DELETE query"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Query Error: {e}")
        if conn and conn.is_connected():
            conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Test connection
if __name__ == "__main__":
    print("🔍 Testing local MySQL connection...")
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE()")
        db = cursor.fetchone()[0]
        print(f"✅ Connected to database: {db}")
        
        # Show tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"📊 Tables found: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
    else:
        print("❌ Could not connect to local MySQL")