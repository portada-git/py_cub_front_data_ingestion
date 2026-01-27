"""
Logging configuration for the PortAda application
"""

import logging
import sys
from typing import Dict, Any
from app.core.config import settings


def setup_logging() -> None:
    """Set up application logging configuration"""
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            # Add file handler if needed
            # logging.FileHandler('app.log')
        ]
    )
    
    # Configure specific loggers
    loggers_config = {
        'uvicorn': logging.INFO,
        'uvicorn.error': logging.INFO,
        'uvicorn.access': logging.WARNING,
        'fastapi': logging.INFO,
        'app': getattr(logging, settings.LOG_LEVEL.upper()),
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)