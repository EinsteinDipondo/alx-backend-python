#!/usr/bin/python3
import mysql.connector
import csv
import uuid
from mysql.connector import Error

def connect_db():
    """Connect to the MySQL database server"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  # Replace with your MySQL username
            password=''   # Replace with your MySQL password
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

def create_database(connection):
    """Create the database ALX_prodev if it does not exist"""
    try:
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS ALX_prodev")
        print("Database ALX_prodev created or already exists")
        cursor.close()
    except Error as e:
        print(f"Error creating database: {e}")

def connect_to_prodev():
    """Connect to the ALX_prodev database in MySQL"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  # Replace with your MySQL username
            password='',  # Replace with your MySQL password
            database='ALX_prodev'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to ALX_prodev: {e}")
        return None

def create_table(connection):
    """Create a table user_data if it does not exist with the required fields"""
    try:
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                user_id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                age DECIMAL(3,0) NOT NULL,
                INDEX idx_user_id (user_id)
            )
        ''')
        print("Table user_data created successfully")
        cursor.close()
    except Error as e:
        print(f"Error creating table: {e}")

def insert_data(connection, csv_file_path):
    """Insert data from CSV file into the database if it does not exist"""
    try:
        cursor = connection.cursor()
        
        # Check if table already has data
        cursor.execute("SELECT COUNT(*) FROM user_data")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print("Data already exists in the table")
            cursor.close()
            return
        
        # Read and insert data from CSV
        with open(csv_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header row
            
            batch_size = 1000
            batch = []
            
            for row in csv_reader:
                if len(row) >= 3:
                    user_id = str(uuid.uuid4())  # Generate UUID
                    name = row[0]
                    email = row[1]
                    age = int(row[2]) if row[2].isdigit() else 0
                    
                    batch.append((user_id, name, email, age))
                    
                    if len(batch) >= batch_size:
                        cursor.executemany('''
                            INSERT INTO user_data (user_id, name, email, age)
                            VALUES (%s, %s, %s, %s)
                        ''', batch)
                        connection.commit()
                        batch = []
            
            # Insert remaining records
            if batch:
                cursor.executemany('''
                    INSERT INTO user_data (user_id, name, email, age)
                    VALUES (%s, %s, %s, %s)
                ''', batch)
                connection.commit()
        
        print("Data inserted successfully")
        cursor.close()
        
    except Error as e:
        print(f"Error inserting data: {e}")
    except FileNotFoundError:
        print(f"CSV file {csv_file_path} not found")
