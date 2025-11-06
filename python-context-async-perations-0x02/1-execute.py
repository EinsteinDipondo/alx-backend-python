import sqlite3
import functools

# Configuration for the database file
DB_FILE = 'users.db'

# --- 1. Database Setup Function ---
def setup_database():
    """Ensures the users.db file and the users table exist with appropriate data."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Drop and re-create the table for a clean run
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER
            )
        """)
        
        # Insert sample data for testing the WHERE age > 25 query
        cursor.execute("INSERT INTO users (name, age) VALUES ('Young Alice', 22)")
        cursor.execute("INSERT INTO users (name, age) VALUES ('Mature Bob', 35)")
        cursor.execute("INSERT INTO users (name, age) VALUES ('Experienced Charlie', 41)")
        cursor.execute("INSERT INTO users (name, age) VALUES ('Fresh David', 19)")
        
        conn.commit()
        conn.close()
        print(f"[SETUP] Database '{DB_FILE}' initialized with test data.")
    except Exception as e:
        print(f"[SETUP ERROR] Could not initialize database: {e}")

# =============================================================
# 🎯 SOLUTION: ExecuteQuery Context Manager
# =============================================================

class ExecuteQuery:
    """
    A class-based context manager for executing a specific query 
    with parameters, managing the connection lifecycle and returning results.
    """
    def __init__(self, db_file, query, params=()):
        self.db_file = db_file
        self.query = query
        # Ensure params is a tuple, as required by cursor.execute
        self.params = params if isinstance(params, tuple) else (params,)
        self.conn = None
        self.results = None

    def __enter__(self):
        """
        Opens the database connection, executes the query, and stores results.
        """
        print(f"[MANAGER] Entering context: Connecting to {self.db_file}")
        try:
            self.conn = sqlite3.connect(self.db_file)
            # Use sqlite3.Row for easy access to column names
            self.conn.row_factory = sqlite3.Row 
            cursor = self.conn.cursor()
            
            print(f"[QUERY] Executing: {self.query} with parameters {self.params}")
            
            # Execute the query using the bound parameters
            cursor.execute(self.query, self.params)
            
            # Fetch and store results only if it was a SELECT query
            if self.query.strip().upper().startswith('SELECT'):
                self.results = cursor.fetchall()
            else:
                self.results = cursor.rowcount
            
            # Return the stored results object to the 'as' variable in the with statement
            return self.results

        except Exception as e:
            # If connection or execution fails, store the exception and let __exit__ handle cleanup
            print(f"[ERROR] Query execution failed: {e}")
            self.results = None # Clear results on error
            raise # Re-raise the exception

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Handles commit/rollback and ensures the connection is closed.
        """
        if self.conn:
            if exc_type is None:
                # Success: commit all changes
                self.conn.commit()
                print("[MANAGER] Transaction committed.")
            else:
                # Failure: rollback all changes
                self.conn.rollback()
                print(f"[MANAGER] Transaction rolled back.")
            
            self.conn.close()
            print("[MANAGER] Connection closed.")

        # If an exception occurred, we want to let Python propagate it (by returning False/None)
        return False 

# =============================================================
# 🚀 Usage Example
# =============================================================

if __name__ == '__main__':
    # 1. Initialize the database
    setup_database()
    
    # Define the required query and parameter
    QUERY = "SELECT * FROM users WHERE age > ?"
    AGE_THRESHOLD = 25
    
    print("\n--- Executing Query with ExecuteQuery Context Manager ---")
    
    try:
        # 2. Use the custom context manager
        with ExecuteQuery(DB_FILE, QUERY, AGE_THRESHOLD) as users_over_25:
            
            print("\nQuery Results:")
            if users_over_25:
                # Print headers
                print(f"{'ID':<5} {'Name':<25} {'Age':<5}")
                print("-" * 35)
                # Print rows
                for row in users_over_25:
                    # Access data using the column name because of row_factory setting
                    print(f"{row['id']:<5} {row['name']:<25} {row['age']:<5}")
            else:
                print("No users found matching the criteria.")
        
    except Exception:
        # Catches any error that was propagated by the context manager
        print("\n[CONTEXT] The main execution block finished with an error.")
