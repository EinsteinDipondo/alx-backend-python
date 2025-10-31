#!/usr/bin/python3
import mysql.connector
from mysql.connector import Error

def stream_users():
    """
    Generator function that streams rows from user_data table one by one.
    Uses server-side cursor for memory efficiency.
    
    Yields:
        dict: A dictionary containing user data with keys:
              'user_id', 'name', 'email', 'age'
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
            # Create a server-side cursor for memory efficiency
            cursor = connection.cursor(buffered=True)
            
            # Execute query to fetch all users
            cursor.execute("SELECT user_id, name, email, age FROM user_data")
            
            # Single loop as required - fetch and yield rows one by one
            while True:
                # Fetch one row at a time
                row = cursor.fetchone()
                if row is None:
                    break
                
                # Yield the row as a dictionary
                yield {
                    'user_id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'age': row[3]
                }
    
    except Error as e:
        print(f"Database error: {e}")
        yield None
    
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
