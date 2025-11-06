import time
import sqlite3 
import functools

# Global cache dictionary
query_cache = {}

def with_db_connection(func):
    """Decorator that automatically handles database connections"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Open a database connection
        conn = sqlite3.connect('users.db')
        try:
            # Pass the connection to the function and execute
            result = func(conn, *args, **kwargs)
            return result
        finally:
            # Always close the connection
            conn.close()
    
    return wrapper

def cache_query(func):
    """
    Decorator that caches the results of database queries to avoid redundant calls
    
    Caches results based on the SQL query string
    """
    @functools.wraps(func)
    def wrapper(conn, query):
        # Use the query string as the cache key
        cache_key = query
        
        # Check if result is already cached
        if cache_key in query_cache:
            print(f"Cache hit for query: {query}")
            return query_cache[cache_key]
        else:
            print(f"Cache miss for query: {query}")
            # Execute the query and cache the result
            result = func(conn, query)
            query_cache[cache_key] = result
            print("Query result cached")
            return result
    
    return wrapper

@with_db_connection
@cache_query
def fetch_users_with_cache(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

#### First call will cache the result
users = fetch_users_with_cache(query="SELECT * FROM users")
print(f"First call returned {len(users)} users")

#### Second call will use the cached result
users_again = fetch_users_with_cache(query="SELECT * FROM users")
print(f"Second call returned {len(users_again)} users")

#### Different query will not use cache
different_users = fetch_users_with_cache(query="SELECT * FROM users WHERE id = 1")
print(f"Different query returned {len(different_users)} users")
