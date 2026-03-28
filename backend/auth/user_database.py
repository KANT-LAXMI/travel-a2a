"""
Database Initialization
=======================
Creates and initializes the PostgreSQL database.

This module sets up the database schema and creates
the necessary tables for the application.
"""

import psycopg2
from backend.config import Config


def init_database():
    """
    Initialize the PostgreSQL database.
    
    Creates the users table if it doesn't exist.
    
    Table Schema:
        - id: Primary key, auto-increment (SERIAL)
        - first_name: User's first name (required)
        - last_name: User's last name (required)
        - email: User's email address (unique, required)
        - password_hash: Bcrypt hashed password (required)
        - created_at: Account creation timestamp (auto-generated)
    
    Indexes:
        - email: For fast user lookup during login
    """
    conn = psycopg2.connect(Config.DATABASE_URL)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(255) NOT NULL,
            last_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index on email for faster lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_users_email 
        ON users(email)
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"[OK] Database initialized")


if __name__ == '__main__':
    # Run this file directly to initialize the database
    init_database()
