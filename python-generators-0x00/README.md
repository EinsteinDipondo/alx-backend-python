# alx-backend-python

This repository contains Python scripts for backend development, specifically focusing on database interaction using MySQL.

## Features and Functionality

This project provides functionality to:

*   Connect to a MySQL database.
*   Create a database named `ALX_prodev` if it doesn't exist.
*   Create a table named `user_data` within the `ALX_prodev` database to store user information.
*   Insert data from a CSV file into the `user_data` table.
*   Generate UUIDs for each user in the database.
*   Handle potential errors during database connection, creation, and data insertion.

## Technology Stack

*   Python 3
*   MySQL
*   `mysql-connector-python` library
*   `csv` module
*   `uuid` module

## Prerequisites

Before running the scripts, ensure you have the following:

*   Python 3 installed on your system.
*   MySQL server installed and running.
*   `mysql-connector-python` library installed.  Install using: `pip install mysql-connector-python`
*   A CSV file containing user data in the format: `name,email,age`.  The `seed.py` script expects the CSV file path as an argument.

## Installation Instructions

1.  Clone the repository:

    ```bash
    git clone https://github.com/EinsteinDipondo/alx-backend-python.git
    cd alx-backend-python
    ```

2.  Install the required Python packages (if not already installed):

    ```bash
    pip install mysql-connector-python
    ```

## Usage Guide

The primary script for this project is `python-generators-0x00/seed.py`.  This script handles the database connection, creation, table creation, and data insertion.

1.  **Configure Database Credentials:**

    Modify the `seed.py` script to reflect your MySQL credentials. Specifically, update the `user` and `password` parameters in the `connect_db()` and `connect_to_prodev()` functions:

    ```python
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

    ```

2.  **Prepare your CSV data file.**

    Make sure you have your CSV file ready with the data following the `name,email,age` format.  Example `data.csv`:

    ```csv
    John Doe,john.doe@example.com,30
    Jane Smith,jane.smith@example.com,25
    Peter Jones,peter.jones@example.com,40
    ```

3.  **Run the script:**

    Execute the `seed.py` script, providing the path to your CSV file as an argument.  Example:

    ```bash
    python3 python-generators-0x00/seed.py data.csv
    ```
    Note: The data.csv in the command above is just an example. The actual file path to your CSV file should be provided.  You'll need to modify `seed.py` itself to take a CSV file path as a command line argument and pass it to the `insert_data` function.  Here's how you could modify `seed.py`:

    ```python
    #!/usr/bin/python3
    import mysql.connector
    import csv
    import uuid
    from mysql.connector import Error
    import sys  # Import the sys module

    # (Database connection and table creation functions - same as before)

    def main():
        if len(sys.argv) != 2:
            print("Usage: seed.py <csv_file_path>")
            sys.exit(1)

        csv_file_path = sys.argv[1]

        connection = connect_db()
        if connection:
            create_database(connection)
            prodev_connection = connect_to_prodev()
            if prodev_connection:
                create_table(prodev_connection)
                insert_data(prodev_connection, csv_file_path)
                prodev_connection.close()
            connection.close()

    if __name__ == "__main__":
        main()
    ```

    Now you can run it as intended: `python3 python-generators-0x00/seed.py path/to/your/data.csv`

4.  **Verify Data Insertion:**

    Connect to your MySQL server and query the `user_data` table to verify that the data has been successfully inserted.

    ```sql
    mysql -u root -p ALX_prodev
    SELECT * FROM user_data;
    ```

## API Documentation

This project does not expose an API. It primarily focuses on database seeding.

## Contributing Guidelines

Contributions are welcome! To contribute to this project, follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Implement your changes.
4.  Test your changes thoroughly.
5.  Submit a pull request with a clear description of your changes.

## License Information

No license specified. All rights reserved.

## Contact/Support Information

For questions or support, please contact [EinsteinDipondo](https://github.com/EinsteinDipondo).
