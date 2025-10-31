#!/usr/bin/python3
import mysql.connector
from mysql.connector import Error
import seed

def stream_user_ages():
    """
    Generator function that yields user ages one by one.
    
    Yields:
        int: User age
    """
    connection = None
    cursor = None
    
    try:
        # Connect to database
        connection = seed.connect_to_prodev()
        cursor = connection.cursor()
        
        # Execute query to get only ages
        cursor.execute("SELECT age FROM user_data")
        
        # Loop 1: Stream ages one by one
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row[0]
                
    except Error as e:
        print(f"Database error: {e}")
    
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def calculate_average_age():
    """
    Calculates the average age using the stream_user_ages generator.
    Uses running average calculation to avoid loading all data into memory.
    
    Returns:
        float: Average age of users
    """
    total_age = 0
    count = 0
    
    # Loop 2: Process ages from generator
    for age in stream_user_ages():
        total_age += age
        count += 1
    
    # Calculate average
    if count > 0:
        average_age = total_age / count
        print(f"Average age of users: {average_age:.2f}")
        return average_age
    else:
        print("No users found in database")
        return 0

# Run the calculation when script is executed directly
if __name__ == "__main__":
    calculate_average_age()
