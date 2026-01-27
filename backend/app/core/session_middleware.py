"""
Session middleware for automatic session management across all requests
"""

import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..database import DatabaseService
from ..session import SessionManager
from ..core.config import settings

logger = logging.getLogger(__name__)


class SessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically manages user sessions for all requests.
    
    Provides transparent session creation, validation, and management
    without requiring explicit session handling in each endpoint.
    """
    
    def __init__(self, app, database_service: DatabaseService = None):
        """
        Initialize session middleware.
        
        Args:
            app: FastAPI application instance
            database_service: DatabaseService instance (optional, will create if None)
        """
        super().__init__(app)
        self.database_service = database_service or DatabaseService()
        self.session_manager = SessionManager(self.database_service)
        self.initialized = False
        
        # Paths that should be excluded from session management
        self.excluded_paths = {
            "/docs", "/redoc", "/openapi.json", "/health", "/favicon.ico"
        }
        
        # Paths that require session management
        self.session_required_paths = {
            "/api/ingestion/upload", "/api/enhanced/upload", "/api/ingestion/history"
        }
        
        logger.info("SessionMiddleware initialized")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with automatic session management.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response: HTTP response with session information
        """
        try:
            # Initialize database service if needed
            if not self.initialized:
                await self._initialize()
            
            # Skip session management for excluded paths
            if self._should_skip_session(request):
                return await call_next(request)
            
            # Get or create session
            session_info = await self._handle_session(request)
            
            # Add session info to request state
            request.state.session_id = session_info["session_id"]
            request.state.session = session_info["session"]
            request.state.is_new_session = session_info["is_new_session"]
            
            # Process the request
            response = await call_next(request)
            
            # Add session information to response headers (if needed)
            if session_info["is_new_session"] and hasattr(response, 'set_cookie'):
                self._set_session_cookie(response, session_info["session_id"])
            
            # Add session ID to response headers for debugging
            if hasattr(response, 'headers'):
                response.headers["X-Session-ID"] = session_info["session_id"]
            
            return response
            
        except Exception as e:
            logger.error(f"Error in session middleware: {e}")
            
            # Continue without session management on error
            try:
                response = await call_next(request)
                return response
            except Exception as inner_e:
                logger.error(f"Error in request processing after session error: {inner_e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal server error",
                        "message": "Session management failed"
                    }
                )
    
    async def _initialize(self) -> None:
        """Initialize the database service"""
        try:
            if not self.database_service._initialized:
                await self.database_service.initialize()
            self.initialized = True
            logger.info("SessionMiddleware database service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize session middleware database: {e}")
            # Continue without database - sessions will be memory-only
    
    def _should_skip_session(self, request: Request) -> bool:
        """
        Determine if session management should be skipped for this request.
        
        Args:
            request: HTTP request
            
        Returns:
            bool: True if session management should be skipped
        """
        path = request.url.path
        
        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return True
        
        # Skip for excluded paths
        if any(excluded in path for excluded in self.excluded_paths):
            return True
        
        # Skip for static files
        if path.startswith("/static/") or path.endswith((".css", ".js", ".png", ".jpg", ".ico")):
            return True
        
        # Skip for health checks
        if "health" in path.lower():
            return True
        
        return False
    
    async def _handle_session(self, request: Request) -> dict:
        """
        Handle session creation or retrieval for the request.
        
        Args:
            request: HTTP request
            
        Returns:
            dict: Session information
        """
        try:
            # Try to get existing session
            session_id = self._extract_session_id(request)
            session = None
            is_new_session = False
            
            if session_id:
                session = await self.session_manager.get_session_by_id(session_id)
                
                if session and not session.is_expired():
                    # Update session access time
                    await self.session_manager.database_service.update_session_access(session_id)
                    logger.debug(f"Retrieved existing session: {session_id}")
                else:
                    # Session expired or not found, create new one
                    session = None
                    session_id = None
            
            # Create new session if needed
            if not session:
                client_info = self._get_client_info(request)
                session = await self.session_manager.create_new_session(client_info)
                session_id = session.id
                is_new_session = True
                logger.info(f"Created new session: {session_id}")
            
            return {
                "session_id": session_id,
                "session": session,
                "is_new_session": is_new_session
            }
            
        except Exception as e:
            logger.error(f"Error handling session: {e}")
            
            # Fallback: create a minimal session
            import uuid
            fallback_session_id = str(uuid.uuid4())
            return {
                "session_id": fallback_session_id,
                "session": None,
                "is_new_session": True
            }
    
    def _extract_session_id(self, request: Request) -> str:
        """
        Extract session ID from request (cookie, header, or query param).
        
        Args:
            request: HTTP request
            
        Returns:
            str or None: Session ID if found
        """
        # Try cookie first
        session_id = request.cookies.get(self.session_manager.SESSION_COOKIE_NAME)
        if session_id:
            return session_id
        
        # Try header
        session_id = request.headers.get(self.session_manager.SESSION_HEADER_NAME)
        if session_id:
            return session_id
        
        # Try query parameter (for debugging/testing)
        session_id = request.query_params.get('session_id')
        if session_id:
            return session_id
        
        return None
    
    def _set_session_cookie(self, response: Response, session_id: str) -> None:
        """
        Set session cookie in response.
        
        Args:
            response: HTTP response
            session_id: Session ID to set in cookie
        """
        try:
            if hasattr(response, 'set_cookie'):
                from datetime import datetime, timedelta, timezone
                
                # Calculate cookie expiration with UTC timezone
                expires = datetime.now(timezone.utc) + timedelta(days=settings.database.SESSION_DURATION_DAYS)
                
                response.set_cookie(
                    key=self.session_manager.SESSION_COOKIE_NAME,
                    value=session_id,
                    expires=expires,
                    httponly=True,
                    secure=False,  # Set to True in production with HTTPS
                    samesite="lax",
                    path="/"
                )
                
                logger.debug(f"Set session cookie: {session_id}")
        except Exception as e:
            logger.error(f"Failed to set session cookie: {e}")
    
    def _get_client_info(self, request: Request) -> dict:
        """
        Extract client information from request for session metadata.
        
        Args:
            request: HTTP request
            
        Returns:
            dict: Client information
        """
        try:
            return {
                "user_agent": request.headers.get("user-agent"),
                "ip_address": self._get_client_ip(request),
                "referer": request.headers.get("referer"),
                "accept_language": request.headers.get("accept-language"),
                "request_path": request.url.path,
                "request_method": request.method
            }
        except Exception as e:
            logger.error(f"Error extracting client info: {e}")
            return {}
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request, handling proxies.
        
        Args:
            request: HTTP request
            
        Returns:
            str or None: Client IP address
        """
        try:
            # Check for forwarded headers (proxy/load balancer)
            forwarded_for = request.headers.get('x-forwarded-for')
            if forwarded_for:
                return forwarded_for.split(',')[0].strip()
            
            # Check for real IP header
            real_ip = request.headers.get('x-real-ip')
            if real_ip:
                return real_ip
            
            # Fall back to direct connection
            if hasattr(request, 'client') and request.client:
                return request.client.host
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting client IP: {e}")
            return None


# Dependency function to get session from request state
def get_current_session(request: Request) -> dict:
    """
    Get current session information from request state.
    
    Args:
        request: HTTP request with session state
        
    Returns:
        dict: Session information
    """
    try:
        return {
            "session_id": getattr(request.state, "session_id", None),
            "session": getattr(request.state, "session", None),
            "is_new_session": getattr(request.state, "is_new_session", False)
        }
    except Exception as e:
        logger.error(f"Error getting current session: {e}")
        return {
            "session_id": None,
            "session": None,
            "is_new_session": False
        }


# Dependency function to get session ID
def get_session_id(request: Request) -> str:
    """
    Get current session ID from request state.
    
    Args:
        request: HTTP request with session state
        
    Returns:
        str: Session ID or None if not available
    """
    try:
        return getattr(request.state, "session_id", None)
    except Exception:
        return None