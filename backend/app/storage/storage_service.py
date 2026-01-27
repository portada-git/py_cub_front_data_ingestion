"""
Storage Service for atomic file operations and storage management
"""

import os
import uuid
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Optional, Union, BinaryIO, Dict, Any
from datetime import datetime

from .directory_manager import DirectoryManager
from ..core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    Handles file storage operations with atomic writes, UUID generation,
    and storage validation. Ensures reliable file operations that prevent
    corruption and handle concurrent access safely.
    """
    
    def __init__(self, storage_path: Optional[Union[str, Path]] = None):
        """
        Initialize the StorageService with storage configuration.
        
        Args:
            storage_path: Base storage path. Defaults to settings.storage.INGESTION_STORAGE_PATH
        """
        self.storage_path = Path(storage_path or settings.storage.INGESTION_STORAGE_PATH).resolve()
        self.directory_manager = DirectoryManager()
        self.max_file_size_bytes = settings.storage.MAX_FILE_SIZE_MB * 1024 * 1024
        self.min_free_space_bytes = settings.storage.MIN_FREE_SPACE_MB * 1024 * 1024
        
        # Ensure storage directory exists
        self.directory_manager.ensure_directory_exists(self.storage_path)
        
        logger.info(f"StorageService initialized with path: {self.storage_path}")
    
    def save_file(self, file_content: bytes, original_filename: str, 
                  custom_uuid: Optional[str] = None) -> Dict[str, Any]:
        """
        Save file content with atomic operations and UUID filename generation.
        
        Args:
            file_content: Binary content of the file to save
            original_filename: Original filename for metadata
            custom_uuid: Optional custom UUID (for testing), generates new if None
            
        Returns:
            dict: Result containing success status, file_id, file_path, and metadata
            
        Raises:
            ValueError: If file validation fails
            OSError: If storage operations fail
        """
        try:
            # Validate file content
            self._validate_file_content(file_content, original_filename)
            
            # Check available disk space
            if not self._check_disk_space(len(file_content)):
                raise OSError("Insufficient disk space for file upload")
            
            # Generate unique filename
            file_id = custom_uuid or str(uuid.uuid4())
            file_extension = Path(original_filename).suffix
            stored_filename = f"{file_id}{file_extension}"
            final_path = self.storage_path / stored_filename
            
            # Ensure uniqueness (handle UUID collisions)
            while final_path.exists():
                file_id = str(uuid.uuid4())
                stored_filename = f"{file_id}{file_extension}"
                final_path = self.storage_path / stored_filename
                logger.warning(f"UUID collision detected, generated new UUID: {file_id}")
            
            # Perform atomic write
            temp_path = self._atomic_write(file_content, final_path)
            
            # Verify file was written correctly
            if not self._verify_file_integrity(final_path, file_content):
                self._cleanup_file(final_path)
                raise OSError("File integrity verification failed")
            
            # Prepare result metadata
            result = {
                'success': True,
                'file_id': file_id,
                'stored_filename': stored_filename,
                'file_path': str(final_path),
                'original_filename': original_filename,
                'file_size': len(file_content),
                'upload_timestamp': datetime.utcnow().isoformat(),
                'storage_path': str(self.storage_path)
            }
            
            logger.info(f"Successfully saved file: {stored_filename} (original: {original_filename})")
            return result
            
        except Exception as e:
            logger.error(f"Error saving file {original_filename}: {e}")
            raise
    
    def get_file_path(self, file_id: str, file_extension: str = ".json") -> Path:
        """
        Get the full path for a file by its ID.
        
        Args:
            file_id: UUID of the file
            file_extension: File extension (defaults to .json)
            
        Returns:
            Path: Full path to the file
        """
        filename = f"{file_id}{file_extension}"
        return self.storage_path / filename
    
    def file_exists(self, file_id: str, file_extension: str = ".json") -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            file_id: UUID of the file
            file_extension: File extension (defaults to .json)
            
        Returns:
            bool: True if file exists, False otherwise
        """
        file_path = self.get_file_path(file_id, file_extension)
        return file_path.exists() and file_path.is_file()
    
    def read_file(self, file_id: str, file_extension: str = ".json") -> bytes:
        """
        Read file content by file ID.
        
        Args:
            file_id: UUID of the file
            file_extension: File extension (defaults to .json)
            
        Returns:
            bytes: File content
            
        Raises:
            FileNotFoundError: If file doesn't exist
            OSError: If file read fails
        """
        file_path = self.get_file_path(file_id, file_extension)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_id}{file_extension}")
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            logger.debug(f"Successfully read file: {file_id}{file_extension}")
            return content
            
        except Exception as e:
            logger.error(f"Error reading file {file_id}{file_extension}: {e}")
            raise OSError(f"Failed to read file: {e}")
    
    def delete_file(self, file_id: str, file_extension: str = ".json") -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_id: UUID of the file
            file_extension: File extension (defaults to .json)
            
        Returns:
            bool: True if file was deleted, False if file didn't exist
            
        Raises:
            OSError: If deletion fails
        """
        file_path = self.get_file_path(file_id, file_extension)
        
        if not file_path.exists():
            logger.debug(f"File not found for deletion: {file_id}{file_extension}")
            return False
        
        try:
            file_path.unlink()
            logger.info(f"Successfully deleted file: {file_id}{file_extension}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_id}{file_extension}: {e}")
            raise OSError(f"Failed to delete file: {e}")
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about the storage system.
        
        Returns:
            dict: Storage information including path, space, and file count
        """
        try:
            dir_info = self.directory_manager.get_directory_info(self.storage_path)
            
            # Count files in storage
            file_count = 0
            total_size = 0
            
            if self.storage_path.exists():
                for file_path in self.storage_path.iterdir():
                    if file_path.is_file():
                        file_count += 1
                        total_size += file_path.stat().st_size
            
            return {
                'storage_path': str(self.storage_path),
                'exists': dir_info['exists'],
                'writable': dir_info['writable'],
                'free_space_mb': dir_info['free_space_mb'],
                'file_count': file_count,
                'total_size_mb': total_size // (1024 * 1024),
                'max_file_size_mb': settings.storage.MAX_FILE_SIZE_MB,
                'min_free_space_mb': settings.storage.MIN_FREE_SPACE_MB
            }
            
        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
            return {
                'storage_path': str(self.storage_path),
                'exists': False,
                'writable': False,
                'error': str(e)
            }
    
    def cleanup_temp_files(self, max_age_hours: Optional[int] = None) -> int:
        """
        Clean up temporary files older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours (defaults to settings value)
            
        Returns:
            int: Number of files cleaned up
        """
        max_age_hours = max_age_hours or settings.storage.CLEANUP_TEMP_FILES_HOURS
        max_age_seconds = max_age_hours * 3600
        current_time = datetime.utcnow().timestamp()
        
        cleaned_count = 0
        
        try:
            if not self.storage_path.exists():
                return 0
            
            for file_path in self.storage_path.iterdir():
                if not file_path.is_file():
                    continue
                
                # Check if file is a temporary file (starts with tmp or has .tmp extension)
                if (file_path.name.startswith('tmp') or 
                    file_path.suffix == '.tmp' or
                    file_path.name.startswith('.')):
                    
                    try:
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > max_age_seconds:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.debug(f"Cleaned up temp file: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"Could not clean up temp file {file_path.name}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} temporary files")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")
            return cleaned_count
    
    def _validate_file_content(self, content: bytes, filename: str) -> None:
        """
        Validate file content before saving.
        
        Args:
            content: File content to validate
            filename: Original filename for validation
            
        Raises:
            ValueError: If validation fails
        """
        if not content:
            raise ValueError("File content is empty")
        
        if len(content) > self.max_file_size_bytes:
            raise ValueError(f"File size ({len(content)} bytes) exceeds maximum allowed "
                           f"({self.max_file_size_bytes} bytes)")
        
        # Validate file extension
        file_extension = Path(filename).suffix.lower()
        allowed_extensions = [ext.lower() for ext in settings.storage.ALLOWED_FILE_EXTENSIONS]
        
        if file_extension not in allowed_extensions:
            raise ValueError(f"File extension '{file_extension}' not allowed. "
                           f"Allowed extensions: {allowed_extensions}")
    
    def _check_disk_space(self, required_bytes: int) -> bool:
        """
        Check if there's enough disk space for the file.
        
        Args:
            required_bytes: Number of bytes required
            
        Returns:
            bool: True if enough space available, False otherwise
        """
        try:
            statvfs = os.statvfs(self.storage_path)
            free_bytes = statvfs.f_frsize * statvfs.f_bavail
            
            # Ensure we have minimum free space plus file size
            required_total = required_bytes + self.min_free_space_bytes
            
            return free_bytes >= required_total
            
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            return False
    
    def _atomic_write(self, content: bytes, target_path: Path) -> Path:
        """
        Perform atomic write operation using temporary file.
        
        Args:
            content: Content to write
            target_path: Final path for the file
            
        Returns:
            Path: Path to the temporary file used
            
        Raises:
            OSError: If write operation fails
        """
        temp_path = None
        try:
            # Create temporary file in the same directory as target
            temp_fd, temp_path_str = tempfile.mkstemp(
                dir=target_path.parent,
                prefix=f"tmp_{target_path.stem}_",
                suffix=target_path.suffix
            )
            temp_path = Path(temp_path_str)
            
            # Write content to temporary file
            with os.fdopen(temp_fd, 'wb') as temp_file:
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())  # Ensure data is written to disk
            
            # Atomic move to final location
            shutil.move(str(temp_path), str(target_path))
            
            logger.debug(f"Atomic write completed: {target_path}")
            return temp_path
            
        except Exception as e:
            # Clean up temporary file if it exists
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            
            logger.error(f"Atomic write failed for {target_path}: {e}")
            raise OSError(f"Failed to write file atomically: {e}")
    
    def _verify_file_integrity(self, file_path: Path, expected_content: bytes) -> bool:
        """
        Verify that the written file matches expected content.
        
        Args:
            file_path: Path to the file to verify
            expected_content: Expected file content
            
        Returns:
            bool: True if file matches expected content, False otherwise
        """
        try:
            if not file_path.exists():
                logger.error(f"File does not exist after write: {file_path}")
                return False
            
            actual_size = file_path.stat().st_size
            expected_size = len(expected_content)
            
            if actual_size != expected_size:
                logger.error(f"File size mismatch: expected {expected_size}, got {actual_size}")
                return False
            
            # For small files, verify content matches
            if expected_size < 1024 * 1024:  # 1MB threshold
                with open(file_path, 'rb') as f:
                    actual_content = f.read()
                
                if actual_content != expected_content:
                    logger.error("File content does not match expected content")
                    return False
            
            logger.debug(f"File integrity verified: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying file integrity {file_path}: {e}")
            return False
    
    def _cleanup_file(self, file_path: Path) -> None:
        """
        Clean up a file, ignoring errors.
        
        Args:
            file_path: Path to the file to clean up
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not clean up file {file_path}: {e}")