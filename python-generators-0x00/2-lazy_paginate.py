#!/usr/bin/python3
import seed

def paginate_users(page_size, offset):
    """
    Function to fetch a page of users from the database.
    
    Args:
        page_size (int): Number of users per page
        offset (int): Starting position for the page
        
    Returns:
        list: List of user dictionaries
    """
    connection = seed.connect_to_prodev()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM user_data LIMIT {page_size} OFFSET {offset}")
    rows = cursor.fetchall()
    connection.close()
    return rows

def lazy_paginate(page_size):
    """
    Generator function that implements lazy pagination.
    Only fetches the next page when needed.
    
    Args:
        page_size (int): Number of users per page
        
    Yields:
        list: A page of user dictionaries
    """
    offset = 0
    
    # Single loop as required
    while True:
        # Fetch the next page
        page = paginate_users(page_size, offset)
        
        # If the page is empty, we've reached the end
        if not page:
            break
        
        # Yield the current page
        yield page
        
        # Move to the next page
        offset += page_size
