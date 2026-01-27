"""
Session Manager for handling user session lifecycle, persistence, and state management
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from ..database.database_service import DatabaseService
from ..database.models import Session
from ..core.config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages user session lifecycle, persistence, and state management.
    
    Handles session creation, retrieval, validation, and cleanup operations
    to provide persistent user state across browser refreshes and multiple uploads.
    """
    
    SESSION_COOKIE_NAME = "portada_session_id"
    SESSION_HEADER_NAME = "X-Session-ID"
    
    def __init__(self, database_service: DatabaseService):
        """
        Initialize the SessionManager with database service.
        
        Args:
            database_service: DatabaseService instance for persistence
        """
        self.database_service = database_service
        self.session_duration_days = settings.database.SESSION_DURATION_DAYS
        self.cleanup_interval_hours = settings.database.SESSION_CLEANUP_INTERVAL_HOURS
        
        logger.info(f"SessionManager initialized with {self.session_duration_days} day session duration")
    
    async def create_or_get_session(self, request: Request, response: Optional[Response] = None) -> Session:
        """
        Create a new session or retrieve existing session from request.
        
        Args:
            request: FastAPI request object
            response: Optional FastAPI response object to set cookies
            
        Returns:
            Session: Active session object
        """
        try:
            # Try to get session ID from various sources
            session_id = self._extract_session_id(request)
            
            if session_id:
                # Try to retrieve existing session
                session = await self.get_session_by_id(session_id)
                if session and not session.is_expired():
                    # Update last accessed time
                    await self.database_service.update_session_access(session_id)
                    logger.debug(f"Retrieved existing session: {session_id}")
                    return session
                elif session and session.is_expired():
                    logger.info(f"Session expired, creating new session. Old session: {session_id}")
                else:
                    logger.warning(f"Session not found, creating new session. Requested: {session_id}")
            
            # Create new session
            session = await self.create_new_session()
            
            # Set session cookie if response is provided
            if response:
                self._set_session_cookie(response, session.id)
            
            logger.info(f"Created new session: {session.id}")
            return session
            
        except Exception as e:
            logger.error(f"Error in create_or_get_session: {e}")
            # Fallback: create new session without cookie
            return await self.create_new_session()
    
    async def create_new_session(self, metadata: Optional[Dict[str, Any]] = None) -> Session:
        """
        Create a new session with optional metadata.
        
        Args:
            metadata: Optional session metadata
            
        Returns:
            Session: Created session object
        """
        try:
            # Add default metadata
            session_metadata = {
                'created_by': 'session_manager',
                'user_agent': None,  # Will be set by caller if available
                'ip_address': None,  # Will be set by caller if available
                **(metadata or {})
            }
            
            session = await self.database_service.create_session(session_metadata)
            logger.info(f"Created new session: {session.id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create new session: {e}")
            raise
    
    async def get_session_by_id(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID with validation.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Session or None if not found or invalid
        """
        try:
            if not session_id or not isinstance(session_id, str):
                return None
            
            session = await self.database_service.get_session_by_id(session_id)
            
            if session:
                logger.debug(f"Retrieved session: {session_id}")
            else:
                logger.debug(f"Session not found: {session_id}")
            
            return session
            
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None
    
    async def is_session_valid(self, session_id: str) -> bool:
        """
        Check if a session is valid (exists and not expired).
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            bool: True if session is valid, False otherwise
        """
        try:
            session = await self.get_session_by_id(session_id)
            return session is not None and not session.is_expired()
            
        except Exception as e:
            logger.error(f"Error validating session {session_id}: {e}")
            return False
    
    async def extend_session(self, session_id: str, days: Optional[int] = None) -> bool:
        """
        Extend session expiration time.
        
        Args:
            session_id: Session ID to extend
            days: Number of days to extend (defaults to configured duration)
            
        Returns:
            bool: True if extended successfully, False otherwise
        """
        try:
            session = await self.get_session_by_id(session_id)
            if not session:
                logger.warning(f"Cannot extend non-existent session: {session_id}")
                return False
            
            # Extend expiration
            extension_days = days or self.session_duration_days
            session.extend_expiration(extension_days)
            
            # Update in database
            async with self.database_service.get_session() as db_session:
                db_session.add(session)
                await db_session.commit()
            
            logger.info(f"Extended session {session_id} by {extension_days} days")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False
    
    async def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a session by setting its expiration to the past.
        
        Args:
            session_id: Session ID to invalidate
            
        Returns:
            bool: True if invalidated successfully, False otherwise
        """
        try:
            session = await self.get_session_by_id(session_id)
            if not session:
                logger.warning(f"Cannot invalidate non-existent session: {session_id}")
                return False
            
            # Set expiration to past
            session.expires_at = datetime.utcnow() - timedelta(minutes=1)
            
            # Update in database
            async with self.database_service.get_session() as db_session:
                db_session.add(session)
                await db_session.commit()
            
            logger.info(f"Invalidated session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate session {session_id}: {e}")
            return False
    
    async def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update session metadata.
        
        Args:
            session_id: Session ID to update
            metadata: Metadata to merge with existing metadata
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            session = await self.get_session_by_id(session_id)
            if not session:
                logger.warning(f"Cannot update metadata for non-existent session: {session_id}")
                return False
            
            # Merge metadata
            current_metadata = session.session_metadata or {}
            current_metadata.update(metadata)
            session.session_metadata = current_metadata
            
            # Update in database
            async with self.database_service.get_session() as db_session:
                db_session.add(session)
                await db_session.commit()
            
            logger.debug(f"Updated metadata for session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session metadata {session_id}: {e}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions and return count of cleaned sessions.
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            count = await self.database_service.cleanup_expired_sessions()
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics for monitoring.
        
        Returns:
            dict: Session statistics
        """
        try:
            db_stats = await self.database_service.get_database_stats()
            
            return {
                'total_sessions': db_stats.get('total_sessions', 0),
                'expired_sessions': db_stats.get('expired_sessions', 0),
                'session_duration_days': self.session_duration_days,
                'cleanup_interval_hours': self.cleanup_interval_hours,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {
                'error': str(e),
                'last_updated': datetime.utcnow().isoformat()
            }
    
    def create_session_response(self, session: Session) -> JSONResponse:
        """
        Create a JSON response with session cookie set.
        
        Args:
            session: Session object to include in response
            
        Returns:
            JSONResponse: Response with session cookie
        """
        response_data = {
            'session': session.to_dict(),
            'message': 'Session created successfully'
        }
        
        response = JSONResponse(content=response_data)
        self._set_session_cookie(response, session.id)
        
        return response
    
    def _extract_session_id(self, request: Request) -> Optional[str]:
        """
        Extract session ID from request (cookie, header, or query param).
        
        Args:
            request: FastAPI request object
            
        Returns:
            str or None: Session ID if found
        """
        # Try cookie first
        session_id = request.cookies.get(self.SESSION_COOKIE_NAME)
        if session_id:
            return session_id
        
        # Try header
        session_id = request.headers.get(self.SESSION_HEADER_NAME)
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
            response: FastAPI response object
            session_id: Session ID to set in cookie
        """
        try:
            # Calculate cookie expiration (same as session expiration)
            expires = datetime.utcnow() + timedelta(days=self.session_duration_days)
            
            response.set_cookie(
                key=self.SESSION_COOKIE_NAME,
                value=session_id,
                expires=expires,
                httponly=True,  # Prevent XSS attacks
                secure=False,   # Set to True in production with HTTPS
                samesite="lax", # CSRF protection
                path="/"        # Available for entire application
            )
            
            logger.debug(f"Set session cookie: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to set session cookie: {e}")
    
    def _get_client_info(self, request: Request) -> Dict[str, Any]:
        """
        Extract client information from request for session metadata.
        
        Args:
            request: FastAPI request object
            
        Returns:
            dict: Client information
        """
        try:
            return {
                'user_agent': request.headers.get('user-agent'),
                'ip_address': self._get_client_ip(request),
                'referer': request.headers.get('referer'),
                'accept_language': request.headers.get('accept-language')
            }
        except Exception as e:
            logger.error(f"Error extracting client info: {e}")
            return {}
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """
        Get client IP address from request, handling proxies.
        
        Args:
            request: FastAPI request object
            
        Returns:
            str or None: Client IP address
        """
        try:
            # Check for forwarded headers (proxy/load balancer)
            forwarded_for = request.headers.get('x-forwarded-for')
            if forwarded_for:
                # Take the first IP in the chain
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