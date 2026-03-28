"""
Flask Backend API with JWT Authentication
===========================================
"""

# Add backend directory to path for imports
import sys
import os
if __name__ == '__main__':
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.config import Config
from backend.auth.user_database import init_database
from backend.auth.db_models import create_user, get_user_by_email, verify_password
from backend.auth.auth import (
    generate_tokens, 
    token_required, 
    refresh_token_required,
    decode_access_token
)
from backend.auth.password_reset import password_reset_manager
from backend.recommendations.recommend import get_place_recommendations
from backend.travel.travel_planner import plan_trip_sync

# ============================================================================
# APPLICATION INITIALIZATION
# ============================================================================

# Initialize Flask application
app = Flask(__name__)

# Enable CORS for React frontend - allow all origins for now
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize database on startup
init_database()

# ============================================================================
# PUBLIC ROUTES (No Authentication Required)
# ============================================================================

@app.route('/api/signup', methods=['POST'])
def signup():
    """
    User Signup Endpoint
    ====================
    
    Creates a new user account with hashed password.
    
    Request:
        Method: POST
        Content-Type: application/json
        Body: {
            "firstName": "string",
            "lastName": "string",
            "email": "string",
            "password": "string"
        }
    
    Response (Success - 201):
        {
            "message": "User created successfully",
            "access_token": "eyJhbGc...",
            "refresh_token": "eyJhbGc...",
            "user": {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com"
            }
        }
    
    Response (Failure - 400):
        {
            "message": "Email already registered" | "All fields required"
        }
    
    Process:
        1. Validate all required fields
        2. Check if email already exists
        3. Hash password with bcrypt
        4. Create user in database
        5. Generate access + refresh tokens
        6. Return tokens and user data
    """
    print("\n" + "="*70)
    print("📝 [SIGNUP] New signup request received")
    
    data = request.get_json()
    print(f"📥 [SIGNUP] Request data received: {list(data.keys()) if data else 'None'}")
    
    # Extract and validate fields
    first_name = data.get('firstName', '').strip()
    last_name = data.get('lastName', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    print(f"👤 [SIGNUP] Attempting to create user: {email}")
    
    # Validate required fields
    if not all([first_name, last_name, email, password]):
        print("❌ [SIGNUP] Validation failed: Missing required fields")
        return jsonify({'message': 'All fields are required'}), 400
    
    # Validate email format (basic check)
    if '@' not in email or '.' not in email:
        print(f"❌ [SIGNUP] Validation failed: Invalid email format - {email}")
        return jsonify({'message': 'Invalid email format'}), 400
    
    # Validate password length
    if len(password) < 6:
        print("❌ [SIGNUP] Validation failed: Password too short")
        return jsonify({'message': 'Password must be at least 6 characters'}), 400
    
    print("✅ [SIGNUP] All validations passed")
    
    # Create user in database
    print("💾 [SIGNUP] Creating user in database...")
    user = create_user(first_name, last_name, email, password)
    
    if not user:
        print(f"❌ [SIGNUP] Failed: Email already registered - {email}")
        return jsonify({'message': 'Email already registered'}), 400
    
    print(f"✅ [SIGNUP] User created successfully with ID: {user.id}")
    
    # Generate tokens
    print("🔐 [SIGNUP] Generating JWT tokens...")
    access_token, refresh_token = generate_tokens(user.id, user.email)
    print("✅ [SIGNUP] Tokens generated successfully")
    
    # Return success response
    print(f"✅ [SIGNUP] Signup complete for user: {email}")
    print("="*70 + "\n")
    return jsonify({
        'message': 'User created successfully',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 201


@app.route('/api/login', methods=['POST'])
def login():
    """
    User Login Endpoint
    ===================
    
    Authenticates user and returns access + refresh tokens.
    
    Request:
        Method: POST
        Content-Type: application/json
        Body: {
            "email": "string",
            "password": "string"
        }
    
    Response (Success - 200):
        {
            "message": "Login successful",
            "access_token": "eyJhbGc...",
            "refresh_token": "eyJhbGc...",
            "user": {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com"
            }
        }
    
    Response (Failure - 401):
        {
            "message": "Invalid credentials"
        }
    
    Process:
        1. Extract email and password
        2. Find user by email
        3. Verify password with bcrypt
        4. Generate access + refresh tokens
        5. Return tokens and user data
    """
    print("\n" + "="*70)
    print("🔑 [LOGIN] Login request received")
    
    data = request.get_json()
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    print(f"👤 [LOGIN] Attempting login for: {email}")
    
    # Validate required fields
    if not email or not password:
        print("❌ [LOGIN] Validation failed: Missing email or password")
        return jsonify({'message': 'Email and password required'}), 400
    
    # Get user from database
    print("🔍 [LOGIN] Looking up user in database...")
    user = get_user_by_email(email)
    
    if not user:
        print(f"❌ [LOGIN] Failed: User not found - {email}")
        return jsonify({'message': 'Invalid credentials'}), 401
    
    print(f"✅ [LOGIN] User found with ID: {user.id}")
    
    # Verify password
    print("🔐 [LOGIN] Verifying password...")
    if not verify_password(password, user.password_hash):
        print(f"❌ [LOGIN] Failed: Invalid password for - {email}")
        return jsonify({'message': 'Invalid credentials'}), 401
    
    print("✅ [LOGIN] Password verified successfully")
    
    # Generate tokens
    print("🔐 [LOGIN] Generating JWT tokens...")
    access_token, refresh_token = generate_tokens(user.id, user.email)
    print("✅ [LOGIN] Tokens generated successfully")
    
    # Return success response
    print(f"✅ [LOGIN] Login successful for user: {email}")
    print("="*70 + "\n")
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


@app.route('/api/refresh', methods=['POST'])
@refresh_token_required
def refresh(user_id, email):
    """
    Token Refresh Endpoint
    ======================
    
    Generates new access token using refresh token.
    
    Request:
        Method: POST
        Content-Type: application/json
        Body: {
            "refresh_token": "eyJhbGc..."
        }
    
    Response (Success - 200):
        {
            "access_token": "eyJhbGc...",
            "message": "Token refreshed successfully"
        }
    
    Response (Failure - 401):
        {
            "message": "Invalid or expired refresh token"
        }
    
    Process:
        1. Validate refresh token (done by decorator)
        2. Generate new access token
        3. Return new access token
    
    Note:
        Refresh token is NOT regenerated for security.
        User must login again when refresh token expires.
    """
    print("\n" + "="*70)
    print("🔄 [REFRESH] Token refresh request received")
    print(f"👤 [REFRESH] User ID: {user_id}, Email: {email}")
    
    # Generate new access token
    from auth import generate_access_token
    print("🔐 [REFRESH] Generating new access token...")
    access_token = generate_access_token(user_id, email)
    
    print("✅ [REFRESH] New access token generated successfully")
    print("="*70 + "\n")
    
    return jsonify({
        'access_token': access_token,
        'message': 'Token refreshed successfully'
    }), 200


# ============================================================================
# PROTECTED ROUTES (Authentication Required)
# ============================================================================

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """
    Get User Profile Endpoint
    =========================
    
    Returns authenticated user's profile information.
    
    Request:
        Method: GET
        Headers: {
            "Authorization": "Bearer <access_token>"
        }
    
    Response (Success - 200):
        {
            "user": {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "created_at": "2024-01-01 12:00:00"
            }
        }
    
    Response (Failure - 401):
        {
            "message": "Invalid or expired token"
        }
    """
    print("\n" + "="*70)
    print("👤 [PROFILE] Profile request received")
    print(f"✅ [PROFILE] Authenticated user: {current_user.email} (ID: {current_user.id})")
    print("="*70 + "\n")
    
    return jsonify({
        'user': current_user.to_dict()
    }), 200


@app.route('/api/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    """
    Verify Token Endpoint
    =====================
    
    Verifies if access token is still valid.
    
    Request:
        Method: GET
        Headers: {
            "Authorization": "Bearer <access_token>"
        }
    
    Response (Success - 200):
        {
            "valid": true,
            "user": {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com"
            }
        }
    
    Response (Failure - 401):
        {
            "message": "Invalid or expired token"
        }
    """
    print("\n" + "="*70)
    print("✔️  [VERIFY] Token verification request received")
    print(f"✅ [VERIFY] Token is valid for user: {current_user.email} (ID: {current_user.id})")
    print("="*70 + "\n")
    
    return jsonify({
        'valid': True,
        'user': current_user.to_dict()
    }), 200


# ============================================================================
# PASSWORD RESET ROUTES (Forgot Password with OTP)
# ============================================================================

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """
    Forgot Password - Request OTP
    ==============================
    
    Sends a 6-digit OTP to user's email for password reset.
    
    Request:
        Method: POST
        Content-Type: application/json
        Body: {
            "email": "string"
        }
    
    Response (Success - 200):
        {
            "message": "OTP sent to your email. Valid for 10 minutes."
        }
    
    Response (Failure - 400):
        {
            "message": "Email is required"
        }
    
    Process:
        1. Validate email
        2. Check if user exists (don't reveal if not)
        3. Generate 6-digit OTP
        4. Store OTP with 10-minute expiration
        5. Send OTP via email
    
    Security:
        - Doesn't reveal if email exists or not
        - OTP expires in 10 minutes
        - Previous OTPs are invalidated
    """
    print("\n" + "="*70)
    print("🔐 [FORGOT-PASSWORD] Request received")
    
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        print("❌ [FORGOT-PASSWORD] Email missing")
        return jsonify({'message': 'Email is required'}), 400
    
    # Request password reset
    success, message = password_reset_manager.request_password_reset(email)
    
    if success:
        print(f"✅ [FORGOT-PASSWORD] OTP sent to: {email}")
        print("="*70 + "\n")
        return jsonify({'message': message}), 200
    else:
        print(f"❌ [FORGOT-PASSWORD] Failed for: {email}")
        print("="*70 + "\n")
        return jsonify({'message': message}), 400


@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP
    ==========
    
    Verifies the OTP sent to user's email.
    
    Request:
        Method: POST
        Content-Type: application/json
        Body: {
            "email": "string",
            "otp": "string"
        }
    
    Response (Success - 200):
        {
            "message": "OTP verified successfully",
            "valid": true
        }
    
    Response (Failure - 400):
        {
            "message": "Invalid or expired OTP",
            "valid": false
        }
    
    Process:
        1. Validate email and OTP
        2. Check if OTP exists and not expired
        3. Check if OTP not already used
        4. Return verification result
    """
    print("\n" + "="*70)
    print("🔍 [VERIFY-OTP] Request received")
    
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    otp = data.get('otp', '').strip()
    
    if not email or not otp:
        print("❌ [VERIFY-OTP] Missing email or OTP")
        return jsonify({'message': 'Email and OTP are required', 'valid': False}), 400
    
    # Verify OTP
    success, message, user_id = password_reset_manager.verify_otp(email, otp)
    
    if success:
        print(f"✅ [VERIFY-OTP] OTP verified for: {email}")
        print("="*70 + "\n")
        return jsonify({'message': message, 'valid': True}), 200
    else:
        print(f"❌ [VERIFY-OTP] Verification failed for: {email}")
        print("="*70 + "\n")
        return jsonify({'message': message, 'valid': False}), 400


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """
    Reset Password
    ==============
    
    Resets user password after OTP verification.
    
    Request:
        Method: POST
        Content-Type: application/json
        Body: {
            "email": "string",
            "otp": "string",
            "newPassword": "string"
        }
    
    Response (Success - 200):
        {
            "message": "Password reset successfully. You can now log in with your new password."
        }
    
    Response (Failure - 400):
        {
            "message": "Invalid OTP or password requirements not met"
        }
    
    Process:
        1. Validate all fields
        2. Verify OTP
        3. Hash new password
        4. Update password in database
        5. Mark OTP as used
        6. Send confirmation email
    
    Security:
        - Password must be at least 6 characters
        - OTP is verified before password change
        - OTP is marked as used after successful reset
        - Confirmation email sent to user
    """
    print("\n" + "="*70)
    print("🔄 [RESET-PASSWORD] Request received")
    
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    otp = data.get('otp', '').strip()
    new_password = data.get('newPassword', '')
    
    if not email or not otp or not new_password:
        print("❌ [RESET-PASSWORD] Missing required fields")
        return jsonify({'message': 'Email, OTP, and new password are required'}), 400
    
    # Reset password
    success, message = password_reset_manager.reset_password(email, otp, new_password)
    
    if success:
        print(f"✅ [RESET-PASSWORD] Password reset successful for: {email}")
        print("="*70 + "\n")
        return jsonify({'message': message}), 200
    else:
        print(f"❌ [RESET-PASSWORD] Failed for: {email}")
        print("="*70 + "\n")
        return jsonify({'message': message}), 400


# ============================================================================
# PLACE RECOMMENDATION ROUTES
# ============================================================================

@app.route('/api/recommend', methods=['POST'])
def recommend_places():
    """
    Place Recommendation Endpoint
    =============================
    
    Recommends tourist attractions and hotels near a given place.
    Only returns places with available images.
    
    Request:
        Method: POST
        Content-Type: application/json
        Body: {
            "place": "string"
        }
    
    Response (Success - 200):
        {
            "success": true,
            "message": "Found X recommendations near Place Name",
            "search_location": {
                "name": "Place Name",
                "lat": 12.345,
                "lon": 67.890
            },
            "results": [
                {
                    "name": "Attraction Name",
                    "lat": 12.345,
                    "lon": 67.890,
                    "type": "attraction|hotel|monument",
                    "image": "https://...",
                    "extract": "Description text..."
                }
            ]
        }
    
    Response (Failure - 400):
        {
            "success": false,
            "message": "Place name is required",
            "results": []
        }
    
    Response (Not Found - 200):
        {
            "success": false,
            "message": "Could not find coordinates for 'Place Name'",
            "results": []
        }
    
    Process:
        1. Validate place name
        2. Get coordinates from Wikipedia
        3. Query nearby attractions/hotels from Overpass API
        4. Enrich with Wikipedia images and descriptions
        5. Filter out places without images
        6. Return enriched results
    """
    print("\n" + "="*70)
    print("🗺️  [RECOMMEND] Place recommendation request received")
    
    data = request.get_json()
    place_name = data.get('place', '').strip()
    
    if not place_name:
        print("❌ [RECOMMEND] Place name missing")
        return jsonify({
            'success': False,
            'message': 'Place name is required',
            'results': []
        }), 400
    
    print(f"📍 [RECOMMEND] Searching for recommendations near: {place_name}")
    
    # Get recommendations
    result = get_place_recommendations(place_name)
    
    if result['success']:
        print(f"✅ [RECOMMEND] Found {len(result['results'])} places with images")
        print("="*70 + "\n")
        return jsonify(result), 200
    else:
        print(f"❌ [RECOMMEND] {result['message']}")
        print("="*70 + "\n")
        return jsonify(result), 200


@app.route('/api/plan-trip', methods=['POST'])
def plan_trip():
    """
    Travel Planning Endpoint
    ========================
    
    Plans a trip using AI agents (budget, places, map, knowledge).
    
    Request:
        Method: POST
        Content-Type: application/json
        Body: {
            "query": "Plan a 5-day trip to Goa under 20000",
            "session_id": "optional-session-id"
        }
    
    Response (Success - 200):
        {
            "success": true,
            "session_id": "abc123...",
            "budget": "Budget breakdown text",
            "itinerary": [
                {
                    "day": "Day 1",
                    "activities": ["8:00 AM - Activity 1", "10:00 AM - Activity 2"]
                }
            ],
            "map_file": "travel_map_20260216_123456.html",
            "summary": "Full response text"
        }
    
    Response (Failure - 400):
        {
            "success": false,
            "message": "Error message"
        }
    """
    print("\n" + "="*70)
    print("✈️  [PLAN-TRIP] Travel planning request received")
    
    data = request.get_json()
    query = data.get('query', '').strip()
    session_id = data.get('session_id')
    
    if not query:
        print("❌ [PLAN-TRIP] Query missing")
        return jsonify({
            'success': False,
            'message': 'Query is required'
        }), 400
    
    print(f"📝 [PLAN-TRIP] Query: {query}")
    
    # Plan trip using A2A system
    result = plan_trip_sync(query, session_id)
    
    # Add Wikipedia data if available from orchestrator
    # The Wikipedia data will be included in the result from plan_trip_sync
    
    if result['success']:
        print(f"✅ [PLAN-TRIP] Trip planned successfully")
        print("="*70 + "\n")
        return jsonify(result), 200
    else:
        print(f"❌ [PLAN-TRIP] {result.get('message', 'Failed')}")
        print("="*70 + "\n")
        return jsonify(result), 500


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    """
    Start the Flask development server.
    
    IMPORTANT:
        - Use a production WSGI server (gunicorn) in production
        - Set environment variables for secrets
        - Enable HTTPS in production
    """
    print("\n" + "="*70)
    print("🚀 JWT Authentication Server with SQLite + Refresh Tokens")
    print("="*70)
    print(f"📍 Server URL: http://localhost:5000")
    print(f"📍 API Base: http://localhost:5000/api")
    print("\n📚 Available Endpoints:")
    print("   POST /api/signup   - Create new account")
    print("   POST /api/login    - User login")
    print("   POST /api/refresh  - Refresh access token")
    print("   GET  /api/verify   - Verify token")
    print("   GET  /api/profile  - Get user profile (protected)")
    print("\n🔐 Password Reset Endpoints:")
    print("   POST /api/forgot-password  - Request OTP for password reset")
    print("   POST /api/verify-otp       - Verify OTP code")
    print("   POST /api/reset-password   - Reset password with OTP")
    print("\n🗺️  Place Recommendation Endpoints:")
    print("   POST /api/recommend        - Get place recommendations (with images only)")
    print("\n✈️  Travel Planning Endpoints:")
    print("   POST /api/plan-trip        - Plan a trip with AI agents")
    print("\n🔐 Token Configuration:")
    print("   Access Token:  15 minutes")
    print("   Refresh Token: 7 days")
    print("\n⚠️  Running in DEBUG mode - Do not use in production!")
    print("="*70 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
