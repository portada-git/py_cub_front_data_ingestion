"""
Application startup validation and initialization
"""

import logging
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

from .config_manager import ConfigurationManager, ValidationResult
from .config import settings

logger = logging.getLogger(__name__)


class StartupValidator:
    """
    Handles application startup validation and initialization.
    
    This class provides a centralized way to validate that all
    requirements are met before the application starts.
    """
    
    def __init__(self):
        """Initialize the StartupValidator"""
        self.config_manager = ConfigurationManager()
        self.validation_results: Optional[ValidationResult] = None
        logger.info("StartupValidator initialized")
    
    def validate_and_prepare_startup(self) -> bool:
        """
        Validate all startup requirements and prepare the application.
        
        This method performs comprehensive validation and attempts
        to fix common issues automatically.
        
        Returns:
            bool: True if application is ready to start, False otherwise
        """
        try:
            logger.info("Starting application startup validation and preparation")
            
            # Step 1: Validate configuration
            logger.info("Step 1: Validating configuration...")
            validation_result = self.config_manager.validate_startup_requirements()
            self.validation_results = validation_result
            
            if not validation_result.is_valid:
                logger.error("Configuration validation failed")
                self._log_validation_errors(validation_result)
                
                # Attempt automatic fixes
                logger.info("Attempting to fix startup issues automatically...")
                is_ready, remaining_issues = self.config_manager.ensure_startup_readiness()
                
                if not is_ready:
                    logger.error("Could not fix all startup issues")
                    self._log_remaining_issues(remaining_issues)
                    return False
                
                logger.info("Successfully fixed startup issues")
            
            # Step 2: Initialize core directories
            logger.info("Step 2: Initializing core directories...")
            if not self._initialize_directories():
                logger.error("Directory initialization failed")
                return False
            
            # Step 3: Validate database setup
            logger.info("Step 3: Validating database setup...")
            if not self._validate_database_setup():
                logger.error("Database setup validation failed")
                return False
            
            # Step 4: Initialize services
            logger.info("Step 4: Initializing core services...")
            if not self._initialize_core_services():
                logger.error("Core services initialization failed")
                return False
            
            logger.info("Application startup validation and preparation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during startup validation and preparation: {e}")
            return False
    
    def _initialize_directories(self) -> bool:
        """
        Initialize all required directories.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            directories_to_create = [
                Path(settings.storage.STORAGE_BASE_PATH),
                Path(settings.storage.INGESTION_STORAGE_PATH),
                Path(settings.PORTADA_BASE_PATH),
                Path(settings.INGESTION_FOLDER)
            ]
            
            for directory in directories_to_create:
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Directory ready: {directory}")
                    
                    # Test write permissions
                    test_file = directory / ".write_test"
                    test_file.touch()
                    test_file.unlink()
                    
                except Exception as e:
                    logger.error(f"Failed to initialize directory {directory}: {e}")
                    return False
            
            logger.info("All directories initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing directories: {e}")
            return False
    
    def _validate_database_setup(self) -> bool:
        """
        Validate database setup and connectivity.
        
        Returns:
            bool: True if database is ready, False otherwise
        """
        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.pool import StaticPool
            
            db_url = settings.database.DATABASE_URL
            logger.debug(f"Testing database connectivity: {self.config_manager._mask_sensitive_info(db_url)}")
            
            # Create engine with appropriate configuration
            if 'sqlite' in db_url.lower():
                engine = create_engine(
                    db_url,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False},
                    echo=settings.database.DATABASE_ECHO
                )
            else:
                engine = create_engine(db_url, echo=settings.database.DATABASE_ECHO)
            
            # Test connectivity
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.scalar() != 1:
                    logger.error("Database connectivity test failed")
                    return False
            
            engine.dispose()
            logger.info("Database setup validation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database setup validation failed: {e}")
            return False
    
    def _initialize_core_services(self) -> bool:
        """
        Initialize and test core services.
        
        Returns:
            bool: True if all services initialized successfully, False otherwise
        """
        try:
            # Test service imports
            service_modules = [
                'app.storage.directory_manager',
                'app.storage.storage_service',
                'app.database.database_service',
                'app.session.session_manager',
                'app.services.enhanced_file_handler',
                'app.services.concurrent_upload_manager',
                'app.services.entity_validator'
            ]
            
            for module_name in service_modules:
                try:
                    __import__(module_name)
                    logger.debug(f"Service module imported successfully: {module_name}")
                except ImportError as e:
                    logger.error(f"Failed to import service module {module_name}: {e}")
                    return False
            
            logger.info("Core services initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing core services: {e}")
            return False
    
    def _log_validation_errors(self, validation_result: ValidationResult) -> None:
        """Log validation errors in a structured way"""
        if validation_result.errors:
            logger.error(f"Validation failed with {len(validation_result.errors)} errors:")
            for i, error in enumerate(validation_result.errors, 1):
                logger.error(f"  {i}. {error}")
        
        if validation_result.warnings:
            logger.warning(f"Validation completed with {len(validation_result.warnings)} warnings:")
            for i, warning in enumerate(validation_result.warnings, 1):
                logger.warning(f"  {i}. {warning}")
    
    def _log_remaining_issues(self, issues: List[str]) -> None:
        """Log remaining issues that could not be fixed automatically"""
        if issues:
            logger.error(f"Remaining startup issues that require manual intervention:")
            for i, issue in enumerate(issues, 1):
                logger.error(f"  {i}. {issue}")
    
    def get_startup_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive startup validation report.
        
        Returns:
            dict: Startup validation report
        """
        try:
            if not self.validation_results:
                # Run validation if not already done
                self.validation_results = self.config_manager.validate_startup_requirements()
            
            # Get configuration report
            config_report = self.config_manager.generate_configuration_report()
            
            # Add startup-specific information
            startup_report = {
                "startup_validation": {
                    "is_ready": self.validation_results.is_valid,
                    "validation_timestamp": config_report.get("report_timestamp"),
                    "errors": self.validation_results.errors,
                    "warnings": self.validation_results.warnings
                },
                "configuration_report": config_report,
                "system_requirements": {
                    "python_version_ok": sys.version_info >= (3, 8),
                    "required_directories": [
                        settings.storage.STORAGE_BASE_PATH,
                        settings.storage.INGESTION_STORAGE_PATH,
                        settings.PORTADA_BASE_PATH,
                        settings.INGESTION_FOLDER
                    ],
                    "database_type": "sqlite" if "sqlite" in settings.database.DATABASE_URL.lower() else "other"
                }
            }
            
            return startup_report
            
        except Exception as e:
            logger.error(f"Error generating startup report: {e}")
            return {
                "startup_validation": {
                    "is_ready": False,
                    "error": str(e)
                }
            }
    
    def print_startup_summary(self) -> None:
        """Print a human-readable startup validation summary"""
        try:
            report = self.get_startup_report()
            startup_info = report.get("startup_validation", {})
            
            print("\n" + "="*60)
            print("APPLICATION STARTUP VALIDATION SUMMARY")
            print("="*60)
            
            if startup_info.get("is_ready", False):
                print("✅ Application is READY to start")
            else:
                print("❌ Application is NOT READY to start")
            
            # Print errors
            errors = startup_info.get("errors", [])
            if errors:
                print(f"\n❌ ERRORS ({len(errors)}):")
                for i, error in enumerate(errors, 1):
                    print(f"   {i}. {error}")
            
            # Print warnings
            warnings = startup_info.get("warnings", [])
            if warnings:
                print(f"\n⚠️  WARNINGS ({len(warnings)}):")
                for i, warning in enumerate(warnings, 1):
                    print(f"   {i}. {warning}")
            
            # Print system info
            config_report = report.get("configuration_report", {})
            env_info = config_report.get("environment_info", {})
            
            print(f"\n📊 SYSTEM INFO:")
            print(f"   Python: {env_info.get('python_version', 'unknown')}")
            print(f"   Platform: {env_info.get('platform', 'unknown')}")
            print(f"   Memory: {env_info.get('memory_mb', 0)}MB")
            print(f"   Disk Space: {env_info.get('disk_space_mb', 0)}MB")
            
            # Print configuration
            config_values = config_report.get("configuration_values", {})
            storage_config = config_values.get("storage", {})
            
            print(f"\n⚙️  CONFIGURATION:")
            print(f"   Storage Path: {storage_config.get('base_path', 'not set')}")
            print(f"   Ingestion Path: {storage_config.get('ingestion_path', 'not set')}")
            print(f"   Max File Size: {storage_config.get('max_file_size_mb', 0)}MB")
            print(f"   Database: {config_values.get('database', {}).get('url', 'not set')}")
            
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n❌ Error generating startup summary: {e}\n")


def validate_startup() -> bool:
    """
    Convenience function to validate application startup.
    
    Returns:
        bool: True if application is ready to start, False otherwise
    """
    validator = StartupValidator()
    return validator.validate_and_prepare_startup()


def get_startup_validator() -> StartupValidator:
    """
    Get a StartupValidator instance.
    
    Returns:
        StartupValidator: Configured startup validator
    """
    return StartupValidator()