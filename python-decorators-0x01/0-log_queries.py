import sqlite3
import functools
import time # Added for execution time logging, which is useful in real-world logging

def log_queries(func):
    """
    Decorator that logs the SQL query being executed by the decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        
        # 1. Identify the Query
        # The query is expected to be passed as an argument (either positional or keyword).
        # We'll assume the SQL query is one of the arguments.
        
        query = None
        
        # Check positional arguments for a string that looks like a query
        if args and isinstance(args[0], str):
            query = args[0]
        # Check keyword arguments (specifically the 'query' keyword from the example call)
        elif 'query' in kwargs:
            query = kwargs['query']
        
        # 2. Log the Query (and function name)
        if query:
            print(f"\n[DB_LOG] ----------------------------------------")
            print(f"[DB_LOG] Function: **{func.__name__}**")
            print(f"[DB_LOG] Executing SQL: **{query}**")
            print(f"[DB_LOG] ----------------------------------------")
        else:
            print(f"[DB_LOG] Function **{func.__name__}** executed, but no explicit query argument found.")

        # 3. Execute the original function and measure time (optional but good practice)
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # 4. Log Execution Time
        duration = (end_time - start_time) * 1000 # in milliseconds
        print(f"[DB_LOG] Execution Time: **{duration:.2f}ms**")
        
        return result
    return wrapper

@log_queries
def fetch_all_users(query):
    # This block requires a database file 'users.db' to exist for a successful run
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except sqlite3.OperationalError as e:
        # Handle case where the users.db file or table doesn't exist
        print(f"[ERROR] Database error: {e}. Please ensure 'users.db' is set up.")
        return []

# --- Example Usage ---
# NOTE: To run this successfully, ensure you have an SQLite database file named 'users.db' 
# with a table containing user data.
try:
    users = fetch_all_users(query="SELECT * FROM users")
    print(f"\nQuery Results (First 3): {users[:3]}...")
except Exception as e:
    print(f"An unexpected error occurred during execution: {e}")
