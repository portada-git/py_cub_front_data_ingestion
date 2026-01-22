"""
Authentication service for the PortAda application
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import logging

from app.core.config import settings
from app.core.exceptions import PortAdaAuthenticationError, PortAdaPermissionError

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling user authentication and authorization"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
        # Mock user database - simplified for username-only authentication
        self.users_db = {
            "admin": {
                "username": "admin",
                "role": "admin",
                "permissions": ["read", "write", "admin"],
                "full_name": "Administrador",
                "email": "admin@portada.com",
                "is_active": True
            },
            "analyst": {
                "username": "analyst",
                "role": "analyst",
                "permissions": ["read", "write"],
                "full_name": "Analista de Datos",
                "email": "analyst@portada.com",
                "is_active": True
            },
            "viewer": {
                "username": "viewer",
                "role": "viewer",
                "permissions": ["read"],
                "full_name": "Visualizador de Datos",
                "email": "viewer@portada.com",
                "is_active": True
            }
        
        # Active sessions storage - in production, use Redis
        self.active_sessions = {}
    
    def authenticate_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user by username only (no password required)
        
        Args:
            username: User's username
            
        Returns:
            User information if authentication successful, None otherwise
        """
        try:
            user = self.users_db.get(username)
            if not user:
                logger.warning(f"Authentication failed: user '{username}' not found")
                return None
            
            if not user.get("is_active", False):
                logger.warning(f"Authentication failed: user '{username}' is inactive")
                return None
            
            logger.info(f"User '{username}' authenticated successfully")
            return {
                "username": user["username"],
                "role": user["role"],
                "permissions": user["permissions"],
                "full_name": user["full_name"],
                "email": user["email"]
            }
            
        except Exception as e:
            logger.error(f"Error during authentication for user '{username}': {e}")
            return None
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """
        Create a JWT access token for a user
        
        Args:
            user_data: User information to encode in token
            
        Returns:
            JWT access token
        """
        try:
            # Set token expiration
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
            # Create token payload
            to_encode = {
                "sub": user_data["username"],
                "exp": expire,
                "iat": datetime.utcnow(),
                "role": user_data["role"],
                "permissions": user_data["permissions"],
                "full_name": user_data["full_name"],
                "email": user_data["email"]
            }
            
            # Encode JWT token
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            # Store session
            session_id = f"{user_data['username']}_{int(datetime.utcnow().timestamp())}"
            self.active_sessions[encoded_jwt] = {
                "session_id": session_id,
                "username": user_data["username"],
                "created_at": datetime.utcnow(),
                "expires_at": expire,
                "is_active": True
            }
            
            logger.info(f"Access token created for user '{user_data['username']}'")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise PortAdaAuthenticationError(
                message="Failed to create access token",
                error_code="TOKEN_CREATION_FAILED",
                original_error=e
            )
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            # Check if session exists and is active
            session = self.active_sessions.get(token)
            if not session or not session.get("is_active", False):
                logger.warning("Token verification failed: session not found or inactive")
                return None
            
            # Check if session has expired
            if datetime.utcnow() > session["expires_at"]:
                logger.warning("Token verification failed: session expired")
                self.invalidate_token(token)
                return None
            
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify user still exists and is active
            username = payload.get("sub")
            user = self.users_db.get(username)
            if not user or not user.get("is_active", False):
                logger.warning(f"Token verification failed: user '{username}' not found or inactive")
                self.invalidate_token(token)
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: token expired")
            self.invalidate_token(token)
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token verification failed: invalid token - {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    def invalidate_token(self, token: str) -> bool:
        """
        Invalidate a JWT token (logout)
        
        Args:
            token: JWT token to invalidate
            
        Returns:
            True if token was invalidated, False otherwise
        """
        try:
            session = self.active_sessions.get(token)
            if session:
                session["is_active"] = False
                logger.info(f"Token invalidated for user '{session['username']}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Error invalidating token: {e}")
            return False
    
    def check_permission(self, user_data: Dict[str, Any], required_permission: str) -> bool:
        """
        Check if user has required permission
        
        Args:
            user_data: User information from token
            required_permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            user_permissions = user_data.get("permissions", [])
            return required_permission in user_permissions
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    def require_permission(self, user_data: Dict[str, Any], required_permission: str) -> None:
        """
        Require user to have specific permission, raise exception if not
        
        Args:
            user_data: User information from token
            required_permission: Permission to check
            
        Raises:
            PortAdaPermissionError: If user lacks required permission
        """
        if not self.check_permission(user_data, required_permission):
            raise PortAdaPermissionError(
                message=f"User '{user_data.get('username', 'unknown')}' lacks required permission: {required_permission}",
                error_code="INSUFFICIENT_PERMISSIONS",
                details={
                    "required_permission": required_permission,
                    "user_permissions": user_data.get("permissions", [])
                }
            )
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by username
        
        Args:
            username: Username to look up
            
        Returns:
            User information (without password hash) if found, None otherwise
        """
        try:
            user = self.users_db.get(username)
            if user:
                return {
                    "username": user["username"],
                    "role": user["role"],
                    "permissions": user["permissions"],
                    "full_name": user["full_name"],
                    "email": user["email"],
                    "is_active": user["is_active"]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user info for '{username}': {e}")
            return None
    
    def list_active_sessions(self) -> Dict[str, Any]:
        """
        List all active sessions (for admin purposes)
        
        Returns:
            Dictionary of active sessions
        """
        try:
            active_sessions = {}
            for token, session in self.active_sessions.items():
                if session.get("is_active", False) and datetime.utcnow() <= session["expires_at"]:
                    active_sessions[session["session_id"]] = {
                        "username": session["username"],
                        "created_at": session["created_at"].isoformat(),
                        "expires_at": session["expires_at"].isoformat()
                    }
            return active_sessions
        except Exception as e:
            logger.error(f"Error listing active sessions: {e}")
            return {}


# Global authentication service instance
auth_service = AuthService()