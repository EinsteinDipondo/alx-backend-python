import asyncio
import aiosqlite
from datetime import datetime

async def async_fetch_users():
    """
    Asynchronously fetch all users from the database
    """
    print("Starting to fetch all users...")
    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT * FROM users") as cursor:
            users = await cursor.fetchall()
            print(f"Fetched {len(users)} users")
            return users

async def async_fetch_older_users():
    """
    Asynchronously fetch users older than 40 from the database
    """
    print("Starting to fetch users older than 40...")
    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT * FROM users WHERE age > 40") as cursor:
            users = await cursor.fetchall()
            print(f"Fetched {len(users)} users older than 40")
            return users

async def initialize_database():
    """
    Initialize the database with sample data for testing
    """
    async with aiosqlite.connect('users.db') as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample data
        sample_users = [
            ('Alice Johnson', 'alice@example.com', 28),
            ('Bob Smith', 'bob@example.com', 45),
            ('Charlie Brown', 'charlie@example.com', 35),
            ('Diana Prince', 'diana@example.com', 52),
            ('Evan Wright', 'evan@example.com', 38),
            ('Fiona Gallagher', 'fiona@example.com', 47)
        ]
        
        await db.executemany(
            "INSERT OR IGNORE INTO users (name, email, age) VALUES (?, ?, ?)",
            sample_users
        )
        await db.commit()
        print("Database initialized with sample data")

async def fetch_concurrently():
    """
    Execute both database queries concurrently using asyncio.gather
    """
    print("Starting concurrent database queries...")
    start_time = datetime.now()
    
    # Execute both queries concurrently
    results = await asyncio.gather(
        async_fetch_users(),
        async_fetch_older_users()
    )
    
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    print(f"\nConcurrent execution completed in {execution_time:.2f} seconds")
    
    # Unpack results
    all_users, older_users = results
    
    print(f"Total users: {len(all_users)}")
    print(f"Users older than 40: {len(older_users)}")
    
    return results

async def fetch_sequentially():
    """
    Compare with sequential execution to demonstrate performance benefit
    """
    print("\n" + "="*50)
    print("COMPARISON: Sequential execution")
    print("="*50)
    
    start_time = datetime.now()
    
    # Execute queries sequentially
    all_users = await async_fetch_users()
    older_users = await async_fetch_older_users()
    
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    print(f"Sequential execution completed in {execution_time:.2f} seconds")
    
    return all_users, older_users

# Main execution
if __name__ == "__main__":
    # Initialize database first
    asyncio.run(initialize_database())
    
    print("="*50)
    print("CONCURRENT ASYNCHRONOUS DATABASE QUERIES")
    print("="*50)
    
    # Run concurrent queries
    results = asyncio.run(fetch_concurrently())
    
    # Run sequential for comparison (optional)
    # Uncomment to see the performance difference
    # asyncio.run(fetch_sequentially())
