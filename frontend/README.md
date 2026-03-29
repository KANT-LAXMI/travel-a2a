# Anywhere App - Travel Planner Frontend

Beautiful React + JavaScript frontend with authentication for the AI-powered travel planner.

## Features

- ✅ Beautiful UI matching the provided design
- ✅ User Authentication (Login/Signup)
- ✅ JWT token management
- ✅ Protected routes
- ✅ Responsive design
- ✅ Integration with Python Flask backend
- ✅ Travel planning interface

## Tech Stack

- React 18
- React Router v6
- Axios for API calls
- Vite for fast development
- Pure CSS (no frameworks)

## Setup Instructions

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start the Backend (Flask)

Make sure your Flask backend is running on port 5000:

```bash
cd backend
python app.py
```

The backend should be running at `http://localhost:5000`

### 3. Start the Frontend (React)

```bash
cd frontend
npm run dev
```

The frontend will start at `http://localhost:3000`

## Project Structure

```
frontend/
├── src/
│   ├── context/
│   │   └── AuthContext.jsx      # Authentication state management
│   ├── pages/
│   │   ├── Login.jsx             # Login page
│   │   ├── Login.css
│   │   ├── Signup.jsx            # Signup page
│   │   ├── Signup.css
│   │   ├── Dashboard.jsx         # Main dashboard
│   │   └── Dashboard.css
│   ├── App.jsx                   # Main app with routing
│   ├── App.css
│   ├── main.jsx                  # Entry point
│   └── index.css                 # Global styles
├── index.html
├── vite.config.js
├── package.json
└── README.md
```

## API Endpoints Used

### Authentication
- `POST /api/signup` - Create new account
- `POST /api/login` - User login
- `GET /api/verify` - Verify token
- `GET /api/profile` - Get user profile
- `POST /api/refresh` - Refresh access token

## Features Breakdown

### 1. Authentication System
- JWT-based authentication
- Access tokens (15 min) + Refresh tokens (7 days)
- Automatic token verification on app load
- Protected routes with redirect

### 2. Beautiful UI
- Modern, clean design
- Smooth animations and transitions
- Responsive layout (mobile, tablet, desktop)
- Professional color scheme

### 3. Travel Planning Interface
- Query input for trip planning
- Integration point for Python backend (port 10000)
- Response display area
- Popular destinations showcase

## Integration with Python Backend

### Current Setup
The frontend is configured to work with:
- Flask backend (port 5000) for authentication
- Python travel planner backend (port 10000) for trip planning

### To Connect Travel Planner

Update `Dashboard.jsx` to connect to your Python backend:

```javascript
const handleSubmit = async (e) => {
  e.preventDefault()
  setLoading(true)

  try {
    const token = localStorage.getItem('access_token')
    
    // Call your Python backend
    const response = await axios.post('http://localhost:10000/send-task', {
      message: query
    }, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    setResponse(response.data.result.history[0].parts[0].text)
  } catch (error) {
    setResponse('Error: ' + error.message)
  }

  setLoading(false)
}
```

## Environment Variables

Create a `.env` file in the frontend directory if needed:

```env
VITE_API_URL=http://localhost:5000
VITE_TRAVEL_API_URL=http://localhost:10000
```

## Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` folder.

## Preview Production Build

```bash
npm run preview
```

## User Flow

1. **Landing** → User sees login page
2. **Signup** → User creates account with first name, last name, email, password
3. **Login** → User logs in with email and password
4. **Dashboard** → User can:
   - Plan trips by entering queries
   - View popular destinations
   - See features
   - Logout

## Security Features

- Passwords hashed with bcrypt (backend)
- JWT tokens for authentication
- Protected routes
- Token expiration handling
- Secure token storage in localStorage

## Responsive Breakpoints

- Desktop: > 1024px
- Tablet: 768px - 1024px
- Mobile: < 768px

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### CORS Issues
If you see CORS errors, make sure the Flask backend has CORS enabled:

```python
from flask_cors import CORS
CORS(app, origins=['http://localhost:3000'])
```

### Port Already in Use
If port 3000 is busy, Vite will automatically use the next available port.

### Backend Not Running
Make sure both Flask (port 5000) and Python travel planner (port 10000) are running.

## Next Steps

1. ✅ Authentication is complete
2. ✅ UI is ready
3. 🔄 Connect Dashboard to Python travel planner backend
4. 🔄 Add trip history/saved trips
5. 🔄 Add user profile editing
6. 🔄 Add map visualization in frontend

## License

MIT
