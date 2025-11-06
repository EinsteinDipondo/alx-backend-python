import asyncio
import sqlite3
import aiosqlite # Assuming this library is installed and available
from datetime import datetime
import time

# --- Configuration ---
DB_FILE = 'users.db'

# --- 1. Synchronous Database Setup ---
def setup_database():
    """Initializes the database and populates the users table with age data."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                joined_at TEXT
            )
        """)
        
        # Insert sample data, including users older than 40
        data = [
            ('Young Alice', 22, datetime.now().isoformat()),
            ('Mature Bob', 35, datetime.now().isoformat()),
            ('Experienced Charlie', 41, datetime.now().isoformat()), # Older than 40
            ('Veteran David', 55, datetime.now().isoformat()),       # Older than 40
            ('Fresh Eve', 19, datetime.now().isoformat()),
        ]
        
        cursor.executemany("INSERT INTO users (name, age, joined_at) VALUES (?, ?, ?)", data)
        
        conn.commit()
        conn.close()
        print(f"[SETUP] Database '{DB_FILE}' initialized with test data.")
    except Exception as e:
        print(f"[SETUP ERROR] Could not initialize database: {e}")

# =============================================================
# 🎯 SOLUTION: Asynchronous Query Functions
# =============================================================

async def async_fetch_users(conn):
    """
    Asynchronous function to fetch all users.
    Takes an open aiosqlite connection object.
    """
    start_time = time.time()
    await asyncio.sleep(0.1) # Simulate some network/processing delay
    
    print(f"\n[QUERY_1] Starting fetch_all_users...")
    
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT name, age FROM users")
        results = await cursor.fetchall()
    
    duration = (time.time() - start_time) * 1000
    print(f"[QUERY_1] Completed fetch_all_users in {duration:.2f}ms.")
    return "All Users", results

async def async_fetch_older_users(conn):
    """
    Asynchronous function to fetch users older than 40.
    Takes an open aiosqlite connection object.
    """
    start_time = time.time()
    await asyncio.sleep(0.2) # Simulate slightly longer network/processing delay
    
    print(f"\n[QUERY_2] Starting fetch_older_users...")
    
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT name, age FROM users WHERE age > ?", (40,))
        results = await cursor.fetchall()
        
    duration = (time.time() - start_time) * 1000
    print(f"[QUERY_2] Completed fetch_older_users in {duration:.2f}ms.")
    return "Users > 40", results

async def fetch_concurrently():
    """
    The main asynchronous runner that executes multiple queries concurrently
    using a single aiosqlite connection context manager.
    """
    print(f"\n[CONCURRENT] Starting concurrent query execution...")
    
    total_start_time = time.time()
    
    # Use the aiosqlite context manager for the connection
    async with aiosqlite.connect(DB_FILE) as db:
        
        # Use asyncio.gather to run both fetch functions simultaneously
        # We pass the shared 'db' connection object to both tasks
        results = await asyncio.gather(
            async_fetch_users(db),
            async_fetch_older_users(db)
        )
        
    total_duration = (time.time() - total_start_time) * 1000
    print(f"\n[CONCURRENT] All queries finished. Total execution time: {total_duration:.2f}ms")
    
    # Results is a list of tuples: [('All Users', [...]), ('Users > 40', [...])]
    return results

# =============================================================
# 🚀 Execution
# =============================================================

if __name__ == '__main__':
    # 1. Setup synchronous database
    setup_database()
    
    # 2. Run the asynchronous main function
    try:
        final_results = asyncio.run(fetch_concurrently())
        
        print("\n" + "="*50)
        print("Final Consolidated Results:")
        print("="*50)
        
        # Display the results from the concurrent run
        for title, data in final_results:
            print(f"\n--- {title} ---")
            if data:
                for name, age in data:
                    print(f"Name: {name:<20} | Age: {age}")
            else:
                print("No results found.")

    except ImportError:
        print("\n[ERROR] The 'aiosqlite' library is required but not installed.")
        print("Please install it: pip install aiosqlite")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] An unexpected error occurred during execution: {e}")
