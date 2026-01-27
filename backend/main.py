"""
Main FastAPI application for PortAda Data Ingestion and Analysis System
Enhanced with comprehensive service management and dependency injection
"""

import logging
from app.core.app_factory import create_app

# Create the FastAPI application using the factory
app = create_app()

# Get logger for this module
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    
    logger.info("Starting PortAda API server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )