"""
Authentication API routes
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.auth_service import auth_service
from app.core.exceptions import PortAdaAuthenticationError, PortAdaPermissionError

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    """Login request model"""
    username: str


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: dict


class LogoutResponse(BaseModel):
    """Logout response model"""
    message: str
    success: bool = True


class UserInfoResponse(BaseModel):
    """User information response model"""
    username: str
    role: str
    permissions: list
    full_name: str
    email: str
    is_active: bool


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user by username only (no password required)
    """
    try:
        logger.info(f"Login attempt for user: {request.username}")
        
        # Authenticate user by username only
        user_data = auth_service.authenticate_user_by_username(request.username)
        if not user_data:
            logger.warning(f"Failed login attempt for user: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token = auth_service.create_access_token(user_data)
        
        logger.info(f"User '{request.username}' logged in successfully")
        return LoginResponse(
            access_token=access_token,
            expires_in=auth_service.access_token_expire_minutes * 60,  # Convert to seconds
            user_info=user_data
        )
        
    except HTTPException:
        raise
    except PortAdaAuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout user and invalidate token
    """
    try:
        logger.info("User logout attempt")
        
        # Invalidate token
        success = auth_service.invalidate_token(credentials.credentials)
        
        if success:
            logger.info("User logged out successfully")
            return LogoutResponse(message="Successfully logged out")
        else:
            logger.warning("Logout failed: token not found")
            return LogoutResponse(
                message="Logout completed (token was already invalid)",
                success=True
            )
            
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout error"
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Get current authenticated user from token
    """
    try:
        # Verify token
        payload = auth_service.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "username": payload.get("sub"),
            "role": payload.get("role"),
            "permissions": payload.get("permissions", []),
            "full_name": payload.get("full_name"),
            "email": payload.get("email")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserInfoResponse)
async def get_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserInfoResponse(**current_user)


@router.get("/sessions")
async def list_active_sessions(current_user: dict = Depends(get_current_user)):
    """List active sessions (admin only)"""
    try:
        # Check admin permission
        auth_service.require_permission(current_user, "admin")
        
        sessions = auth_service.list_active_sessions()
        return {
            "active_sessions": sessions,
            "total_sessions": len(sessions)
        }
        
    except PortAdaPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving sessions"
        )