"""
Middleware for error handling and request processing
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from typing import Callable

from app.core.exceptions import PortAdaBaseException, get_user_friendly_message

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to handle PortAda exceptions and convert them to HTTP responses"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
        except PortAdaBaseException as e:
            logger.error(f"PortAda error in {request.url.path}: {e.message}")
            
            # Determine HTTP status code based on error type
            status_code = self._get_status_code(e)
            
            # Create error response
            error_response = {
                "error": True,
                "message": get_user_friendly_message(e),
                "error_code": e.error_code,
                "details": e.details if logger.level <= logging.DEBUG else {}
            }
            
            return JSONResponse(
                status_code=status_code,
                content=error_response
            )
        except HTTPException:
            # Let FastAPI handle HTTP exceptions normally
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {request.url.path}: {str(e)}", exc_info=True)
            
            # Generic error response for unexpected errors
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "An unexpected error occurred. Please try again or contact support.",
                    "error_code": "INTERNAL_ERROR"
                }
            )
    
    def _get_status_code(self, error: PortAdaBaseException) -> int:
        """Map PortAda error codes to HTTP status codes"""
        status_mapping = {
            "CONNECTION_FAILED": 503,  # Service Unavailable
            "CONFIGURATION_ERROR": 500,  # Internal Server Error
            "OPERATION_TIMEOUT": 504,  # Gateway Timeout
            "ACCESS_DENIED": 403,  # Forbidden
            "FILE_ERROR": 400,  # Bad Request
            "VALIDATION_ERROR": 400,  # Bad Request
            "INGESTION_ERROR": 422,  # Unprocessable Entity
            "QUERY_ERROR": 500,  # Internal Server Error
            "UNKNOWN_ERROR": 500,  # Internal Server Error
        }
        
        return status_mapping.get(error.error_code, 500)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log API requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        logger.info(f"Response: {response.status_code} for {request.method} {request.url.path}")
        
        return response