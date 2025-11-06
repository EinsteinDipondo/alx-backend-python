import sqlite3
import functools
from datetime import datetime # <-- Added this import

def log_queries(func):
    """
    Decorator that logs the SQL query, timestamp, and execution time.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        
        # 1. Identify the Query and Capture Start Time/Timestamp
        start_datetime = datetime.now() # Capture the exact start time
        start_time = start_datetime.timestamp() # Use timestamp for duration calculation
        
        query = None
        if args and isinstance(args[0], str):
            query = args[0]
        elif 'query' in kwargs:
            query = kwargs['query']
        
        # 2. Log the Query details including the full timestamp
        print(f"\n[DB_LOG] ----------------------------------------")
        print(f"[DB_LOG] Timestamp: {start_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        print(f"[DB_LOG] Function: **{func.__name__}**")
        
        if query:
            print(f"[DB_LOG] Executing SQL: **{query}**")
        else:
            print(f"[DB_LOG] No explicit query argument found.")

        # 3. Execute the original function
        result = func(*args, **kwargs)
        
        # 4. Log Execution Time
        end_time = datetime.now().timestamp()
        duration = (end_time - start_time) * 1000 # in milliseconds
        print(f"[DB_LOG] Execution Time: **{duration:.2f}ms**")
        print(f"[DB_LOG] ----------------------------------------")
        
        return result
    return wrapper

@log_queries
def fetch_all_users(query):
    # This block requires a database file 'users.db' to exist for a successful run
    try:
        # Simulate connection and query execution time
        conn = sqlite3.connect('users.db') 
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except sqlite3.OperationalError as e:
        print(f"[ERROR] Database error: {e}. Please ensure 'users.db' is set up.")
        return []

# --- Example Usage ---
# Ensure 'users.db' is set up for testing
try:
    users = fetch_all_users(query="SELECT * FROM users")
    print(f"\nQuery Results (First 3): {users[:3]}...")
except Exception as e:
    # Catch any general exceptions
    pass
