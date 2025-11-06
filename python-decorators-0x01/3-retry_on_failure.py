import time
import sqlite3 
import functools

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

def retry_on_failure(retries=3, delay=2):
    """
    Decorator that retries database operations if they fail due to transient errors
    
    Args:
        retries: Number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 2)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(retries + 1):  # +1 for the initial attempt
                try:
                    if attempt > 0:
                        print(f"Retry attempt {attempt}/{retries} after {current_delay} seconds...")
                    
                    # Execute the function
                    return func(*args, **kwargs)
                    
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if attempt == retries:
                        print(f"All {retries} retry attempts failed. Last error: {str(e)}")
                        break
                    
                    # Wait before retrying
                    time.sleep(current_delay)
                    # Optional: Increase delay for next retry (exponential backoff)
                    current_delay *= 1.5
                    
                except Exception as e:
                    # Non-retriable exception (syntax errors, etc.)
                    print(f"Non-retriable error: {str(e)}")
                    raise
            
            # If we exhausted all retries, raise the last exception
            raise last_exception
        
        return wrapper
    return decorator

@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_users_with_retry(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()

#### attempt to fetch users with automatic retry on failure
users = fetch_users_with_retry()
print(users)
