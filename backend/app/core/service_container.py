"""
Service Container for dependency injection and service management
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.core.config import settings
from app.core.startup_validator import StartupValidator
from app.storage.directory_manager import DirectoryManager
from app.storage.storage_service import StorageService
from app.database.database_service import DatabaseService
from app.session.session_manager import SessionManager
from app.session.session_cleanup import SessionCleanupService
from app.services.enhanced_file_handler import EnhancedFileHandler
from app.services.concurrent_upload_manager import ConcurrentUploadManager
from app.services.entity_validator import EntityValidator

logger = logging.getLogger(__name__)


@dataclass
class ServiceContainer:
    """
    Container for managing application services and their dependencies.
    
    Provides centralized service management with proper initialization
    order and dependency injection.
    """
    
    # Core services
    startup_validator: Optional[StartupValidator] = None
    directory_manager: Optional[DirectoryManager] = None
    storage_service: Optional[StorageService] = None
    database_service: Optional[DatabaseService] = None
    session_manager: Optional[SessionManager] = None
    session_cleanup_service: Optional[SessionCleanupService] = None
    
    # Enhanced services
    enhanced_file_handler: Optional[EnhancedFileHandler] = None
    concurrent_upload_manager: Optional[ConcurrentUploadManager] = None
    entity_validator: Optional[EntityValidator] = None
    
    # Service state
    _initialized: bool = False
    _startup_validated: bool = False
    
    async def initialize(self) -> bool:
        """
        Initialize all services in the correct order.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if self._initialized:
                logger.info("Service container already initialized")
                return True
            
            logger.info("Initializing service container...")
            
            # Step 1: Validate startup requirements
            logger.info("Step 1: Validating startup requirements...")
            self.startup_validator = StartupValidator()
            
            if not self.startup_validator.validate_and_prepare_startup():
                logger.error("Startup validation failed - cannot initialize services")
                return False
            
            self._startup_validated = True
            logger.info("✅ Startup validation completed successfully")
            
            # Step 2: Initialize core infrastructure services
            logger.info("Step 2: Initializing core infrastructure services...")
            
            # Directory Manager
            self.directory_manager = DirectoryManager(
                base_path=settings.storage.STORAGE_BASE_PATH
            )
            
            # Ensure required directories exist
            required_directories = [
                settings.storage.STORAGE_BASE_PATH,
                settings.storage.INGESTION_STORAGE_PATH,
                settings.PORTADA_BASE_PATH,
                settings.INGESTION_FOLDER
            ]
            
            for directory in required_directories:
                if not self.directory_manager.ensure_directory_exists(directory):
                    raise RuntimeError(f"Failed to create required directory: {directory}")
            
            logger.info("✅ Directory Manager initialized")
            
            # Storage Service
            self.storage_service = StorageService(
                storage_path=settings.storage.INGESTION_STORAGE_PATH
            )
            logger.info("✅ Storage Service initialized")
            
            # Database Service
            self.database_service = DatabaseService()
            await self.database_service.initialize()
            logger.info("✅ Database Service initialized")
            
            # Step 3: Initialize session management
            logger.info("Step 3: Initializing session management...")
            
            # Session Manager
            self.session_manager = SessionManager(
                database_service=self.database_service
            )
            logger.info("✅ Session Manager initialized")
            
            # Session Cleanup Service
            self.session_cleanup_service = SessionCleanupService(
                database_service=self.database_service,
                session_manager=self.session_manager
            )
            await self.session_cleanup_service.start_cleanup_scheduler()
            logger.info("✅ Session Cleanup Service initialized")
            
            # Step 4: Initialize enhanced services
            logger.info("Step 4: Initializing enhanced services...")
            
            # Enhanced File Handler
            self.enhanced_file_handler = EnhancedFileHandler(
                storage_service=self.storage_service,
                database_service=self.database_service
            )
            logger.info("✅ Enhanced File Handler initialized")
            
            # Concurrent Upload Manager
            self.concurrent_upload_manager = ConcurrentUploadManager(
                file_handler=self.enhanced_file_handler,
                max_concurrent_uploads=5,  # Configurable
                max_queue_size=100,
                upload_timeout_seconds=300  # 5 minutes
            )
            logger.info("✅ Concurrent Upload Manager initialized")
            
            # Entity Validator
            self.entity_validator = EntityValidator()
            logger.info("✅ Entity Validator initialized")
            
            self._initialized = True
            logger.info("🎉 Service container initialization completed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Service container initialization failed: {e}")
            await self.cleanup()
            return False
    
    async def cleanup(self) -> None:
        """
        Clean up all services and resources.
        """
        try:
            logger.info("Cleaning up service container...")
            
            # Stop session cleanup service
            if self.session_cleanup_service:
                await self.session_cleanup_service.stop_cleanup_scheduler()
                logger.info("Session cleanup service stopped")
            
            # Stop concurrent upload manager
            if self.concurrent_upload_manager:
                # Check if it has a shutdown method, otherwise skip
                if hasattr(self.concurrent_upload_manager, 'shutdown'):
                    await self.concurrent_upload_manager.shutdown()
                logger.info("Concurrent upload manager stopped")
            
            # Close database connections
            if self.database_service:
                await self.database_service.close()
                logger.info("Database service closed")
            
            self._initialized = False
            logger.info("Service container cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during service container cleanup: {e}")
    
    def get_service(self, service_name: str) -> Any:
        """
        Get a service by name.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The requested service instance
            
        Raises:
            ValueError: If service not found or container not initialized
        """
        if not self._initialized:
            raise ValueError("Service container not initialized")
        
        service_map = {
            'startup_validator': self.startup_validator,
            'directory_manager': self.directory_manager,
            'storage_service': self.storage_service,
            'database_service': self.database_service,
            'session_manager': self.session_manager,
            'session_cleanup_service': self.session_cleanup_service,
            'enhanced_file_handler': self.enhanced_file_handler,
            'concurrent_upload_manager': self.concurrent_upload_manager,
            'entity_validator': self.entity_validator
        }
        
        service = service_map.get(service_name)
        if service is None:
            raise ValueError(f"Service '{service_name}' not found")
        
        return service
    
    def is_initialized(self) -> bool:
        """Check if the service container is initialized."""
        return self._initialized
    
    def is_startup_validated(self) -> bool:
        """Check if startup validation passed."""
        return self._startup_validated
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all services.
        
        Returns:
            dict: Health status information
        """
        if not self._initialized:
            return {
                "status": "not_initialized",
                "services": {}
            }
        
        services_status = {}
        
        # Check each service
        service_checks = [
            ("startup_validator", self.startup_validator),
            ("directory_manager", self.directory_manager),
            ("storage_service", self.storage_service),
            ("database_service", self.database_service),
            ("session_manager", self.session_manager),
            ("session_cleanup_service", self.session_cleanup_service),
            ("enhanced_file_handler", self.enhanced_file_handler),
            ("concurrent_upload_manager", self.concurrent_upload_manager),
            ("entity_validator", self.entity_validator)
        ]
        
        all_healthy = True
        
        for service_name, service in service_checks:
            if service is None:
                services_status[service_name] = {"status": "not_initialized"}
                all_healthy = False
            else:
                # Check if service has a health check method
                if hasattr(service, 'get_health_status'):
                    try:
                        services_status[service_name] = service.get_health_status()
                        if services_status[service_name].get("status") != "healthy":
                            all_healthy = False
                    except Exception as e:
                        services_status[service_name] = {
                            "status": "error",
                            "error": str(e)
                        }
                        all_healthy = False
                else:
                    services_status[service_name] = {"status": "initialized"}
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "initialized": self._initialized,
            "startup_validated": self._startup_validated,
            "services": services_status
        }


# Global service container instance
_service_container: Optional[ServiceContainer] = None


async def get_service_container() -> ServiceContainer:
    """
    Get the global service container instance.
    
    Returns:
        ServiceContainer: The global service container
    """
    global _service_container
    
    if _service_container is None:
        _service_container = ServiceContainer()
        
        # Initialize the container
        if not await _service_container.initialize():
            raise RuntimeError("Failed to initialize service container")
    
    return _service_container


async def cleanup_service_container() -> None:
    """
    Clean up the global service container.
    """
    global _service_container
    
    if _service_container is not None:
        await _service_container.cleanup()
        _service_container = None


def get_service(service_name: str) -> Any:
    """
    Synchronous helper to get a service from the container.
    
    Args:
        service_name: Name of the service to retrieve
        
    Returns:
        The requested service instance
        
    Note:
        This assumes the container is already initialized.
        Use get_service_container() for async initialization.
    """
    global _service_container
    
    if _service_container is None or not _service_container.is_initialized():
        raise RuntimeError("Service container not initialized. Call get_service_container() first.")
    
    return _service_container.get_service(service_name)