# CORS Fix Documentation

## Problem
The frontend was getting CORS errors when trying to connect to the backend API:
```
OPTIONS /api/auth/login - 400 Bad Request
```

## Root Causes Identified

### 1. **Pydantic Settings JSON Parsing Error**
- **Problem**: Pydantic was trying to parse `ALLOWED_ORIGINS` as JSON because it was defined as `List[str]`
- **Solution**: Changed to `str` type with a `cors_origins` property that handles parsing

### 2. **Incorrect CORS Origins Format in Environment Variables**
- **Problem**: Environment variables were using JSON array syntax `["http://localhost:5173"]`
- **Solution**: Changed to comma-separated format `http://localhost:5173,http://localhost:3000`

### 3. **Port Mismatch**
- **Problem**: Frontend was configured for port 8000, but backend was running on port 8001
- **Solution**: Standardized on port 8001 for consistency

### 4. **Missing OPTIONS Method in CORS**
- **Problem**: CORS middleware wasn't explicitly allowing OPTIONS requests
- **Solution**: Added "OPTIONS" to allowed methods

### 5. **Incomplete CORS Headers**
- **Problem**: Missing `expose_headers` configuration
- **Solution**: Added `expose_headers=["*"]` to CORS middleware

## Changes Made

### Backend Changes

#### 1. Fixed Configuration Model (`config.py`):
```python
# Before
ALLOWED_ORIGINS: List[str] = [...]

# After  
ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,..."

@property
def cors_origins(self) -> List[str]:
    """Parse CORS origins from string"""
    # Handles both comma-separated and JSON array formats
```

#### 2. Fixed `.env` file:
```bash
# Before
ALLOWED_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# After
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000,http://localhost:8001,http://127.0.0.1:8001
```

#### 3. Enhanced CORS middleware in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Using new property
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Added OPTIONS
    allow_headers=["*"],
    expose_headers=["*"]  # Added expose_headers
)
```

#### 4. Changed default port to 8001:
```python
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8001,  # Changed from 8000
    reload=True,
    log_level=settings.LOG_LEVEL.lower()
)
```

#### 5. Added CORS debugging:
- Added startup logging to show allowed origins
- Added `/api/cors-test` endpoint for testing

### Frontend Changes

#### 1. Updated `.env` file:
```bash
# Before
VITE_API_BASE_URL=http://localhost:8000/api

# After
VITE_API_BASE_URL=http://localhost:8001/api
```

### Docker Configuration Updates

#### 1. Fixed CORS origins format in docker-compose files
#### 2. Updated ports from 8000 to 8001
#### 3. Updated API URLs to match new port

## Testing the Fix

### 1. **Start the Backend**
```bash
cd backend
./start.sh
```

### 2. **Test CORS Endpoint**
```bash
curl -X GET http://localhost:8001/api/cors-test
```

### 3. **Test OPTIONS Request**
```bash
curl -X OPTIONS http://localhost:8001/api/auth/login \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

### 4. **Check Browser Network Tab**
- Should see successful OPTIONS requests (200 status)
- Should see proper CORS headers in response

## Expected CORS Headers

The backend should now return these headers for CORS requests:
```
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: *
Access-Control-Allow-Credentials: true
Access-Control-Expose-Headers: *
```

## Troubleshooting

### If CORS errors persist:

1. **Check the browser console** for specific error messages
2. **Verify the frontend is connecting to the right port** (8001)
3. **Check backend logs** for CORS-related messages
4. **Test the CORS endpoint** directly: `http://localhost:8001/api/cors-test`
5. **Clear browser cache** and restart both frontend and backend

### Common Issues:

- **Port mismatch**: Ensure frontend and backend are using consistent ports
- **Environment variables**: Make sure `.env` files are loaded correctly
- **Middleware order**: CORS middleware should be added first
- **Origin format**: Use comma-separated strings, not JSON arrays
- **Pydantic parsing**: Ensure environment variables are in the correct format for Pydantic

## Restart Instructions

After making these changes:

1. **Stop the backend** (Ctrl+C)
2. **Stop the frontend** (Ctrl+C)
3. **Restart the backend**: `cd backend && ./start.sh`
4. **Restart the frontend**: `cd frontend && npm run dev` (or `bun dev`)
5. **Test the connection** by trying to log in

The CORS errors should now be resolved!