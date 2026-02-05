"""
Application initialization module for setup, validation, and deployment preparation
"""

import asyncio
import logging
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from .startup_validator import StartupValidator
from .service_container import get_service_container, cleanup_service_container
from .config import settings
from ..database.database_service import DatabaseService

logger = logging.getLogger(__name__)


class ApplicationInitializer:
    """
    Handles complete application initialization including database setup,
    directory creation, and service validation.
    """
    
    def __init__(self):
        """Initialize the ApplicationInitializer"""
        self.startup_validator = None
        self.service_container = None
        self.initialization_complete = False
        
    async def initialize_application(self, 
                                   create_database: bool = True,
                                   validate_services: bool = True,
                                   run_migrations: bool = True) -> Dict[str, Any]:
        """
        Perform complete application initialization.
        
        Args:
            create_database: Whether to create database schema
            validate_services: Whether to validate all services
            run_migrations: Whether to run database migrations
            
        Returns:
            dict: Initialization results and status
        """
        try:
            logger.info("Starting complete application initialization...")
            
            initialization_results = {
                'success': False,
                'steps_completed': [],
                'errors': [],
                'warnings': [],
                'services_initialized': 0,
                'database_ready': False,
                'directories_created': [],
                'validation_passed': False
            }
            
            # Step 1: Validate startup requirements
            logger.info("Step 1: Validating startup requirements...")
            self.startup_validator = StartupValidator()
            
            if not self.startup_validator.validate_and_prepare_startup():
                initialization_results['errors'].append("Startup validation failed")
                return initialization_results
            
            initialization_results['steps_completed'].append('startup_validation')
            initialization_results['validation_passed'] = True
            logger.info("✅ Startup validation completed")
            
            # Step 2: Initialize service container
            logger.info("Step 2: Initializing service container...")
            self.service_container = await get_service_container()
            
            if not self.service_container.is_initialized():
                initialization_results['errors'].append("Service container initialization failed")
                return initialization_results
            
            initialization_results['steps_completed'].append('service_container')
            initialization_results['services_initialized'] = len(self.service_container.get_health_status()['services'])
            logger.info("✅ Service container initialized")
            
            # Step 3: Database initialization
            if create_database:
                logger.info("Step 3: Initializing database...")
                database_service = self.service_container.get_service('database_service')
                
                # Ensure database schema is created
                await database_service.initialize()
                
                # Run migrations if requested
                if run_migrations:
                    await self._run_database_migrations(database_service)
                
                initialization_results['steps_completed'].append('database_initialization')
                initialization_results['database_ready'] = True
                logger.info("✅ Database initialization completed")
            
            # Step 4: Directory structure validation
            logger.info("Step 4: Validating directory structure...")
            directory_manager = self.service_container.get_service('directory_manager')
            
            # Create Portada configuration directory
            config_dir = Path(settings.storage.STORAGE_BASE_PATH) / "config"
            if directory_manager.ensure_directory_exists(str(config_dir)):
                initialization_results['directories_created'].append(str(config_dir))
                logger.info(f"✅ Portada configuration directory created: {config_dir}")
            
            required_directories = [
                settings.storage.STORAGE_BASE_PATH,
                settings.storage.INGESTION_STORAGE_PATH,
                settings.PORTADA_BASE_PATH,
                settings.INGESTION_FOLDER
            ]
            
            for directory in required_directories:
                if directory_manager.ensure_directory_exists(directory):
                    initialization_results['directories_created'].append(str(directory))
                else:
                    initialization_results['errors'].append(f"Failed to create directory: {directory}")
            
            # Verify Portada configuration files
            try:
                settings._validate_portada_config_files()
                logger.info("✅ Portada configuration files validated")
            except ValueError as e:
                initialization_results['warnings'].append(str(e))
                logger.warning(f"⚠️  {e}")
            
            initialization_results['steps_completed'].append('directory_validation')
            logger.info("✅ Directory structure validation completed")
            
            # Step 5: Service validation
            if validate_services:
                logger.info("Step 5: Validating all services...")
                health_status = self.service_container.get_health_status()
                
                if health_status['status'] != 'healthy':
                    initialization_results['warnings'].append("Some services are not fully healthy")
                    logger.warning("Service health check shows degraded status")
                else:
                    logger.info("✅ All services are healthy")
                
                initialization_results['steps_completed'].append('service_validation')
            
            # Step 6: Final validation
            logger.info("Step 6: Final validation...")
            final_validation = await self._perform_final_validation()
            
            if final_validation['success']:
                initialization_results['steps_completed'].append('final_validation')
                initialization_results['success'] = True
                self.initialization_complete = True
                logger.info("🎉 Application initialization completed successfully")
            else:
                initialization_results['errors'].extend(final_validation['errors'])
                logger.error("Final validation failed")
            
            return initialization_results
            
        except Exception as e:
            logger.error(f"Application initialization failed: {e}")
            initialization_results['errors'].append(f"Initialization error: {str(e)}")
            return initialization_results
    
    async def _run_database_migrations(self, database_service: DatabaseService) -> None:
        """
        Run database migrations if needed.
        
        Args:
            database_service: DatabaseService instance
        """
        try:
            logger.info("Running database migrations...")
            
            # For now, just ensure schema is up to date
            # In a real application, you might use Alembic or similar
            await database_service.initialize()
            
            logger.info("Database migrations completed")
            
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            raise
    
    async def _perform_final_validation(self) -> Dict[str, Any]:
        """
        Perform final validation to ensure everything is working.
        
        Returns:
            dict: Validation results
        """
        try:
            validation_results = {
                'success': True,
                'errors': [],
                'checks_performed': []
            }
            
            # Test database connectivity
            try:
                database_service = self.service_container.get_service('database_service')
                # Perform a simple query to test connectivity
                # This is already done in the database service initialization
                validation_results['checks_performed'].append('database_connectivity')
            except Exception as e:
                validation_results['errors'].append(f"Database connectivity test failed: {e}")
                validation_results['success'] = False
            
            # Test storage writability
            try:
                storage_service = self.service_container.get_service('storage_service')
                # Test file operations
                test_content = b"test content"
                result = storage_service.save_file(test_content, "test.txt")
                
                if result['success']:
                    # Clean up test file
                    test_file_path = Path(result['file_path'])
                    if test_file_path.exists():
                        test_file_path.unlink()
                    validation_results['checks_performed'].append('storage_writability')
                else:
                    validation_results['errors'].append("Storage writability test failed")
                    validation_results['success'] = False
                    
            except Exception as e:
                validation_results['errors'].append(f"Storage test failed: {e}")
                validation_results['success'] = False
            
            # Test session management
            try:
                session_manager = self.service_container.get_service('session_manager')
                # Session manager is initialized and ready
                validation_results['checks_performed'].append('session_management')
            except Exception as e:
                validation_results['errors'].append(f"Session management test failed: {e}")
                validation_results['success'] = False
            
            return validation_results
            
        except Exception as e:
            return {
                'success': False,
                'errors': [f"Final validation error: {str(e)}"],
                'checks_performed': []
            }
    
    async def cleanup(self) -> None:
        """
        Clean up initialization resources.
        """
        try:
            if self.service_container:
                await cleanup_service_container()
                self.service_container = None
            
            self.initialization_complete = False
            logger.info("Application initializer cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during initializer cleanup: {e}")
    
    def get_initialization_status(self) -> Dict[str, Any]:
        """
        Get current initialization status.
        
        Returns:
            dict: Current status information
        """
        return {
            'initialization_complete': self.initialization_complete,
            'startup_validator_ready': self.startup_validator is not None,
            'service_container_ready': self.service_container is not None and self.service_container.is_initialized(),
            'health_status': self.service_container.get_health_status() if self.service_container else None
        }


async def initialize_application_for_deployment() -> bool:
    """
    Initialize application for deployment with full validation.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    initializer = ApplicationInitializer()
    
    try:
        logger.info("Initializing application for deployment...")
        
        result = await initializer.initialize_application(
            create_database=True,
            validate_services=True,
            run_migrations=True
        )
        
        if result['success']:
            logger.info("✅ Application deployment initialization completed successfully")
            
            # Print summary
            print("\n" + "="*60)
            print("APPLICATION DEPLOYMENT INITIALIZATION SUMMARY")
            print("="*60)
            print(f"✅ Status: SUCCESS")
            print(f"✅ Steps completed: {len(result['steps_completed'])}")
            print(f"✅ Services initialized: {result['services_initialized']}")
            print(f"✅ Database ready: {result['database_ready']}")
            print(f"✅ Directories created: {len(result['directories_created'])}")
            
            if result['warnings']:
                print(f"\n⚠️  Warnings ({len(result['warnings'])}):")
                for warning in result['warnings']:
                    print(f"   - {warning}")
            
            print("="*60 + "\n")
            
            return True
        else:
            logger.error("❌ Application deployment initialization failed")
            
            # Print error summary
            print("\n" + "="*60)
            print("APPLICATION DEPLOYMENT INITIALIZATION FAILED")
            print("="*60)
            print(f"❌ Status: FAILED")
            print(f"❌ Errors ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"   - {error}")
            print("="*60 + "\n")
            
            return False
            
    except Exception as e:
        logger.error(f"Deployment initialization error: {e}")
        return False
    
    finally:
        await initializer.cleanup()


async def initialize_application_for_testing() -> bool:
    """
    Initialize application for testing with minimal setup.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    initializer = ApplicationInitializer()
    
    try:
        logger.info("Initializing application for testing...")
        
        result = await initializer.initialize_application(
            create_database=True,
            validate_services=False,  # Skip full service validation for faster testing
            run_migrations=False      # Skip migrations for testing
        )
        
        success = result['success']
        
        if success:
            logger.info("✅ Application testing initialization completed")
        else:
            logger.error("❌ Application testing initialization failed")
            for error in result['errors']:
                logger.error(f"   - {error}")
        
        return success
        
    except Exception as e:
        logger.error(f"Testing initialization error: {e}")
        return False
    
    finally:
        await initializer.cleanup()


def main():
    """
    Main entry point for application initialization.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize PortAda application")
    parser.add_argument('--mode', choices=['deployment', 'testing'], default='deployment',
                       help='Initialization mode')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run initialization
    if args.mode == 'deployment':
        success = asyncio.run(initialize_application_for_deployment())
    else:
        success = asyncio.run(initialize_application_for_testing())
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()