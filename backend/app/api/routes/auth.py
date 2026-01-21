"""
Authentication routes - Simplified username-only authentication
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str

class LoginResponse(BaseModel):
    success: bool
    user: dict

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Simple username-only authentication for activity tracking
    No password required - for development/internal use
    """
    username = request.username.strip()
    
    if not username:
        return LoginResponse(
            success=False,
            user={}
        )
    
    return LoginResponse(
        success=True,
        user={
            "name": username,
            "email": f"{username}@portada.local",
            "picture": None
        }
    )

@router.post("/logout")
async def logout():
    """Logout endpoint"""
    return {"message": "Successfully logged out"}