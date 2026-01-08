"""
Authentication routes
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Simple login endpoint for demo purposes
    In production, implement proper authentication
    """
    # Mock authentication - replace with real implementation
    if request.username == "admin" and request.password == "admin":
        return LoginResponse(
            access_token="mock-jwt-token",
            token_type="bearer",
            user={
                "name": "Administrador",
                "email": "admin@portada.com",
                "picture": None
            }
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

@router.post("/logout")
async def logout():
    """Logout endpoint"""
    return {"message": "Successfully logged out"}