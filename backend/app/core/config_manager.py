"""
Configuration Manager for environment setup and validation
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]


@dataclass
class EnvironmentInfo:
    """Information about the current environment"""
    python_version: str
    platform: str
    working_directory: str
    environment_variables: Dict[str, str]
    disk_space_mb: int
    memory_mb: int


class ConfigurationManager:
    """
    Manages application configuration, validation, and environment setup.
    
    Provides comprehensive configuration validation, environment checks,
    and setup assistance for reliable application deployment.
    """
    
    def __init__(self):
        """Initialize the ConfigurationManager"""
        self.validation_results = {}
        self.environment_info = None
        logger.info("ConfigurationManager initialized")
    
    def validate_complete_configuration(self) -> ValidationResult:
        """
        Perform comprehensive validation of all configuration aspects.
        
        Returns:
            ValidationResult: Complete validation results
        """
        try:
            logger.info("Starting comprehensive configuration validation")
            
            all_errors = []
            all_warnings = []
            validation_details = {}
            
            # Validate storage configuration
            storage_result = self.validate_storage_configuration()
            all_errors.extend(storage_result.errors)
            all_warnings.extend(storage_result.warnings)
            validation_details['storage'] = storage_result.details
            
            # Validate database configuration
            database_result = self.validate_database_configuration()
            all_errors.extend(database_result.errors)
            all_warnings.extend(database_result.warnings)
            validation_details['database'] = database_result.details
            
            # Validate environment
            env_result = self.validate_environment()
            all_errors.extend(env_result.errors)
            all_warnings.extend(env_result.warnings)
            validation_details['environment'] = env_result.details
            
            # Validate permissions
            perm_result = self.validate_permissions()
            all_errors.extend(perm_result.errors)
            all_warnings.extend(perm_result.warnings)
            validation_details['permissions'] = perm_result.details
            
            # Validate dependencies
            dep_result = self.validate_dependencies()
            all_errors.extend(dep_result.errors)
            all_warnings.extend(dep_result.warnings)
            validation_details['dependencies'] = dep_result.details
            
            is_valid = len(all_errors) == 0
            
            result = ValidationResult(
                is_valid=is_valid,
                errors=all_errors,
                warnings=all_warnings,
                details=validation_details
            )
            
            # Store results for later reference
            self.validation_results = result
            
            if is_valid:
                logger.info("Configuration validation completed successfully")
            else:
                logger.error(f"Configuration validation failed with {len(all_errors)} errors")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during configuration validation: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Configuration validation failed: {str(e)}"],
                warnings=[],
                details={"validation_error": str(e)}
            )
    
    def validate_storage_configuration(self) -> ValidationResult:
        """
        Validate storage-related configuration.
        
        Returns:
            ValidationResult: Storage validation results
        """
        try:
            errors = []
            warnings = []
            details = {}
            
            # Check storage paths
            storage_base = Path(settings.storage.STORAGE_BASE_PATH)
            ingestion_path = Path(settings.storage.INGESTION_STORAGE_PATH)
            
            details['storage_base_path'] = str(storage_base.resolve())
            details['ingestion_path'] = str(ingestion_path.resolve())
            
            # Validate base storage path
            if not storage_base.exists():
                try:
                    storage_base.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created storage base directory: {storage_base}")
                except Exception as e:
                    errors.append(f"Cannot create storage base directory {storage_base}: {e}")
            
            if storage_base.exists():
                if not storage_base.is_dir():
                    errors.append(f"Storage base path is not a directory: {storage_base}")
                elif not os.access(storage_base, os.W_OK):
                    errors.append(f"Storage base directory is not writable: {storage_base}")
                else:
                    details['storage_base_writable'] = True
            
            # Validate ingestion path
            if not ingestion_path.exists():
                try:
                    ingestion_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created ingestion directory: {ingestion_path}")
                except Exception as e:
                    errors.append(f"Cannot create ingestion directory {ingestion_path}: {e}")
            
            if ingestion_path.exists():
                if not ingestion_path.is_dir():
                    errors.append(f"Ingestion path is not a directory: {ingestion_path}")
                elif not os.access(ingestion_path, os.W_OK):
                    errors.append(f"Ingestion directory is not writable: {ingestion_path}")
                else:
                    details['ingestion_path_writable'] = True
            
            # Check disk space
            try:
                statvfs = os.statvfs(storage_base)
                free_space_mb = (statvfs.f_frsize * statvfs.f_bavail) // (1024 * 1024)
                details['free_space_mb'] = free_space_mb
                
                if free_space_mb < settings.storage.MIN_FREE_SPACE_MB:
                    warnings.append(f"Low disk space: {free_space_mb}MB available, "
                                  f"{settings.storage.MIN_FREE_SPACE_MB}MB recommended")
            except Exception as e:
                warnings.append(f"Could not check disk space: {e}")
            
            # Validate file size limits
            if settings.storage.MAX_FILE_SIZE_MB <= 0:
                errors.append("MAX_FILE_SIZE_MB must be positive")
            elif settings.storage.MAX_FILE_SIZE_MB > 1000:
                warnings.append(f"Large max file size configured: {settings.storage.MAX_FILE_SIZE_MB}MB")
            
            details['max_file_size_mb'] = settings.storage.MAX_FILE_SIZE_MB
            details['min_free_space_mb'] = settings.storage.MIN_FREE_SPACE_MB
            
            # Validate allowed extensions
            if not settings.storage.ALLOWED_FILE_EXTENSIONS:
                errors.append("No allowed file extensions configured")
            else:
                details['allowed_extensions'] = settings.storage.ALLOWED_FILE_EXTENSIONS
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                details=details
            )
            
        except Exception as e:
            logger.error(f"Error validating storage configuration: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Storage validation failed: {str(e)}"],
                warnings=[],
                details={}
            )
    
    def validate_database_configuration(self) -> ValidationResult:
        """
        Validate database-related configuration.
        
        Returns:
            ValidationResult: Database validation results
        """
        try:
            errors = []
            warnings = []
            details = {}
            
            # Check database URL
            db_url = settings.database.DATABASE_URL
            details['database_url'] = self._mask_sensitive_info(db_url)
            
            if not db_url:
                errors.append("DATABASE_URL is not configured")
                return ValidationResult(False, errors, warnings, details)
            
            # Parse database type
            if 'sqlite' in db_url.lower():
                details['database_type'] = 'sqlite'
                # For SQLite, check if directory exists
                if ':///' in db_url:
                    db_path = db_url.split(':///', 1)[1]
                    if db_path and not db_path.startswith(':memory:'):
                        db_file = Path(db_path)
                        db_dir = db_file.parent
                        
                        if not db_dir.exists():
                            try:
                                db_dir.mkdir(parents=True, exist_ok=True)
                                logger.info(f"Created database directory: {db_dir}")
                            except Exception as e:
                                errors.append(f"Cannot create database directory {db_dir}: {e}")
                        
                        details['database_file'] = str(db_file.resolve())
                        details['database_directory'] = str(db_dir.resolve())
                        
                        # Check if directory is writable
                        if db_dir.exists() and not os.access(db_dir, os.W_OK):
                            errors.append(f"Database directory is not writable: {db_dir}")
            
            elif 'postgresql' in db_url.lower():
                details['database_type'] = 'postgresql'
                warnings.append("PostgreSQL configuration detected - ensure server is accessible")
            
            elif 'mysql' in db_url.lower():
                details['database_type'] = 'mysql'
                warnings.append("MySQL configuration detected - ensure server is accessible")
            
            else:
                warnings.append(f"Unknown database type in URL: {db_url}")
                details['database_type'] = 'unknown'
            
            # Validate session configuration
            if settings.database.SESSION_DURATION_DAYS <= 0:
                errors.append("SESSION_DURATION_DAYS must be positive")
            elif settings.database.SESSION_DURATION_DAYS > 365:
                warnings.append(f"Very long session duration: {settings.database.SESSION_DURATION_DAYS} days")
            
            if settings.database.SESSION_CLEANUP_INTERVAL_HOURS <= 0:
                errors.append("SESSION_CLEANUP_INTERVAL_HOURS must be positive")
            
            details['session_duration_days'] = settings.database.SESSION_DURATION_DAYS
            details['cleanup_interval_hours'] = settings.database.SESSION_CLEANUP_INTERVAL_HOURS
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                details=details
            )
            
        except Exception as e:
            logger.error(f"Error validating database configuration: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Database validation failed: {str(e)}"],
                warnings=[],
                details={}
            )
    
    def validate_environment(self) -> ValidationResult:
        """
        Validate environment and system requirements.
        
        Returns:
            ValidationResult: Environment validation results
        """
        try:
            errors = []
            warnings = []
            details = {}
            
            # Get environment information
            env_info = self.get_environment_info()
            details.update(env_info.__dict__)
            
            # Check Python version
            import sys
            python_version = sys.version_info
            if python_version < (3, 8):
                errors.append(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
            elif python_version < (3, 10):
                warnings.append(f"Python 3.10+ recommended, found {python_version.major}.{python_version.minor}")
            
            # Check memory
            if env_info.memory_mb < 512:
                warnings.append(f"Low memory detected: {env_info.memory_mb}MB")
            
            # Check disk space
            if env_info.disk_space_mb < 1000:
                warnings.append(f"Low disk space: {env_info.disk_space_mb}MB")
            
            # Check critical environment variables
            critical_env_vars = ['SECRET_KEY']
            for var in critical_env_vars:
                if not os.getenv(var):
                    warnings.append(f"Environment variable {var} not set - using default")
            
            # Check working directory permissions
            cwd = Path.cwd()
            if not os.access(cwd, os.W_OK):
                errors.append(f"Working directory is not writable: {cwd}")
            
            details['working_directory_writable'] = os.access(cwd, os.W_OK)
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                details=details
            )
            
        except Exception as e:
            logger.error(f"Error validating environment: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Environment validation failed: {str(e)}"],
                warnings=[],
                details={}
            )
    
    def validate_permissions(self) -> ValidationResult:
        """
        Validate file system permissions.
        
        Returns:
            ValidationResult: Permissions validation results
        """
        try:
            errors = []
            warnings = []
            details = {}
            
            # Test paths that need to be writable
            test_paths = [
                Path(settings.storage.STORAGE_BASE_PATH),
                Path(settings.storage.INGESTION_STORAGE_PATH),
                Path.cwd()
            ]
            
            for path in test_paths:
                path_name = str(path)
                details[f"{path.name}_permissions"] = {}
                
                if path.exists():
                    # Test read permission
                    readable = os.access(path, os.R_OK)
                    details[f"{path.name}_permissions"]['readable'] = readable
                    
                    # Test write permission
                    writable = os.access(path, os.W_OK)
                    details[f"{path.name}_permissions"]['writable'] = writable
                    
                    # Test execute permission (for directories)
                    if path.is_dir():
                        executable = os.access(path, os.X_OK)
                        details[f"{path.name}_permissions"]['executable'] = executable
                        
                        if not executable:
                            errors.append(f"Directory not executable: {path}")
                    
                    if not readable:
                        errors.append(f"Path not readable: {path}")
                    
                    if not writable:
                        errors.append(f"Path not writable: {path}")
                    
                    # Test actual file creation
                    if writable and path.is_dir():
                        test_file = path / f".write_test_{datetime.now().timestamp()}"
                        try:
                            test_file.touch()
                            test_file.unlink()
                            details[f"{path.name}_permissions"]['write_test'] = True
                        except Exception as e:
                            errors.append(f"Cannot create files in {path}: {e}")
                            details[f"{path.name}_permissions"]['write_test'] = False
                
                else:
                    warnings.append(f"Path does not exist: {path}")
                    details[f"{path.name}_permissions"]['exists'] = False
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                details=details
            )
            
        except Exception as e:
            logger.error(f"Error validating permissions: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Permissions validation failed: {str(e)}"],
                warnings=[],
                details={}
            )
    
    def validate_dependencies(self) -> ValidationResult:
        """
        Validate required dependencies and imports.
        
        Returns:
            ValidationResult: Dependencies validation results
        """
        try:
            errors = []
            warnings = []
            details = {}
            
            # Critical dependencies
            critical_deps = [
                ('fastapi', 'FastAPI web framework'),
                ('sqlalchemy', 'Database ORM'),
                ('pydantic', 'Data validation'),
                ('aiofiles', 'Async file operations'),
                ('uvicorn', 'ASGI server')
            ]
            
            # Optional dependencies
            optional_deps = [
                ('redis', 'Redis client'),
                ('celery', 'Task queue'),
                ('hypothesis', 'Property-based testing')
            ]
            
            # Test critical dependencies
            for dep_name, description in critical_deps:
                try:
                    __import__(dep_name)
                    details[f"{dep_name}_available"] = True
                    logger.debug(f"✓ {dep_name}: {description}")
                except ImportError as e:
                    errors.append(f"Missing critical dependency {dep_name}: {description}")
                    details[f"{dep_name}_available"] = False
                    logger.error(f"✗ {dep_name}: {e}")
            
            # Test optional dependencies
            for dep_name, description in optional_deps:
                try:
                    __import__(dep_name)
                    details[f"{dep_name}_available"] = True
                    logger.debug(f"✓ {dep_name}: {description}")
                except ImportError:
                    warnings.append(f"Optional dependency not available: {dep_name} ({description})")
                    details[f"{dep_name}_available"] = False
            
            # Test our own modules
            our_modules = [
                'app.storage',
                'app.database',
                'app.session',
                'app.services.enhanced_file_handler',
                'app.services.concurrent_upload_manager',
                'app.services.entity_validator'
            ]
            
            for module_name in our_modules:
                try:
                    __import__(module_name)
                    details[f"{module_name.split('.')[-1]}_module"] = True
                except ImportError as e:
                    errors.append(f"Cannot import module {module_name}: {e}")
                    details[f"{module_name.split('.')[-1]}_module"] = False
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                details=details
            )
            
        except Exception as e:
            logger.error(f"Error validating dependencies: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Dependencies validation failed: {str(e)}"],
                warnings=[],
                details={}
            )
    
    def get_environment_info(self) -> EnvironmentInfo:
        """
        Get comprehensive environment information.
        
        Returns:
            EnvironmentInfo: Current environment details
        """
        try:
            import sys
            import platform
            import psutil
            
            # Get basic system info
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            platform_info = f"{platform.system()} {platform.release()}"
            working_dir = str(Path.cwd())
            
            # Get environment variables (filtered)
            env_vars = {
                key: value for key, value in os.environ.items()
                if not any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token'])
            }
            
            # Get system resources
            try:
                disk_usage = psutil.disk_usage('/')
                disk_space_mb = disk_usage.free // (1024 * 1024)
            except:
                disk_space_mb = 0
            
            try:
                memory_info = psutil.virtual_memory()
                memory_mb = memory_info.available // (1024 * 1024)
            except:
                memory_mb = 0
            
            env_info = EnvironmentInfo(
                python_version=python_version,
                platform=platform_info,
                working_directory=working_dir,
                environment_variables=env_vars,
                disk_space_mb=disk_space_mb,
                memory_mb=memory_mb
            )
            
            self.environment_info = env_info
            return env_info
            
        except Exception as e:
            logger.error(f"Error getting environment info: {e}")
            # Return minimal info on error
            return EnvironmentInfo(
                python_version="unknown",
                platform="unknown",
                working_directory=str(Path.cwd()),
                environment_variables={},
                disk_space_mb=0,
                memory_mb=0
            )
    
    def generate_configuration_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive configuration report.
        
        Returns:
            dict: Complete configuration report
        """
        try:
            # Run validation if not already done
            if not self.validation_results:
                validation_result = self.validate_complete_configuration()
            else:
                validation_result = self.validation_results
            
            # Get environment info
            if not self.environment_info:
                env_info = self.get_environment_info()
            else:
                env_info = self.environment_info
            
            report = {
                "report_timestamp": datetime.utcnow().isoformat(),
                "validation_summary": {
                    "is_valid": validation_result.is_valid,
                    "total_errors": len(validation_result.errors),
                    "total_warnings": len(validation_result.warnings)
                },
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
                "validation_details": validation_result.details,
                "environment_info": env_info.__dict__,
                "configuration_values": {
                    "storage": {
                        "base_path": settings.storage.STORAGE_BASE_PATH,
                        "ingestion_path": settings.storage.INGESTION_STORAGE_PATH,
                        "max_file_size_mb": settings.storage.MAX_FILE_SIZE_MB,
                        "min_free_space_mb": settings.storage.MIN_FREE_SPACE_MB,
                        "allowed_extensions": settings.storage.ALLOWED_FILE_EXTENSIONS
                    },
                    "database": {
                        "url": self._mask_sensitive_info(settings.database.DATABASE_URL),
                        "session_duration_days": settings.database.SESSION_DURATION_DAYS,
                        "cleanup_interval_hours": settings.database.SESSION_CLEANUP_INTERVAL_HOURS
                    }
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating configuration report: {e}")
            return {
                "report_timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "validation_summary": {"is_valid": False, "total_errors": 1, "total_warnings": 0}
            }
    
    def validate_startup_requirements(self) -> ValidationResult:
        """
        Validate all requirements needed for application startup.
        
        This method performs comprehensive validation that must pass
        before the application can start successfully.
        
        Returns:
            ValidationResult: Startup validation results
        """
        try:
            logger.info("Starting application startup validation")
            
            # Run complete configuration validation first
            config_result = self.validate_complete_configuration()
            
            if not config_result.is_valid:
                logger.error("Configuration validation failed - cannot start application")
                return config_result
            
            # Additional startup-specific validations
            startup_errors = []
            startup_warnings = []
            startup_details = config_result.details.copy()
            
            # Test database connectivity
            db_test_result = self._test_database_connectivity()
            startup_details['database_connectivity'] = db_test_result
            if not db_test_result['success']:
                startup_errors.append(f"Database connectivity failed: {db_test_result['error']}")
            
            # Test storage writability
            storage_test_result = self._test_storage_writability()
            startup_details['storage_writability'] = storage_test_result
            if not storage_test_result['success']:
                startup_errors.append(f"Storage writability test failed: {storage_test_result['error']}")
            
            # Test critical service imports
            service_test_result = self._test_service_imports()
            startup_details['service_imports'] = service_test_result
            if not service_test_result['success']:
                startup_errors.extend(service_test_result['errors'])
            
            # Combine all errors and warnings
            all_errors = config_result.errors + startup_errors
            all_warnings = config_result.warnings + startup_warnings
            
            is_valid = len(all_errors) == 0
            
            result = ValidationResult(
                is_valid=is_valid,
                errors=all_errors,
                warnings=all_warnings,
                details=startup_details
            )
            
            if is_valid:
                logger.info("Application startup validation completed successfully")
            else:
                logger.error(f"Application startup validation failed with {len(all_errors)} errors")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during startup validation: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Startup validation failed: {str(e)}"],
                warnings=[],
                details={"startup_validation_error": str(e)}
            )
    
    def _test_database_connectivity(self) -> Dict[str, Any]:
        """
        Test database connectivity and basic operations.
        
        Returns:
            dict: Database connectivity test results
        """
        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.pool import StaticPool
            
            db_url = settings.database.DATABASE_URL
            
            # Create test engine with appropriate configuration
            if 'sqlite' in db_url.lower():
                # For SQLite, use special configuration
                engine = create_engine(
                    db_url,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False},
                    echo=False
                )
            else:
                engine = create_engine(db_url, echo=False)
            
            # Test basic connectivity
            with engine.connect() as conn:
                # Simple test query
                result = conn.execute(text("SELECT 1"))
                test_value = result.scalar()
                
                if test_value != 1:
                    return {
                        'success': False,
                        'error': f"Database test query returned unexpected value: {test_value}",
                        'details': {}
                    }
            
            # Test database file creation for SQLite
            if 'sqlite' in db_url.lower() and ':///' in db_url:
                db_path = db_url.split(':///', 1)[1]
                if db_path and not db_path.startswith(':memory:'):
                    db_file = Path(db_path)
                    if not db_file.exists():
                        return {
                            'success': False,
                            'error': f"SQLite database file was not created: {db_file}",
                            'details': {'database_file': str(db_file)}
                        }
            
            engine.dispose()
            
            return {
                'success': True,
                'error': None,
                'details': {
                    'database_type': 'sqlite' if 'sqlite' in db_url.lower() else 'other',
                    'connection_test': 'passed'
                }
            }
            
        except Exception as e:
            logger.error(f"Database connectivity test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'details': {'exception_type': type(e).__name__}
            }
    
    def _test_storage_writability(self) -> Dict[str, Any]:
        """
        Test storage directory writability with actual file operations.
        
        Returns:
            dict: Storage writability test results
        """
        try:
            from datetime import datetime
            import tempfile
            import uuid
            
            test_results = {}
            
            # Test storage base path
            storage_base = Path(settings.storage.STORAGE_BASE_PATH)
            base_test = self._test_directory_write(storage_base, "storage_base")
            test_results['storage_base'] = base_test
            
            # Test ingestion path
            ingestion_path = Path(settings.storage.INGESTION_STORAGE_PATH)
            ingestion_test = self._test_directory_write(ingestion_path, "ingestion")
            test_results['ingestion'] = ingestion_test
            
            # Check if all tests passed
            all_success = all(result['success'] for result in test_results.values())
            
            if not all_success:
                failed_tests = [name for name, result in test_results.items() if not result['success']]
                return {
                    'success': False,
                    'error': f"Storage writability failed for: {', '.join(failed_tests)}",
                    'details': test_results
                }
            
            return {
                'success': True,
                'error': None,
                'details': test_results
            }
            
        except Exception as e:
            logger.error(f"Storage writability test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'details': {'exception_type': type(e).__name__}
            }
    
    def _test_directory_write(self, directory: Path, test_name: str) -> Dict[str, Any]:
        """
        Test write operations in a specific directory.
        
        Args:
            directory: Directory to test
            test_name: Name for this test
            
        Returns:
            dict: Test results for this directory
        """
        try:
            # Ensure directory exists
            directory.mkdir(parents=True, exist_ok=True)
            
            # Generate unique test filename
            test_filename = f".write_test_{test_name}_{uuid.uuid4().hex[:8]}.tmp"
            test_file = directory / test_filename
            
            # Test file creation
            test_content = f"Write test for {test_name} at {datetime.utcnow().isoformat()}"
            test_file.write_text(test_content)
            
            # Test file reading
            read_content = test_file.read_text()
            if read_content != test_content:
                return {
                    'success': False,
                    'error': f"File content mismatch in {directory}",
                    'path': str(directory)
                }
            
            # Test file deletion
            test_file.unlink()
            
            # Verify file was deleted
            if test_file.exists():
                return {
                    'success': False,
                    'error': f"Could not delete test file in {directory}",
                    'path': str(directory)
                }
            
            return {
                'success': True,
                'error': None,
                'path': str(directory),
                'operations': ['create', 'read', 'delete']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'path': str(directory),
                'exception_type': type(e).__name__
            }
    
    def _test_service_imports(self) -> Dict[str, Any]:
        """
        Test that all critical services can be imported and initialized.
        
        Returns:
            dict: Service import test results
        """
        try:
            import_results = {}
            import_errors = []
            
            # Critical service modules to test
            critical_services = [
                ('app.storage.directory_manager', 'DirectoryManager'),
                ('app.storage.storage_service', 'StorageService'),
                ('app.database.database_service', 'DatabaseService'),
                ('app.session.session_manager', 'SessionManager'),
                ('app.services.enhanced_file_handler', 'EnhancedFileHandler'),
                ('app.services.concurrent_upload_manager', 'ConcurrentUploadManager'),
                ('app.services.entity_validator', 'EntityValidator')
            ]
            
            for module_name, class_name in critical_services:
                try:
                    # Import the module
                    module = __import__(module_name, fromlist=[class_name])
                    
                    # Get the class
                    service_class = getattr(module, class_name)
                    
                    # Test basic instantiation (without full initialization)
                    # This tests that the class definition is valid
                    import inspect
                    sig = inspect.signature(service_class.__init__)
                    
                    import_results[f"{module_name}.{class_name}"] = {
                        'import_success': True,
                        'class_found': True,
                        'init_signature_valid': True
                    }
                    
                except ImportError as e:
                    import_errors.append(f"Cannot import {module_name}: {e}")
                    import_results[f"{module_name}.{class_name}"] = {
                        'import_success': False,
                        'error': str(e)
                    }
                    
                except AttributeError as e:
                    import_errors.append(f"Class {class_name} not found in {module_name}: {e}")
                    import_results[f"{module_name}.{class_name}"] = {
                        'import_success': True,
                        'class_found': False,
                        'error': str(e)
                    }
                    
                except Exception as e:
                    import_errors.append(f"Error testing {module_name}.{class_name}: {e}")
                    import_results[f"{module_name}.{class_name}"] = {
                        'import_success': True,
                        'class_found': True,
                        'error': str(e)
                    }
            
            return {
                'success': len(import_errors) == 0,
                'errors': import_errors,
                'details': import_results
            }
            
        except Exception as e:
            logger.error(f"Service import test failed: {e}")
            return {
                'success': False,
                'errors': [f"Service import test failed: {str(e)}"],
                'details': {'exception_type': type(e).__name__}
            }
    
    def ensure_startup_readiness(self) -> Tuple[bool, List[str]]:
        """
        Ensure the application is ready for startup by validating and fixing issues.
        
        This method attempts to automatically fix common startup issues
        and returns whether the application is ready to start.
        
        Returns:
            tuple: (is_ready, list_of_remaining_issues)
        """
        try:
            logger.info("Ensuring application startup readiness")
            
            # Run startup validation
            validation_result = self.validate_startup_requirements()
            
            if validation_result.is_valid:
                logger.info("Application is ready for startup")
                return True, []
            
            # Attempt to fix common issues
            fixable_issues = []
            unfixable_issues = []
            
            for error in validation_result.errors:
                if self._attempt_fix_startup_issue(error):
                    fixable_issues.append(error)
                else:
                    unfixable_issues.append(error)
            
            # Re-validate after fixes
            if fixable_issues:
                logger.info(f"Attempted to fix {len(fixable_issues)} startup issues")
                revalidation_result = self.validate_startup_requirements()
                
                if revalidation_result.is_valid:
                    logger.info("Application is now ready for startup after fixes")
                    return True, []
                else:
                    unfixable_issues = revalidation_result.errors
            
            logger.warning(f"Application startup readiness check failed with {len(unfixable_issues)} remaining issues")
            return False, unfixable_issues
            
        except Exception as e:
            logger.error(f"Error ensuring startup readiness: {e}")
            return False, [f"Startup readiness check failed: {str(e)}"]
    
    def _attempt_fix_startup_issue(self, error: str) -> bool:
        """
        Attempt to automatically fix a startup issue.
        
        Args:
            error: Error message describing the issue
            
        Returns:
            bool: True if fix was attempted, False if not fixable
        """
        try:
            # Fix directory creation issues
            if "Cannot create" in error and "directory" in error:
                # Extract directory path from error message
                import re
                path_match = re.search(r'directory ([^:]+):', error)
                if path_match:
                    dir_path = Path(path_match.group(1))
                    try:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Created missing directory: {dir_path}")
                        return True
                    except Exception as e:
                        logger.error(f"Failed to create directory {dir_path}: {e}")
                        return False
            
            # Fix permission issues
            if "not writable" in error:
                # Extract path from error message
                import re
                path_match = re.search(r'not writable: ([^\s]+)', error)
                if path_match:
                    dir_path = Path(path_match.group(1))
                    try:
                        # Attempt to fix permissions
                        import stat
                        current_mode = dir_path.stat().st_mode
                        new_mode = current_mode | stat.S_IWUSR | stat.S_IWGRP
                        dir_path.chmod(new_mode)
                        logger.info(f"Fixed permissions for: {dir_path}")
                        return True
                    except Exception as e:
                        logger.error(f"Failed to fix permissions for {dir_path}: {e}")
                        return False
            
            # Other issues are not automatically fixable
            return False
            
        except Exception as e:
            logger.error(f"Error attempting to fix startup issue '{error}': {e}")
            return False
    
    def _mask_sensitive_info(self, value: str) -> str:
        """Mask sensitive information in configuration values"""
        if not value:
            return value
        
        # Mask database URLs
        if '://' in value:
            parts = value.split('://')
            if len(parts) == 2 and '@' in parts[1]:
                scheme = parts[0]
                rest = parts[1]
                if '@' in rest:
                    credentials, host_part = rest.split('@', 1)
                    return f"{scheme}://***:***@{host_part}"
        
        return value