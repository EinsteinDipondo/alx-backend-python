import sqlite3
import functools
import time

# Configuration for the database file
DB_FILE = 'users.db'

# --- 1. Database Setup Function ---
def setup_database():
    """Ensures the users.db file and the users table exist with some data."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Drop and re-create the table for a clean run
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT
            )
        """)
        
        # Insert sample data
        cursor.execute("INSERT INTO users (name, role) VALUES ('Alice', 'Admin')")
        cursor.execute("INSERT INTO users (name, role) VALUES ('Bob', 'User')")
        cursor.execute("INSERT INTO users (name, role) VALUES ('Charlie', 'Guest')")
        
        conn.commit()
        conn.close()
        print(f"[SETUP] Database '{DB_FILE}' initialized with 3 records.")
    except Exception as e:
        print(f"[SETUP ERROR] Could not initialize database: {e}")

# =============================================================
# 🎯 SOLUTION: Custom Class-Based Context Manager
# =============================================================

class DatabaseConnection:
    """
    A custom context manager for handling synchronous SQLite connections.
    It automatically opens the connection in __enter__ and ensures it is
    closed, committing or rolling back transactions, in __exit__.
    """
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None

    def __enter__(self):
        """
        The entry point of the 'with' statement.
        Opens the connection and returns it.
        """
        print(f"[MANAGER] Opening connection to {self.db_file}...")
        self.conn = sqlite3.connect(self.db_file)
        # Optional: Set row factory to easily access columns by name
        self.conn.row_factory = sqlite3.Row 
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        The exit point of the 'with' statement.
        Handles commit/rollback and ensures the connection is closed.
        """
        if exc_type is None:
            # If no exception occurred, commit the changes
            self.conn.commit()
            print("[MANAGER] Transaction committed.")
        else:
            # If an exception occurred, rollback the transaction
            self.conn.rollback()
            print(f"[MANAGER] Transaction rolled back due to error: {exc_val}")
            
        if self.conn:
            self.conn.close()
            print("[MANAGER] Connection closed.")

        # Return False to re-raise the exception (standard behavior)
        return False 

# =============================================================
# 🚀 Usage Example
# =============================================================

if __name__ == '__main__':
    # 1. Initialize the database
    setup_database()
    
    print("\n--- Executing Query with Context Manager ---")
    
    try:
        # Use the custom context manager with the 'with' statement
        with DatabaseConnection(DB_FILE) as conn:
            cursor = conn.cursor()
            
            # Execute the mandatory query
            cursor.execute("SELECT * FROM users")
            
            results = cursor.fetchall()
            
            # Print the results
            print("\nQuery Results:")
            if results:
                # Print headers
                print(f"{'ID':<5} {'Name':<15} {'Role':<10}")
                print("-" * 30)
                # Print rows
                for row in results:
                    # Access data using the column name because of row_factory setting
                    print(f"{row['id']:<5} {row['name']:<15} {row['role']:<10}")
            else:
                print("No users found.")
        
        # The connection is automatically closed here (via __exit__)
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] The application failed: {e}")
