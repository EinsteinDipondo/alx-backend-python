import sqlite3
import functools
import logging

# Set up logging to include timestamps automatically
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log_queries(func):
    """Decorator that logs SQL queries before executing them"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract query from keyword arguments or first positional argument
        query = kwargs.get('query') or (args[0] if args else None)
        
        if query:
            logger.info(f"Executing SQL query: {query}")
        else:
            logger.warning("No query parameter found")
        
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

# Example usage
if __name__ == "__main__":
    # Create sample database for testing
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT
        )
    """)
    # Insert sample data if not exists
    cursor.execute("INSERT OR IGNORE INTO users (name, email) VALUES ('John Doe', 'john@example.com')")
    cursor.execute("INSERT OR IGNORE INTO users (name, email) VALUES ('Jane Smith', 'jane@example.com')")
    conn.commit()
    conn.close()
    
    # Fetch users while logging the query
    users = fetch_all_users(query="SELECT * FROM users")
    print(f"Fetched {len(users)} users")
