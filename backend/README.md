# JWT Authentication API

A Flask-based REST API with JWT authentication, featuring access tokens, refresh tokens, and SQLite database.

## Features

- User signup and login
- JWT access tokens (15 minutes)
- JWT refresh tokens (7 days)
- Bcrypt password hashing
- Protected routes
- SQLite database
- CORS enabled

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python app.py
```

The server will start at `http://localhost:5000`

## API Endpoints

### Base URL
```
http://localhost:5000/api
```

---

## 1. User Signup

Create a new user account.

**Endpoint:** `POST /api/signup`

**Request Body:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@example.com",
  "password": "password123"
}
```

**Success Response (201):**
```json
{
  "message": "User created successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "created_at": "2024-01-01 12:00:00"
  }
}
```

**Error Responses:**
- `400` - Missing required fields
- `400` - Invalid email format
- `400` - Password too short (minimum 6 characters)
- `400` - Email already registered

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "password": "password123"
  }'
```

---

## 2. User Login

Authenticate and receive tokens.

**Endpoint:** `POST /api/login`

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "password123"
}
```

**Success Response (200):**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "created_at": "2024-01-01 12:00:00"
  }
}
```

**Error Responses:**
- `400` - Missing email or password
- `401` - Invalid credentials

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }'
```

---

## 3. Refresh Access Token

Get a new access token using refresh token.

**Endpoint:** `POST /api/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Token refreshed successfully"
}
```

**Error Responses:**
- `401` - Missing refresh token
- `401` - Invalid or expired refresh token

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN_HERE"
  }'
```

---

## 4. Get User Profile (Protected)

Retrieve authenticated user's profile.

**Endpoint:** `GET /api/profile`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "created_at": "2024-01-01 12:00:00"
  }
}
```

**Error Responses:**
- `401` - Missing authorization header
- `401` - Invalid authorization format
- `401` - Invalid or expired token

**cURL Example:**
```bash
curl -X GET http://localhost:5000/api/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

---

## 5. Verify Token (Protected)

Check if access token is valid.

**Endpoint:** `GET /api/verify`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "valid": true,
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "created_at": "2024-01-01 12:00:00"
  }
}
```

**Error Responses:**
- `401` - Missing authorization header
- `401` - Invalid authorization format
- `401` - Invalid or expired token

**cURL Example:**
```bash
curl -X GET http://localhost:5000/api/verify \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

---

## Authentication Flow

### Initial Authentication
1. User signs up or logs in
2. Server returns `access_token` and `refresh_token`
3. Store both tokens securely (localStorage, sessionStorage, or httpOnly cookies)

### Making Authenticated Requests
1. Include access token in Authorization header:
   ```
   Authorization: Bearer <access_token>
   ```

### Token Refresh Flow
1. When access token expires (after 15 minutes), you'll get a `401` error
2. Use the refresh token to get a new access token:
   ```bash
   POST /api/refresh
   Body: { "refresh_token": "..." }
   ```
3. Update stored access token with the new one
4. Retry the original request

### Token Expiration
- **Access Token:** 15 minutes
- **Refresh Token:** 7 days

When refresh token expires, user must log in again.

---

## JavaScript/Fetch Examples

### Signup
```javascript
const signup = async (firstName, lastName, email, password) => {
  const response = await fetch('http://localhost:5000/api/signup', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      firstName,
      lastName,
      email,
      password
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Store tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  } else {
    throw new Error(data.message);
  }
};
```

### Login
```javascript
const login = async (email, password) => {
  const response = await fetch('http://localhost:5000/api/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Store tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return data;
  } else {
    throw new Error(data.message);
  }
};
```

### Get Profile (Protected)
```javascript
const getProfile = async () => {
  const accessToken = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:5000/api/profile', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  
  if (response.ok) {
    return await response.json();
  } else if (response.status === 401) {
    // Token expired, try to refresh
    await refreshToken();
    // Retry the request
    return getProfile();
  } else {
    throw new Error('Failed to fetch profile');
  }
};
```

### Refresh Token
```javascript
const refreshToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  
  const response = await fetch('http://localhost:5000/api/refresh', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Update access token
    localStorage.setItem('access_token', data.access_token);
    return data.access_token;
  } else {
    // Refresh token expired, redirect to login
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
    throw new Error('Session expired');
  }
};
```

---

## Python/Requests Examples

### Signup
```python
import requests

response = requests.post('http://localhost:5000/api/signup', json={
    'firstName': 'John',
    'lastName': 'Doe',
    'email': 'john@example.com',
    'password': 'password123'
})

data = response.json()
print(data)
```

### Login
```python
import requests

response = requests.post('http://localhost:5000/api/login', json={
    'email': 'john@example.com',
    'password': 'password123'
})

data = response.json()
access_token = data['access_token']
refresh_token = data['refresh_token']
```

### Get Profile (Protected)
```python
import requests

headers = {
    'Authorization': f'Bearer {access_token}'
}

response = requests.get('http://localhost:5000/api/profile', headers=headers)
print(response.json())
```

---

## Terminal Logs

When you run the server, you'll see detailed logs for every request:

```
======================================================================
📝 [SIGNUP] New signup request received
📥 [SIGNUP] Request data received: ['firstName', 'lastName', 'email', 'password']
👤 [SIGNUP] Attempting to create user: john@example.com
✅ [SIGNUP] All validations passed
💾 [SIGNUP] Creating user in database...
💾 [DB] Creating user: john@example.com
🔍 [DB] Checking if email already exists: john@example.com
🔐 [DB] Hashing password with bcrypt...
✅ [DB] Password hashed successfully
💾 [DB] Inserting user into database...
✅ [DB] User created with ID: 1
✅ [SIGNUP] User created successfully with ID: 1
🔐 [SIGNUP] Generating JWT tokens...
🔐 [AUTH] Generating access token for user_id=1, email=john@example.com
✅ [AUTH] Access token generated (expires in 0:15:00)
🔐 [AUTH] Generating refresh token for user_id=1
✅ [AUTH] Refresh token generated (expires in 7 days, 0:00:00)
✅ [SIGNUP] Tokens generated successfully
✅ [SIGNUP] Signup complete for user: john@example.com
======================================================================
```

These logs help you understand:
- Request flow through the application
- Database operations
- Token generation and validation
- Authentication success/failure
- Error conditions

---

## Error Handling

All error responses follow this format:
```json
{
  "message": "Error description"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created (signup)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication failed)
- `500` - Internal Server Error

---

## Security Notes

1. **Change Secret Keys:** Update `JWT_SECRET_KEY` and `JWT_REFRESH_SECRET_KEY` in production
2. **Use Environment Variables:** Store secrets in environment variables, not in code
3. **Enable HTTPS:** Always use HTTPS in production
4. **Secure Token Storage:** Use httpOnly cookies for tokens in production
5. **CORS Configuration:** Restrict CORS origins to your frontend domain
6. **Password Requirements:** Enforce strong password policies
7. **Rate Limiting:** Add rate limiting to prevent brute force attacks

---

## Configuration

Edit `config.py` to customize:
- Token expiration times
- Secret keys
- Database path
- CORS origins
- Bcrypt rounds

---

## Database Schema

**users table:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Testing with Postman

1. Import the endpoints into Postman
2. Create an environment with variables:
   - `base_url`: `http://localhost:5000/api`
   - `access_token`: (will be set automatically)
   - `refresh_token`: (will be set automatically)

3. Add a test script to login/signup requests to save tokens:
```javascript
if (pm.response.code === 200 || pm.response.code === 201) {
    const data = pm.response.json();
    pm.environment.set("access_token", data.access_token);
    pm.environment.set("refresh_token", data.refresh_token);
}
```

4. For protected routes, use `{{access_token}}` in Authorization header

---

## License

MIT
