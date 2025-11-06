import sqlite3
import functools

#### decorator to log SQL queries
def log_queries(func):
    """Decorator that logs SQL queries before executing them"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract the query from keyword arguments
        query = kwargs.get('query')
        
        # Log the SQL query
        print(f"Executing SQL query: {query}")
        
        # Execute the original function
        return func(*args, **kwargs)
    
    return wrapper

@log_queries
def fetch_all_users(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

#### fetch users while logging the query
users = fetch_all_users(query="SELECT * FROM users")
