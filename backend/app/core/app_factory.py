"""
Application factory for creating and configuring the FastAPI application
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from app.core.session_middleware import SessionMiddleware
from app.core.service_container import get_service_container, cleanup_service_container
from app.api.routes import auth, analysis
from app.api.routes import ingestion  # Original ingestion routes
from app.api.routes import enhanced_upload, history, statistics # New enhanced routes

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with enhanced service management"""
    # Startup
    setup_logging()
    logger.info("Starting PortAda API application with enhanced services")
    
    try:
        # Initialize service container
        logger.info("Initializing service container...")
        service_container = await get_service_container()
        
        # Store service container in app state for access in routes
        app.state.service_container = service_container
        
        logger.info("✅ Service container initialized successfully")
        logger.info(f"CORS allowed origins: {settings.cors_origins}")
        
        # Print startup summary
        if service_container.startup_validator:
            service_container.startup_validator.print_startup_summary()
        
        yield
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    # Shutdown
    logger.info("Shutting down PortAda API application")
    try:
        await cleanup_service_container()
        logger.info("✅ Service container cleanup completed")
    except Exception as e:
        logger.error(f"Error during service container cleanup: {e}")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    
    # Create FastAPI application
    app = FastAPI(
        title="PortAda Data Ingestion and Analysis API",
        description="Enhanced API for managing historical newspaper data ingestion and analysis",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )
    
    # Add CORS middleware first (most important for preflight requests)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    # Add trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
    )
    
    # Add session middleware for enhanced session management
    app.add_middleware(SessionMiddleware)
    
    # Add custom error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add request logging middleware (optional, for debugging)
    if settings.LOG_LEVEL.upper() in ["DEBUG", "INFO"]:
        app.add_middleware(RequestLoggingMiddleware)
    
    # Include API routes
    app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
    
    # Include both original and enhanced ingestion routes
    app.include_router(ingestion.router, prefix="/api/ingestion", tags=["ingestion"])
    app.include_router(enhanced_upload.router, prefix="/api/ingestion", tags=["enhanced-ingestion"])
    app.include_router(history.router, prefix="/api/ingestion", tags=["ingestion-history"])
    
    app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
    app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])
    
    # Import and include metadata router
    from app.api.routes import metadata
    app.include_router(metadata.router, prefix="/api/metadata", tags=["metadata"])
    
    # Add enhanced endpoints
    @app.get("/")
    async def root():
        """Root endpoint with enhanced information"""
        return {
            "message": "PortAda Data Ingestion and Analysis API",
            "version": "2.0.0",
            "features": [
                "Enhanced file upload with atomic operations",
                "Session-based processing history",
                "Concurrent upload management",
                "Comprehensive error handling",
                "Database persistence"
            ],
            "docs": "/api/docs"
        }
    
    @app.get("/api/health")
    async def health_check():
        """Enhanced health check endpoint"""
        try:
            # Get service container health status
            if hasattr(app.state, 'service_container') and app.state.service_container:
                health_status = app.state.service_container.get_health_status()
                return {
                    "status": health_status["status"],
                    "service": "portada-api",
                    "version": "2.0.0",
                    "services": health_status["services"],
                    "initialized": health_status["initialized"],
                    "startup_validated": health_status["startup_validated"]
                }
            else:
                return {
                    "status": "initializing",
                    "service": "portada-api",
                    "version": "2.0.0",
                    "message": "Service container not yet initialized"
                }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "service": "portada-api",
                "version": "2.0.0",
                "error": str(e)
            }
    
    @app.get("/api/cors-test")
    async def cors_test():
        """CORS test endpoint"""
        return {
            "message": "CORS is working",
            "allowed_origins": settings.cors_origins,
            "version": "2.0.0"
        }
    
    @app.get("/api/services/status")
    async def services_status():
        """Get detailed status of all services"""
        try:
            if hasattr(app.state, 'service_container') and app.state.service_container:
                return app.state.service_container.get_health_status()
            else:
                return {
                    "status": "not_initialized",
                    "message": "Service container not initialized"
                }
        except Exception as e:
            logger.error(f"Services status check failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Services status check failed: {str(e)}"
            )
    
    return app


# Dependency to get service container in routes
async def get_service_container_dependency():
    """
    FastAPI dependency to get the service container.
    
    Returns:
        ServiceContainer: The initialized service container
    """
    try:
        return await get_service_container()
    except Exception as e:
        logger.error(f"Failed to get service container: {e}")
        raise HTTPException(
            status_code=500,
            detail="Service container not available"
        )


# Convenience functions to get specific services
def get_storage_service():
    """Get the storage service from the container."""
    from app.core.service_container import get_service
    return get_service('storage_service')


def get_database_service():
    """Get the database service from the container."""
    from app.core.service_container import get_service
    return get_service('database_service')


def get_session_manager():
    """Get the session manager from the container."""
    from app.core.service_container import get_service
    return get_service('session_manager')


def get_enhanced_file_handler():
    """Get the enhanced file handler from the container."""
    from app.core.service_container import get_service
    return get_service('enhanced_file_handler')


def get_concurrent_upload_manager():
    """Get the concurrent upload manager from the container."""
    from app.core.service_container import get_service
    return get_service('concurrent_upload_manager')


def get_entity_validator():
    """Get the entity validator from the container."""
    from app.core.service_container import get_service
    return get_service('entity_validator')