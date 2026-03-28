"""
Backend Configuration
=====================
Centralized configuration for the Flask application.

This module contains all configuration settings including:
- Secret keys for JWT tokens
- Database configuration
- Token expiration times
- CORS settings
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Application Configuration Class
    
    Contains all configuration variables for the Flask application.
    In production, use environment variables for sensitive data.
    """
    
    # ============================================================================
    # SECRET KEYS
    # ============================================================================
    
    # Secret key for JWT access token encoding/decoding
    # IMPORTANT: Change this in production and use environment variables
    # Example: os.environ.get('JWT_SECRET_KEY', 'fallback-secret-key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'QWERTY123456')
    
    # Secret key for JWT refresh token encoding/decoding
    # Should be different from access token secret for added security
    JWT_REFRESH_SECRET_KEY = os.environ.get('JWT_REFRESH_SECRET_KEY', 'poiuyt09876')
    
    # ============================================================================
    # TOKEN EXPIRATION TIMES
    # ============================================================================
    
    # Access token expires in 15 minutes (short-lived for security)
    ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.environ.get('ACCESS_TOKEN_MINUTES', 15)))
    
    # Refresh token expires in 7 days (long-lived for user convenience)
    REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.environ.get('REFRESH_TOKEN_DAYS', 7)))
    
    # ============================================================================
    # DATABASE CONFIGURATION
    # ============================================================================
    
    # PostgreSQL database URL
    # Format: postgresql://user:password@host:port/dbname
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///backend/database/travel_buddy.db')
    
    # Legacy SQLite path (for backward compatibility)
    DATABASE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'backend', 'database', 'travel_buddy.db'
    )
    
    # ============================================================================
    # CORS CONFIGURATION
    # ============================================================================
    
    # Allowed origins for CORS
    # In production, specify exact frontend URL
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # ============================================================================
    # PASSWORD HASHING
    # ============================================================================
    
    # Bcrypt rounds for password hashing (higher = more secure but slower)
    # 12 is a good balance between security and performance
    BCRYPT_ROUNDS = int(os.environ.get('BCRYPT_ROUNDS', 12))
    
    # ============================================================================
    # EMAIL CONFIGURATION
    # ============================================================================
    
    EMAIL_SENDER = os.environ.get('EMAIL_SENDER', 'noreply@travelbuddy.com')
    EMAIL_SENDER_NAME = os.environ.get('EMAIL_SENDER_NAME', 'Travel Buddy')
    
    # ============================================================================
    # A2A AGENT CONFIGURATION
    # ============================================================================
    
    HOST_AGENT_URL = os.environ.get('HOST_AGENT_URL', 'http://localhost:10000')
    A2A_TIMEOUT = float(os.environ.get('A2A_TIMEOUT', 300.0))  # 5 minutes default
    
    # ============================================================================
    # LOGGING CONFIGURATION
    # ============================================================================
    
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    ENABLE_DEBUG_LOGGING = os.environ.get('ENABLE_DEBUG_LOGGING', 'False').lower() == 'true'
