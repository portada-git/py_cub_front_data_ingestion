"""
Directory Manager for automatic directory creation and validation
"""

import os
import stat
import logging
from pathlib import Path
from typing import Optional, Union
from ..core.config import settings

logger = logging.getLogger(__name__)


class DirectoryManager:
    """
    Manages directory creation, validation, and permissions for the storage system.
    
    This class ensures that all required directories exist with proper permissions
    before file operations are attempted, preventing the "No such file or directory"
    errors that were occurring in the upload system.
    """
    
    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """
        Initialize the DirectoryManager with a base storage path.
        
        Args:
            base_path: Base directory path for storage operations.
                      Defaults to settings.storage.STORAGE_BASE_PATH
        """
        self.base_path = Path(base_path or settings.storage.STORAGE_BASE_PATH).resolve()
        self.permissions = settings.storage.STORAGE_PERMISSIONS
        logger.info(f"DirectoryManager initialized with base path: {self.base_path}")
    
    def ensure_directory_exists(self, path: Union[str, Path]) -> bool:
        """
        Ensure that a directory exists, creating it if necessary.
        
        Args:
            path: Directory path to ensure exists (can be relative to base_path or absolute)
            
        Returns:
            bool: True if directory exists or was created successfully, False otherwise
            
        Raises:
            ValueError: If path validation fails
            PermissionError: If directory creation fails due to permissions
        """
        try:
            # Convert to Path object and resolve
            dir_path = Path(path)
            
            # If path is relative, make it relative to base_path
            if not dir_path.is_absolute():
                dir_path = self.base_path / dir_path
            
            dir_path = dir_path.resolve()
            
            # Validate path security
            if not self._validate_path_security(dir_path):
                raise ValueError(f"Path validation failed for: {dir_path}")
            
            # Check if directory already exists
            if dir_path.exists():
                if not dir_path.is_dir():
                    raise ValueError(f"Path exists but is not a directory: {dir_path}")
                
                # Verify permissions
                if not self._check_directory_permissions(dir_path):
                    logger.warning(f"Directory permissions incorrect for: {dir_path}")
                    self._fix_directory_permissions(dir_path)
                
                logger.debug(f"Directory already exists: {dir_path}")
                return True
            
            # Create directory with parents
            dir_path.mkdir(parents=True, exist_ok=True, mode=self.permissions)
            
            # Verify creation and permissions
            if not dir_path.exists():
                logger.error(f"Failed to create directory: {dir_path}")
                return False
            
            # Set permissions explicitly (mkdir mode can be affected by umask)
            self._fix_directory_permissions(dir_path)
            
            logger.info(f"Successfully created directory: {dir_path}")
            return True
            
        except PermissionError as e:
            logger.error(f"Permission denied creating directory {path}: {e}")
            raise PermissionError(f"Cannot create directory {path}: insufficient permissions")
        
        except OSError as e:
            logger.error(f"OS error creating directory {path}: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error creating directory {path}: {e}")
            return False
    
    def validate_directory_writable(self, path: Union[str, Path]) -> bool:
        """
        Validate that a directory is writable by the current process.
        
        Args:
            path: Directory path to validate
            
        Returns:
            bool: True if directory is writable, False otherwise
        """
        try:
            dir_path = Path(path)
            if not dir_path.is_absolute():
                dir_path = self.base_path / dir_path
            
            dir_path = dir_path.resolve()
            
            if not dir_path.exists():
                logger.warning(f"Directory does not exist for writability check: {dir_path}")
                return False
            
            if not dir_path.is_dir():
                logger.error(f"Path is not a directory: {dir_path}")
                return False
            
            # Test writability by creating a temporary file
            test_file = dir_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
                logger.debug(f"Directory is writable: {dir_path}")
                return True
            except (PermissionError, OSError) as e:
                logger.error(f"Directory is not writable {dir_path}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking directory writability {path}: {e}")
            return False
    
    def get_directory_info(self, path: Union[str, Path]) -> dict:
        """
        Get information about a directory including permissions and space.
        
        Args:
            path: Directory path to analyze
            
        Returns:
            dict: Directory information including exists, writable, permissions, free_space_mb
        """
        try:
            dir_path = Path(path)
            if not dir_path.is_absolute():
                dir_path = self.base_path / dir_path
            
            dir_path = dir_path.resolve()
            
            info = {
                'path': str(dir_path),
                'exists': dir_path.exists(),
                'is_directory': dir_path.is_dir() if dir_path.exists() else False,
                'writable': False,
                'permissions': None,
                'free_space_mb': 0
            }
            
            if dir_path.exists() and dir_path.is_dir():
                info['writable'] = self.validate_directory_writable(dir_path)
                info['permissions'] = oct(dir_path.stat().st_mode)[-3:]
                
                # Get free space
                statvfs = os.statvfs(dir_path)
                free_space_bytes = statvfs.f_frsize * statvfs.f_bavail
                info['free_space_mb'] = free_space_bytes // (1024 * 1024)
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting directory info for {path}: {e}")
            return {
                'path': str(path),
                'exists': False,
                'is_directory': False,
                'writable': False,
                'permissions': None,
                'free_space_mb': 0,
                'error': str(e)
            }
    
    def cleanup_empty_directories(self, path: Union[str, Path], max_depth: int = 3) -> int:
        """
        Clean up empty directories within the specified path.
        
        Args:
            path: Base path to clean up
            max_depth: Maximum depth to traverse for cleanup
            
        Returns:
            int: Number of directories removed
        """
        removed_count = 0
        try:
            dir_path = Path(path)
            if not dir_path.is_absolute():
                dir_path = self.base_path / dir_path
            
            dir_path = dir_path.resolve()
            
            if not dir_path.exists() or not dir_path.is_dir():
                return 0
            
            # Recursively remove empty directories
            for root, dirs, files in os.walk(dir_path, topdown=False):
                current_path = Path(root)
                
                # Skip if we've exceeded max depth
                try:
                    current_path.relative_to(dir_path)
                    depth = len(current_path.relative_to(dir_path).parts)
                    if depth > max_depth:
                        continue
                except ValueError:
                    continue
                
                # Don't remove the base directory
                if current_path == dir_path:
                    continue
                
                # Remove if empty
                try:
                    if not files and not dirs:
                        current_path.rmdir()
                        removed_count += 1
                        logger.debug(f"Removed empty directory: {current_path}")
                except OSError as e:
                    logger.debug(f"Could not remove directory {current_path}: {e}")
            
            logger.info(f"Cleaned up {removed_count} empty directories in {dir_path}")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error during directory cleanup {path}: {e}")
            return removed_count
    
    def _validate_path_security(self, path: Path) -> bool:
        """
        Validate that a path is secure and within allowed boundaries.
        
        Args:
            path: Path to validate
            
        Returns:
            bool: True if path is secure, False otherwise
        """
        try:
            # Ensure path is within base_path or is the base_path itself
            try:
                path.relative_to(self.base_path)
                return True
            except ValueError:
                # Path is not within base_path, check if it's the base_path itself
                if path == self.base_path:
                    return True
                
                logger.warning(f"Path outside of allowed base path: {path}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating path security {path}: {e}")
            return False
    
    def _check_directory_permissions(self, path: Path) -> bool:
        """
        Check if directory has correct permissions.
        
        Args:
            path: Directory path to check
            
        Returns:
            bool: True if permissions are correct, False otherwise
        """
        try:
            current_mode = path.stat().st_mode
            expected_mode = self.permissions
            
            # Compare permission bits (ignore file type bits)
            current_perms = stat.S_IMODE(current_mode)
            return current_perms == expected_mode
            
        except Exception as e:
            logger.error(f"Error checking directory permissions {path}: {e}")
            return False
    
    def _fix_directory_permissions(self, path: Path) -> bool:
        """
        Fix directory permissions to match expected permissions.
        
        Args:
            path: Directory path to fix
            
        Returns:
            bool: True if permissions were fixed, False otherwise
        """
        try:
            path.chmod(self.permissions)
            logger.debug(f"Fixed permissions for directory: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error fixing directory permissions {path}: {e}")
            return False