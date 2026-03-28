"""
Database Models
===============
PostgreSQL database models for user management.

This module defines the database schema and provides
functions for user operations (create, read, update).
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any
from datetime import datetime
import bcrypt
from backend.config import Config


class User:
    """
    User Model
    
    Represents a user in the database with authentication credentials.
    
    Attributes:
        id (int): Unique user identifier
        first_name (str): User's first name
        last_name (str): User's last name
        email (str): User's email address (unique)
        password_hash (str): Bcrypt hashed password
        created_at (datetime): Account creation timestamp
    """
    
    def __init__(self, id: int, first_name: str, last_name: str, 
                 email: str, password_hash: str, created_at: str):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert user object to dictionary (excluding password).
        
        Returns:
            dict: User data without sensitive information
        """
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'created_at': self.created_at
        }


def get_db_connection():
    """
    Create and return a database connection.
    
    Returns:
        psycopg2.Connection: Database connection object
    """
    conn = psycopg2.connect(Config.DATABASE_URL)
    return conn


def create_user(first_name: str, last_name: str, email: str, password: str) -> Optional[User]:
    """
    Create a new user in the database.
    
    Args:
        first_name (str): User's first name
        last_name (str): User's last name
        email (str): User's email address
        password (str): Plain text password (will be hashed)
    
    Returns:
        User: Created user object if successful
        None: If email already exists or creation fails
    
    Process:
        1. Check if email already exists
        2. Hash the password using bcrypt
        3. Insert user into database
        4. Return user object
    """
    print(f"💾 [DB] Creating user: {email}")
    conn = psycopg2.connect(Config.DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Check if email already exists
        print(f"🔍 [DB] Checking if email already exists: {email}")
        cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
        if cursor.fetchone():
            print(f"❌ [DB] Email already registered: {email}")
            return None  # Email already registered
        
        # Hash password using bcrypt
        print("🔐 [DB] Hashing password with bcrypt...")
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt(Config.BCRYPT_ROUNDS)
        ).decode('utf-8')
        print("✅ [DB] Password hashed successfully")
        
        # Insert new user
        print("💾 [DB] Inserting user into database...")
        cursor.execute('''
            INSERT INTO users (first_name, last_name, email, password_hash)
            VALUES (%s, %s, %s, %s)
            RETURNING id, first_name, last_name, email, password_hash, created_at
        ''', (first_name, last_name, email, password_hash))
        
        row = cursor.fetchone()
        conn.commit()
        print(f"✅ [DB] User created with ID: {row['id']}")
        
        return User(
            id=row['id'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            email=row['email'],
            password_hash=row['password_hash'],
            created_at=str(row['created_at'])
        )
        
    except psycopg2.Error as e:
        print(f"❌ [DB] Database error: {e}")
        return None
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[User]:
    """
    Retrieve a user by email address.
    
    Args:
        email (str): User's email address
    
    Returns:
        User: User object if found
        None: If user doesn't exist
    """
    print(f"🔍 [DB] Looking up user by email: {email}")
    conn = psycopg2.connect(Config.DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        row = cursor.fetchone()
        
        if row:
            print(f"✅ [DB] User found with ID: {row['id']}")
            return User(
                id=row['id'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                password_hash=row['password_hash'],
                created_at=str(row['created_at'])
            )
        print(f"❌ [DB] User not found: {email}")
        return None
        
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[User]:
    """
    Retrieve a user by ID.
    
    Args:
        user_id (int): User's unique identifier
    
    Returns:
        User: User object if found
        None: If user doesn't exist
    """
    print(f"🔍 [DB] Looking up user by ID: {user_id}")
    conn = psycopg2.connect(Config.DATABASE_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        row = cursor.fetchone()
        
        if row:
            print(f"✅ [DB] User found: {row['email']}")
            return User(
                id=row['id'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                password_hash=row['password_hash'],
                created_at=str(row['created_at'])
            )
        print(f"❌ [DB] User not found with ID: {user_id}")
        return None
        
    finally:
        conn.close()


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password (str): Plain text password to verify
        password_hash (str): Bcrypt hashed password from database
    
    Returns:
        bool: True if password matches, False otherwise
    """
    print("🔐 [DB] Verifying password with bcrypt...")
    result = bcrypt.checkpw(
        plain_password.encode('utf-8'),
        password_hash.encode('utf-8')
    )
    if result:
        print("✅ [DB] Password verification successful")
    else:
        print("❌ [DB] Password verification failed")
    return result
