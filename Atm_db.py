
import mysql.connector
from mysql.connector import Error

try:
    # Step 1: Connect to MySQL Server
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )

    if connection.is_connected():
        print("MySQL Connected Successfully!")

    cursor = connection.cursor()

    # Step 2: Create Database
    cursor.execute("""
        CREATE DATABASE IF NOT EXISTS atm_db
    """)

    print("Database created successfully!")

    # Step 3: Select Database
    cursor.execute("USE atm_db")

    # Step 4: Create Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            account_number VARCHAR(12) NOT NULL UNIQUE,
            balance DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("Users table created successfully!")

    # Step 5: Create Transactions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            txn_id INT AUTO_INCREMENT PRIMARY KEY,
            account_number VARCHAR(12) NOT NULL,
            txn_type ENUM(
                'DEPOSIT',
                'WITHDRAW',
                'TRANSFER_IN',
                'TRANSFER_OUT'
            ) NOT NULL,
            amount DECIMAL(12, 2) NOT NULL,
            balance_after DECIMAL(12, 2) NOT NULL,
            txn_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (account_number)
            REFERENCES users(account_number)
        )
    """)

    print("Transactions table created successfully!")

    print("\nATM DATABASE SETUP COMPLETED!")

except Error as e:
    print("Error:", e)

finally:
    if 'cursor' in locals():
        cursor.close()

    if 'connection' in locals() and connection.is_connected():
        connection.close()
        print("MySQL Connection Closed.")
