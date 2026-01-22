"""
Main FastAPI application for PortAda Data Ingestion and Analysis System
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from app.core.config import settings
from app.api.routes import auth, ingestion, analysis
from app.core.logging import setup_logging
from app.core.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting PortAda API application")
    
    # Validate configuration
    try:
        settings.validate_config()
        logger.info("Configuration validated successfully")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    
    # Create ingestion folder if it doesn't exist
    os.makedirs(settings.INGESTION_FOLDER, exist_ok=True)
    logger.info(f"Ingestion folder ready: {settings.INGESTION_FOLDER}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PortAda API application")


# Create FastAPI application
app = FastAPI(
    title="PortAda Data Ingestion and Analysis API",
    description="API for managing historical newspaper data ingestion and analysis",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

# Add custom error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Add request logging middleware (optional, for debugging)
if settings.LOG_LEVEL.upper() in ["DEBUG", "INFO"]:
    app.add_middleware(RequestLoggingMiddleware)

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(ingestion.router, prefix="/api/ingestion", tags=["ingestion"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PortAda Data Ingestion and Analysis API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "portada-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )