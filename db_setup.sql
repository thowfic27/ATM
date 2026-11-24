-- Create database
CREATE DATABASE IF NOT EXISTS atm_db;

USE atm_db;

-- Users table (login credentials + account info)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    account_number VARCHAR(12) NOT NULL UNIQUE,
    balance DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table (for mini-statement)
CREATE TABLE IF NOT EXISTS transactions (
    txn_id INT AUTO_INCREMENT PRIMARY KEY,
    account_number VARCHAR(12) NOT NULL,
    txn_type ENUM (
        'DEPOSIT',
        'WITHDRAW',
        'TRANSFER_IN',
        'TRANSFER_OUT'
    ) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    balance_after DECIMAL(12, 2) NOT NULL,
    txn_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_number) REFERENCES users (account_number)
);