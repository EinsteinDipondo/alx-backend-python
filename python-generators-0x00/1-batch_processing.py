#!/usr/bin/python3
import mysql.connector
from mysql.connector import Error

def stream_users_in_batches(batch_size):
    """
    Generator function that fetches rows from user_data table in batches.
    
    Args:
        batch_size (int): Number of rows to fetch per batch
        
    Yields:
        list: A list of dictionaries, each containing user data
    """
    connection = None
    cursor = None
    
    try:
        # Establish database connection
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='ALX_prodev'
        )
        
        if connection.is_connected():
            cursor = connection.cursor(buffered=True)
            cursor.execute("SELECT user_id, name, email, age FROM user_data")
            
            # Loop 1: Main batch fetching loop
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                batch = []
                # Loop 2: Convert rows to dictionaries
                for row in rows:
                    batch.append({
                        'user_id': row[0],
                        'name': row[1],
                        'email': row[2],
                        'age': row[3]
                    })
                
                yield batch
    
    except Error as e:
        print(f"Database error: {e}")
        # Yield an empty batch on error
        yield []
    
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def batch_processing(batch_size):
    """
    Generator function that processes batches and yields users over age 25.
    
    Args:
        batch_size (int): Number of rows to process per batch
        
    Yields:
        dict: User data for users over age 25
    """
    batch_count = 0
    users_yielded = 0
    
    # Loop 3: Iterate through batches from generator
    for batch in stream_users_in_batches(batch_size):
        batch_count += 1
        
        # Process each user in current batch
        for user in batch:
            if user['age'] > 25:
                users_yielded += 1
                yield user
