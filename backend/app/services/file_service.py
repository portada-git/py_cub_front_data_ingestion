"""
File handling service for the PortAda application
"""

import os
import json
import yaml
import aiofiles
import hashlib
import mimetypes
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import (
    PortAdaFileError, PortAdaValidationError, 
    wrap_portada_error
)
from app.models.ingestion import FileFormat, FileValidation

logger = logging.getLogger(__name__)


class FileService:
    """Service for handling file operations"""
    
    def __init__(self):
        self.upload_folder = settings.INGESTION_FOLDER
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_extensions = {
            FileFormat.JSON: ['.json'],
            FileFormat.YAML: ['.yaml', '.yml'],
            FileFormat.YML: ['.yml', '.yaml']
        }
        self.cleanup_interval_hours = 24  # Clean up files older than 24 hours
        
        # Ensure upload folder exists
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename"""
        return Path(filename).suffix.lower()
    
    def _detect_file_format(self, filename: str) -> Optional[FileFormat]:
        """
        Detect file format from filename extension
        
        Args:
            filename: Name of the file
            
        Returns:
            Detected file format or None if not supported
        """
        extension = self._get_file_extension(filename)
        
        for file_format, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return file_format
        
        return None
    
    def _calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    async def validate_file(
        self, 
        file: UploadFile, 
        expected_format: Optional[FileFormat] = None
    ) -> FileValidation:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file object
            expected_format: Expected file format (optional)
            
        Returns:
            File validation results
        """
        try:
            validation_errors = []
            
            # Read file content
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            file_size = len(content)
            
            # Check file size
            if file_size > self.max_file_size:
                validation_errors.append(
                    f"File size {file_size} bytes exceeds maximum allowed size of {self.max_file_size} bytes"
                )
            
            if file_size == 0:
                validation_errors.append("File is empty")
            
            # Detect file format
            detected_format = self._detect_file_format(file.filename)
            if not detected_format:
                validation_errors.append(f"Unsupported file format: {self._get_file_extension(file.filename)}")
                return FileValidation(
                    is_valid=False,
                    file_size=file_size,
                    file_format=FileFormat.JSON,  # Default
                    validation_errors=validation_errors
                )
            
            # Check expected format
            if expected_format and detected_format != expected_format:
                validation_errors.append(
                    f"Expected {expected_format.value} format, but got {detected_format.value}"
                )
            
            # Validate file content based on format
            record_count = None
            try:
                if detected_format == FileFormat.JSON:
                    data = json.loads(content.decode('utf-8'))
                    record_count = self._count_json_records(data)
                elif detected_format in [FileFormat.YAML, FileFormat.YML]:
                    data = yaml.safe_load(content.decode('utf-8'))
                    record_count = self._count_yaml_records(data)
            except json.JSONDecodeError as e:
                validation_errors.append(f"Invalid JSON format: {str(e)}")
            except yaml.YAMLError as e:
                validation_errors.append(f"Invalid YAML format: {str(e)}")
            except UnicodeDecodeError as e:
                validation_errors.append(f"File encoding error: {str(e)}")
            except Exception as e:
                validation_errors.append(f"Content validation error: {str(e)}")
            
            return FileValidation(
                is_valid=len(validation_errors) == 0,
                file_size=file_size,
                file_format=detected_format,
                record_count=record_count,
                validation_errors=validation_errors
            )
            
        except Exception as e:
            logger.error(f"Error validating file {file.filename}: {e}")
            raise PortAdaFileError(
                message=f"File validation failed: {str(e)}",
                error_code="FILE_VALIDATION_ERROR",
                details={"filename": file.filename},
                original_error=e
            )
    
    def _count_json_records(self, data: Any) -> int:
        """Count records in JSON data"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            return 1
        else:
            return 1
    
    def _count_yaml_records(self, data: Any) -> int:
        """Count records in YAML data"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            # Count top-level keys as records
            return len(data.keys()) if data else 0
        else:
            return 1
    
    async def save_uploaded_file(
        self, 
        file: UploadFile, 
        task_id: str,
        preserve_extension: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Save uploaded file to temporary storage
        
        Args:
            file: Uploaded file object
            task_id: Unique task identifier
            preserve_extension: Whether to preserve original file extension
            
        Returns:
            Tuple of (file_path, file_metadata)
        """
        try:
            # Generate filename
            if preserve_extension:
                extension = self._get_file_extension(file.filename)
                temp_filename = f"{task_id}{extension}"
            else:
                temp_filename = task_id
            
            temp_path = os.path.join(self.upload_folder, temp_filename)
            
            # Read file content
            content = await file.read()
            
            # Calculate file hash for integrity checking
            file_hash = self._calculate_file_hash(content)
            
            # Save file
            async with aiofiles.open(temp_path, 'wb') as f:
                await f.write(content)
            
            # Create metadata
            file_metadata = {
                "original_filename": file.filename,
                "saved_filename": temp_filename,
                "file_path": temp_path,
                "file_size": len(content),
                "file_hash": file_hash,
                "content_type": file.content_type,
                "upload_time": datetime.utcnow().isoformat(),
                "task_id": task_id
            }
            
            logger.info(f"File saved: {temp_filename} (task: {task_id})")
            return temp_path, file_metadata
            
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {e}")
            raise PortAdaFileError(
                message=f"Failed to save file: {str(e)}",
                error_code="FILE_SAVE_ERROR",
                details={"filename": file.filename, "task_id": task_id},
                original_error=e
            )
    
    async def read_file_content(self, file_path: str, file_format: FileFormat) -> Any:
        """
        Read and parse file content
        
        Args:
            file_path: Path to the file
            file_format: Expected file format
            
        Returns:
            Parsed file content
        """
        try:
            if not os.path.exists(file_path):
                raise PortAdaFileError(
                    message=f"File not found: {file_path}",
                    error_code="FILE_NOT_FOUND",
                    details={"file_path": file_path}
                )
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            if file_format == FileFormat.JSON:
                return json.loads(content)
            elif file_format in [FileFormat.YAML, FileFormat.YML]:
                return yaml.safe_load(content)
            else:
                raise PortAdaValidationError(
                    message=f"Unsupported file format: {file_format}",
                    error_code="UNSUPPORTED_FORMAT",
                    details={"file_format": file_format.value}
                )
                
        except json.JSONDecodeError as e:
            raise PortAdaValidationError(
                message=f"Invalid JSON content in file: {str(e)}",
                error_code="INVALID_JSON",
                details={"file_path": file_path},
                original_error=e
            )
        except yaml.YAMLError as e:
            raise PortAdaValidationError(
                message=f"Invalid YAML content in file: {str(e)}",
                error_code="INVALID_YAML",
                details={"file_path": file_path},
                original_error=e
            )
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise wrap_portada_error(e, f"reading file {file_path}")
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if file was deleted, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def cleanup_old_files(self, max_age_hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Clean up old temporary files
        
        Args:
            max_age_hours: Maximum age in hours (default: 24)
            
        Returns:
            Cleanup statistics
        """
        try:
            max_age = max_age_hours or self.cleanup_interval_hours
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age)
            
            deleted_files = []
            total_size_freed = 0
            
            for filename in os.listdir(self.upload_folder):
                file_path = os.path.join(self.upload_folder, filename)
                
                if os.path.isfile(file_path):
                    # Check file age
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mtime < cutoff_time:
                        file_size = os.path.getsize(file_path)
                        if self.delete_file(file_path):
                            deleted_files.append(filename)
                            total_size_freed += file_size
            
            cleanup_stats = {
                "deleted_files": deleted_files,
                "files_deleted": len(deleted_files),
                "total_size_freed": total_size_freed,
                "cleanup_time": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Cleanup completed: {len(deleted_files)} files deleted, {total_size_freed} bytes freed")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error during file cleanup: {e}")
            return {
                "deleted_files": [],
                "files_deleted": 0,
                "total_size_freed": 0,
                "error": str(e)
            }
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            File information dictionary or None if file doesn't exist
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            
            return {
                "file_path": file_path,
                "filename": os.path.basename(file_path),
                "file_size": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_file": os.path.isfile(file_path),
                "is_readable": os.access(file_path, os.R_OK),
                "is_writable": os.access(file_path, os.W_OK)
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None
    
    def list_upload_folder_contents(self) -> List[Dict[str, Any]]:
        """
        List contents of the upload folder
        
        Returns:
            List of file information dictionaries
        """
        try:
            files = []
            
            for filename in os.listdir(self.upload_folder):
                file_path = os.path.join(self.upload_folder, filename)
                file_info = self.get_file_info(file_path)
                if file_info:
                    files.append(file_info)
            
            return sorted(files, key=lambda x: x['modified_time'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing upload folder contents: {e}")
            return []


# Global file service instance
file_service = FileService()