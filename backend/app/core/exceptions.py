"""
Custom exception classes for the PortAda application
"""

from typing import Optional, Dict, Any


class PortAdaBaseException(Exception):
    """Base exception for all PortAda-related errors"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class PortAdaConnectionError(PortAdaBaseException):
    """Raised when connection to PortAda library fails"""
    pass


class PortAdaConfigurationError(PortAdaBaseException):
    """Raised when PortAda configuration is invalid"""
    pass


class PortAdaIngestionError(PortAdaBaseException):
    """Raised when data ingestion fails"""
    pass


class PortAdaQueryError(PortAdaBaseException):
    """Raised when data query operations fail"""
    pass


class PortAdaValidationError(PortAdaBaseException):
    """Raised when data validation fails"""
    pass


class PortAdaFileError(PortAdaBaseException):
    """Raised when file operations fail"""
    pass


class PortAdaTimeoutError(PortAdaBaseException):
    """Raised when operations timeout"""
    pass


class PortAdaAuthenticationError(PortAdaBaseException):
    """Raised when authentication fails"""
    pass


class PortAdaPermissionError(PortAdaBaseException):
    """Raised when user lacks required permissions"""
    pass


def wrap_portada_error(original_error: Exception, operation: str) -> PortAdaBaseException:
    """
    Wrap original PortAda library errors into user-friendly exceptions
    
    Args:
        original_error: The original exception from PortAda library
        operation: Description of the operation that failed
        
    Returns:
        Appropriate PortAda exception with user-friendly message
    """
    error_message = str(original_error)
    error_type = type(original_error).__name__
    
    # Map common error patterns to specific exception types
    if "connection" in error_message.lower() or "network" in error_message.lower():
        return PortAdaConnectionError(
            message=f"Failed to connect to PortAda service during {operation}",
            error_code="CONNECTION_FAILED",
            details={"operation": operation, "original_error": error_type},
            original_error=original_error
        )
    
    elif "configuration" in error_message.lower() or "config" in error_message.lower():
        return PortAdaConfigurationError(
            message=f"PortAda configuration error during {operation}",
            error_code="CONFIGURATION_ERROR",
            details={"operation": operation, "original_error": error_type},
            original_error=original_error
        )
    
    elif "timeout" in error_message.lower():
        return PortAdaTimeoutError(
            message=f"Operation timed out during {operation}",
            error_code="OPERATION_TIMEOUT",
            details={"operation": operation, "original_error": error_type},
            original_error=original_error
        )
    
    elif "permission" in error_message.lower() or "access" in error_message.lower():
        return PortAdaPermissionError(
            message=f"Access denied during {operation}",
            error_code="ACCESS_DENIED",
            details={"operation": operation, "original_error": error_type},
            original_error=original_error
        )
    
    elif "file" in error_message.lower() or "path" in error_message.lower():
        return PortAdaFileError(
            message=f"File operation failed during {operation}",
            error_code="FILE_ERROR",
            details={"operation": operation, "original_error": error_type},
            original_error=original_error
        )
    
    elif "validation" in error_message.lower() or "invalid" in error_message.lower():
        return PortAdaValidationError(
            message=f"Data validation failed during {operation}",
            error_code="VALIDATION_ERROR",
            details={"operation": operation, "original_error": error_type},
            original_error=original_error
        )
    
    elif "ingest" in error_message.lower():
        return PortAdaIngestionError(
            message=f"Data ingestion failed during {operation}",
            error_code="INGESTION_ERROR",
            details={"operation": operation, "original_error": error_type},
            original_error=original_error
        )
    
    elif "query" in error_message.lower() or "search" in error_message.lower():
        return PortAdaQueryError(
            message=f"Data query failed during {operation}",
            error_code="QUERY_ERROR",
            details={"operation": operation, "original_error": error_type},
            original_error=original_error
        )
    
    # Default to base exception for unknown errors
    return PortAdaBaseException(
        message=f"PortAda operation failed during {operation}: {error_message}",
        error_code="UNKNOWN_ERROR",
        details={"operation": operation, "original_error": error_type},
        original_error=original_error
    )


def get_user_friendly_message(error: PortAdaBaseException) -> str:
    """
    Get user-friendly error message for display in UI
    
    Args:
        error: PortAda exception
        
    Returns:
        User-friendly error message
    """
    error_messages = {
        "CONNECTION_FAILED": "Unable to connect to the data service. Please check your network connection and try again.",
        "CONFIGURATION_ERROR": "System configuration error. Please contact your administrator.",
        "OPERATION_TIMEOUT": "The operation took too long to complete. Please try again with a smaller dataset.",
        "ACCESS_DENIED": "You don't have permission to perform this operation. Please contact your administrator.",
        "FILE_ERROR": "There was a problem with the file. Please check the file format and try again.",
        "VALIDATION_ERROR": "The data format is invalid. Please check your input and try again.",
        "INGESTION_ERROR": "Failed to process the uploaded data. Please check the file format and try again.",
        "QUERY_ERROR": "Failed to retrieve the requested data. Please try again or contact support.",
        "UNKNOWN_ERROR": "An unexpected error occurred. Please try again or contact support."
    }
    
    return error_messages.get(error.error_code, error.message)