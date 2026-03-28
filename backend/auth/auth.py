"""
Authentication Module
=====================
JWT token generation and validation with refresh token support.
"""

import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from functools import wraps
from flask import request, jsonify
from backend.config import Config
from backend.auth.db_models import get_user_by_id

logger = logging.getLogger(__name__)


def generate_access_token(user_id: int, email: str) -> str:
    """Generate a JWT access token (short-lived)."""
    payload = {
        'user_id': user_id,
        'email': email,
        'type': 'access',
        'exp': datetime.utcnow() + Config.ACCESS_TOKEN_EXPIRES,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')


def generate_refresh_token(user_id: int) -> str:
    """Generate a JWT refresh token (long-lived)."""
    payload = {
        'user_id': user_id,
        'type': 'refresh',
        'exp': datetime.utcnow() + Config.REFRESH_TOKEN_EXPIRES,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, Config.JWT_REFRESH_SECRET_KEY, algorithm='HS256')


def generate_tokens(user_id: int, email: str) -> Tuple[str, str]:
    """Generate both access and refresh tokens."""
    return generate_access_token(user_id, email), generate_refresh_token(user_id)


def decode_access_token(token: str) -> Optional[Dict]:
    """Decode and validate an access token."""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload if payload.get('type') == 'access' else None
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        logger.debug(f"Token validation failed: {e}")
        return None


def decode_refresh_token(token: str) -> Optional[Dict]:
    """Decode and validate a refresh token."""
    try:
        payload = jwt.decode(token, Config.JWT_REFRESH_SECRET_KEY, algorithms=['HS256'])
        return payload if payload.get('type') == 'refresh' else None
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        logger.debug(f"Refresh token validation failed: {e}")
        return None


def token_required(f):
    """Decorator to protect routes requiring authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'message': 'Authorization header missing'}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'message': 'Invalid authorization header format'}), 401
        
        payload = decode_access_token(parts[1])
        if not payload:
            return jsonify({'message': 'Invalid or expired token'}), 401
        
        current_user = get_user_by_id(payload.get('user_id'))
        if not current_user:
            return jsonify({'message': 'User not found'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated


def refresh_token_required(f):
    """Decorator to validate refresh tokens."""
    @wraps(f)
    def decorated(*args, **kwargs):
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'message': 'Refresh token missing'}), 401
        
        payload = decode_refresh_token(refresh_token)
        if not payload:
            return jsonify({'message': 'Invalid or expired refresh token'}), 401
        
        user = get_user_by_id(payload.get('user_id'))
        if not user:
            return jsonify({'message': 'User not found'}), 401
        
        return f(payload.get('user_id'), user.email, *args, **kwargs)
    
    return decorated
