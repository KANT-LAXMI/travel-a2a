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
    Falls back to simplified planner if host agent is not available.
    Saves the plan to database with user_id if authenticated.
    
    Request:
        Method: POST
        Content-Type: application/json
        Headers: {
            "Authorization": "Bearer <access_token>" (optional)
        }
        Body: {
            "query": "Plan a 5-day trip to Goa under 20000",
            "session_id": "optional-session-id"
        }
    
    Response (Success - 200):
        {
            "success": true,
            "session_id": "abc123...",
            "budget": {...},
            "itinerary": [...],
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
    
    # Try to get current user (optional authentication)
    current_user = None
    user_id = None
    auth_header = request.headers.get('Authorization')
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            payload = decode_access_token(token)
            if payload:
                user_id = payload.get('user_id')
                current_user = get_user_by_email(payload.get('email'))
                print(f"👤 [PLAN-TRIP] Authenticated User: {current_user.email} (ID: {user_id})")
        except Exception as e:
            print(f"⚠️  [PLAN-TRIP] Token validation failed: {e}")
    
    if not current_user:
        print("👤 [PLAN-TRIP] Anonymous user (no authentication)")
    
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
    
    # Check if HOST_AGENT_URL is configured
    host_agent_url = Config.HOST_AGENT_URL
    
    # Try A2A system first if available
    if host_agent_url and host_agent_url != 'http://localhost:10000':
        print(f"🔗 [PLAN-TRIP] Using A2A host agent at {host_agent_url}")
        try:
            result = plan_trip_sync(query, session_id)
            
            if result['success']:
                print(f"✅ [PLAN-TRIP] Trip planned successfully via A2A")
                print("="*70 + "\n")
                return jsonify(result), 200
        except Exception as e:
            print(f"⚠️  [PLAN-TRIP] A2A failed: {e}, falling back to simple planner")
    
    # Fallback to simplified planner
    print("🔄 [PLAN-TRIP] Using simplified planner (serverless mode)")
    from backend.travel.simple_planner import get_simple_planner
    
    planner = get_simple_planner()
    result = planner.plan_trip(query, session_id, user_id=user_id)
    
    if result['success']:
        print(f"✅ [PLAN-TRIP] Trip planned successfully via simple planner")
        print("="*70 + "\n")
        return jsonify(result), 200
    else:
        print(f"❌ [PLAN-TRIP] {result.get('message', 'Failed')}")
        print("="*70 + "\n")
        return jsonify(result), 400


@app.route('/api/my-trips', methods=['GET'])
@token_required
def get_my_trips(current_user):
    """
    Get all trips for the authenticated user
    
    Request:
        Method: GET
        Headers: {
            "Authorization": "Bearer <access_token>"
        }
    
    Response (Success - 200):
        {
            "success": true,
            "trips": [
                {
                    "id": "uuid",
                    "destination": "Pune",
                    "duration_days": 2,
                    "status": "completed",
                    "created_at": "2025-01-12",
                    "pdf_url": "https://...",
                    "user_query": "Plan 2 day trip to Pune"
                }
            ]
        }
    """
    print("\n" + "="*70)
    print("📋 [MY-TRIPS] Fetching trips for user")
    print(f"👤 [MY-TRIPS] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        from backend.database.db_manager import TravelBuddyDB
        db = TravelBuddyDB()
        
        trips = db.get_user_trips(current_user.id)
        
        print(f"✅ [MY-TRIPS] Found {len(trips)} trips")
        print("="*70 + "\n")
        
        return jsonify({
            'success': True,
            'trips': trips
        }), 200
        
    except Exception as e:
        print(f"❌ [MY-TRIPS] Error: {e}")
        print("="*70 + "\n")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/trips/<trip_id>', methods=['DELETE'])
@token_required
def delete_trip(current_user, trip_id):
    """
    Delete a trip
    
    Request:
        Method: DELETE
        Headers: {
            "Authorization": "Bearer <access_token>"
        }
    
    Response (Success - 200):
        {
            "success": true,
            "message": "Trip deleted successfully"
        }
    """
    print("\n" + "="*70)
    print(f"🗑️  [DELETE-TRIP] Deleting trip {trip_id}")
    print(f"👤 [DELETE-TRIP] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        from backend.database.db_manager import TravelBuddyDB
        db = TravelBuddyDB()
        
        # Verify trip belongs to user
        success = db.delete_user_trip(trip_id, current_user.id)
        
        if success:
            print(f"✅ [DELETE-TRIP] Trip deleted successfully")
            print("="*70 + "\n")
            return jsonify({
                'success': True,
                'message': 'Trip deleted successfully'
            }), 200
        else:
            print(f"❌ [DELETE-TRIP] Trip not found or unauthorized")
            print("="*70 + "\n")
            return jsonify({
                'success': False,
                'message': 'Trip not found or unauthorized'
            }), 404
        
    except Exception as e:
        print(f"❌ [DELETE-TRIP] Error: {e}")
        print("="*70 + "\n")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/trips/<trip_id>', methods=['GET'])
@token_required
def get_trip_details(current_user, trip_id):
    """
    Get full trip details including budget, itinerary, and map data
    
    Request:
        Method: GET
        Headers: {
            "Authorization": "Bearer <access_token>"
        }
    
    Response (Success - 200):
        {
            "success": true,
            "trip": {
                "destination": "Mumbai",
                "duration_days": 3,
                "budget": {...},
                "itinerary": {...},
                "map": {...}
            }
        }
    """
    print("\n" + "="*70)
    print(f"📄 [GET-TRIP] Fetching trip details for {trip_id}")
    print(f"👤 [GET-TRIP] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        from backend.database.db_manager import TravelBuddyDB
        db = TravelBuddyDB()
        
        # Get the trip
        trip = db.get_travel_plan(trip_id)
        
        if not trip:
            print(f"❌ [GET-TRIP] Trip not found")
            print("="*70 + "\n")
            return jsonify({
                'success': False,
                'message': 'Trip not found'
            }), 404
        
        # Verify ownership
        if trip.get('user_id') != current_user.id:
            print(f"❌ [GET-TRIP] Unauthorized access attempt")
            print("="*70 + "\n")
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
        
        # Format the response to match PDF generator expectations
        formatted_trip = {
            'destination': trip.get('destination') or 'Unknown',
            'duration_days': trip.get('duration_days') or 0,
            'summary': trip.get('summary') or f"Explore the beauty and culture of {trip.get('destination', 'Unknown')}",
            'budget': {},
            'itinerary': {
                'days': [],
                'summary': trip.get('summary') or f"Explore the beauty and culture of {trip.get('destination', 'Unknown')}",
                'tips': trip.get('tips') or [
                    "Plan your activities in advance to make the most of your time",
                    "Keep some buffer time between activities for travel",
                    "Try local cuisine and street food for authentic experience",
                    "Carry cash and small change for local vendors"
                ]
            },
            'map': {
                'locations': []
            },
            'pdf_url': trip.get('pdf_url')
        }
        
        # Format budget
        if trip.get('budget'):
            budget = trip['budget']
            formatted_trip['budget'] = {
                'transport': float(budget.get('transport', 0)),
                'accommodation': float(budget.get('accommodation', 0)),
                'food': float(budget.get('food', 0)),
                'activities': float(budget.get('activities', 0)),
                'miscellaneous': float(budget.get('miscellaneous', 0)),
                'total': float(budget.get('total', 0)),
                'currency': budget.get('currency', 'INR')
            }
        
        # Format itinerary days
        for day in trip.get('itinerary_days', []):
            formatted_day = {
                'day': day.get('day_number'),
                'date': day.get('date'),
                'activities': []
            }
            
            for activity in day.get('activities', []):
                formatted_activity = {
                    'time': activity.get('time'),
                    'title': activity.get('title'),
                    'description': activity.get('description'),
                    'cost': activity.get('cost'),
                    'location': {
                        'name': activity.get('location_name'),
                        'latitude': activity.get('location_latitude'),
                        'longitude': activity.get('location_longitude')
                    }
                }
                formatted_day['activities'].append(formatted_activity)
            
            formatted_trip['itinerary']['days'].append(formatted_day)
        
        # Format map locations
        if trip.get('map'):
            for location in trip['map'].get('locations', []):
                formatted_location = {
                    'name': location.get('name'),
                    'latitude': location.get('latitude'),
                    'longitude': location.get('longitude'),
                    'day': location.get('day'),
                    'time': location.get('time'),
                    'description': location.get('description'),
                    'image': location.get('image_url'),
                    'extract': location.get('description')
                }
                formatted_trip['map']['locations'].append(formatted_location)
        
        print(f"✅ [GET-TRIP] Trip details retrieved successfully")
        print("="*70 + "\n")
        
        return jsonify({
            'success': True,
            'trip': formatted_trip
        }), 200
        
    except Exception as e:
        print(f"❌ [GET-TRIP] Error: {e}")
        print("="*70 + "\n")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/test-pdf', methods=['GET'])
def test_pdf():
    """Test PDF generation capabilities"""
    import logging
    
    logger = logging.getLogger(__name__)
    
    results = {
        'imports': {},
        'environment': {},
        'test_generation': None
    }
    
    # Test imports
    try:
        import reportlab
        results['imports']['reportlab'] = f"✅ {reportlab.__version__}"
    except Exception as e:
        results['imports']['reportlab'] = f"❌ {str(e)}"
    
    try:
        from PIL import Image
        results['imports']['PIL'] = f"✅ Available"
    except Exception as e:
        results['imports']['PIL'] = f"❌ {str(e)}"
    
    try:
        import requests
        results['imports']['requests'] = f"✅ {requests.__version__}"
    except Exception as e:
        results['imports']['requests'] = f"❌ {str(e)}"
    
    # Check environment
    results['environment']['BLOB_READ_WRITE_TOKEN'] = '✅ Set' if os.getenv('BLOB_READ_WRITE_TOKEN') else '❌ Not set'
    results['environment']['DATABASE_URL'] = '✅ Set' if os.getenv('DATABASE_URL') else '❌ Not set'
    
    # Test PDF generation
    try:
        from backend.mcp_tools.filesystem_mcp_service.filesystem_api import FilesystemAPI
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            fs_api = FilesystemAPI(base_dir=temp_dir)
            
            # Test data
            test_data = {
                'destination': 'Mumbai',
                'duration_days': 2,
                'budget': {
                    'transport': 5000,
                    'accommodation': 6000,
                    'food': 3000,
                    'activities': 4000,
                    'miscellaneous': 1000,
                    'total': 19000,
                    'currency': 'INR'
                },
                'itinerary': {
                    'days': [
                        {
                            'day': 1,
                            'activities': [
                                {
                                    'time': '9:00 AM',
                                    'title': 'Visit Gateway of India',
                                    'description': 'Iconic monument',
                                    'location': {'name': 'Gateway of India'}
                                }
                            ]
                        }
                    ],
                    'total_days': 2
                },
                'map': {
                    'locations': [
                        {
                            'name': 'Gateway of India',
                            'latitude': 18.9220,
                            'longitude': 72.8347,
                            'day': 1,
                            'time': '9:00 AM',
                            'description': 'Historic monument'
                        }
                    ]
                }
            }
            
            pdf_result = fs_api.save_plan_as_pdf(
                destination='Mumbai',
                duration_days=2,
                plan_data=test_data,
                session_id='test'
            )
            
            if pdf_result.get('success'):
                results['test_generation'] = f"✅ PDF generated: {pdf_result['filename']} ({pdf_result['size_kb']} KB)"
            else:
                results['test_generation'] = f"❌ Failed: {pdf_result.get('error')}"
                
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        results['test_generation'] = f"❌ Exception: {str(e)}"
        logger.error(f"PDF generation test failed: {e}", exc_info=True)
    
    return jsonify(results), 200


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
