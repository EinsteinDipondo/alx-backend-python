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
            user='root',  # Replace with your MySQL username
            password='',  # Replace with your MySQL password
            database='ALX_prodev'
        )
        
        if connection.is_connected():
            # Create a server-side cursor
            cursor = connection.cursor(buffered=True)
            
            # Execute query to fetch all users
            cursor.execute("SELECT user_id, name, email, age FROM user_data")
            
            # Loop 1: Fetch batches until no more data
            while True:
                # Fetch a batch of rows
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                
                # Convert batch to list of dictionaries
                batch = []
                # Loop 2: Process rows in current batch
                for row in rows:
                    user_dict = {
                        'user_id': row[0],
                        'name': row[1],
                        'email': row[2],
                        'age': row[3]
                    }
                    batch.append(user_dict)
                
                yield batch
    
    except Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        yield []
    
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def batch_processing(batch_size):
    """
    Processes batches of users and filters those over age 25.
    
    Args:
        batch_size (int): Number of rows to process per batch
    """
    # Loop 3: Iterate through batches from the generator
    for batch in stream_users_in_batches(batch_size):
        # Process each user in the current batch
        for user in batch:
            # Filter users over age 25
            if user['age'] > 25:
                print(user)
