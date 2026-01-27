"""
Enhanced File Handler with database integration and improved error handling
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from fastapi import UploadFile
from pathlib import Path

from ..storage.storage_service import StorageService
from ..database.database_service import DatabaseService
from ..database.models import ProcessingRecord, FileMetadata
from ..core.config import settings
from ..core.exceptions import PortAdaFileError, PortAdaValidationError

logger = logging.getLogger(__name__)


class ProcessingResult:
    """Result of file processing operation"""
    
    def __init__(self, success: bool, record_id: Optional[str] = None, 
                 error_message: Optional[str] = None, file_path: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.success = success
        self.record_id = record_id
        self.error_message = error_message
        self.file_path = file_path
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'success': self.success,
            'record_id': self.record_id,
            'error_message': self.error_message,
            'file_path': self.file_path,
            'metadata': self.metadata
        }


class EnhancedFileHandler:
    """
    Enhanced file handler that integrates storage service with database persistence.
    
    Provides comprehensive file processing with atomic operations, database tracking,
    metadata preservation, and concurrent upload handling.
    """
    
    def __init__(self, storage_service: StorageService, database_service: DatabaseService):
        """
        Initialize the EnhancedFileHandler.
        
        Args:
            storage_service: StorageService instance for file operations
            database_service: DatabaseService instance for persistence
        """
        self.storage_service = storage_service
        self.database_service = database_service
        self.max_file_size_bytes = settings.storage.MAX_FILE_SIZE_MB * 1024 * 1024
        self.allowed_extensions = settings.storage.ALLOWED_FILE_EXTENSIONS
        
        logger.info("EnhancedFileHandler initialized")
    
    async def process_upload(self, file: UploadFile, session_id: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Process file upload with comprehensive validation, storage, and database tracking.
        
        Args:
            file: Uploaded file object
            session_id: Session ID for tracking
            metadata: Optional additional metadata
            
        Returns:
            ProcessingResult: Result of the processing operation
        """
        processing_start = datetime.utcnow()
        
        try:
            logger.info(f"Processing upload: {file.filename} for session: {session_id}")
            
            # Read file content
            content = await file.read()
            await file.seek(0)  # Reset file pointer for potential re-reading
            
            # Validate file
            validation_result = await self.validate_file(file, content)
            if not validation_result['is_valid']:
                error_msg = f"File validation failed: {'; '.join(validation_result['errors'])}"
                logger.warning(f"Validation failed for {file.filename}: {error_msg}")
                return ProcessingResult(
                    success=False,
                    error_message=error_msg,
                    metadata={'validation_errors': validation_result['errors']}
                )
            
            # Save file to storage
            storage_result = self.storage_service.save_file(content, file.filename)
            
            # Create processing record
            file_info = {
                'original_filename': file.filename,
                'stored_filename': storage_result['stored_filename'],
                'file_size': storage_result['file_size'],
                'file_path': storage_result['file_path'],
                'metadata': {
                    'upload_timestamp': storage_result['upload_timestamp'],
                    'file_id': storage_result['file_id'],
                    'content_type': file.content_type,
                    'validation_result': validation_result,
                    **(metadata or {})
                }
            }
            
            processing_record = await self.database_service.create_processing_record(
                session_id, file_info
            )
            
            # Create file metadata record
            file_metadata_info = await self._analyze_file_content(content, file.filename)
            await self.database_service.create_file_metadata(
                processing_record.id, file_metadata_info
            )
            
            processing_end = datetime.utcnow()
            processing_duration = (processing_end - processing_start).total_seconds()
            
            logger.info(f"Successfully processed upload: {file.filename} -> {storage_result['stored_filename']} "
                       f"(duration: {processing_duration:.2f}s)")
            
            return ProcessingResult(
                success=True,
                record_id=processing_record.id,
                file_path=storage_result['file_path'],
                metadata={
                    'file_id': storage_result['file_id'],
                    'stored_filename': storage_result['stored_filename'],
                    'processing_duration_seconds': processing_duration,
                    'validation_result': validation_result
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing upload {file.filename}: {e}")
            
            # Try to clean up any partial files
            try:
                if 'storage_result' in locals() and storage_result.get('file_path'):
                    self.storage_service.delete_file(
                        storage_result['file_id'], 
                        Path(file.filename).suffix
                    )
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")
            
            return ProcessingResult(
                success=False,
                error_message=f"Upload processing failed: {str(e)}",
                metadata={'error_type': type(e).__name__}
            )
    
    async def validate_file(self, file: UploadFile, content: bytes) -> Dict[str, Any]:
        """
        Comprehensive file validation.
        
        Args:
            file: Uploaded file object
            content: File content bytes
            
        Returns:
            dict: Validation result with is_valid flag and errors list
        """
        errors = []
        warnings = []
        
        try:
            # Basic validations
            if not file.filename:
                errors.append("Filename is required")
            
            if len(content) == 0:
                errors.append("File is empty")
            
            if len(content) > self.max_file_size_bytes:
                errors.append(f"File size ({len(content)} bytes) exceeds maximum "
                             f"allowed size ({self.max_file_size_bytes} bytes)")
            
            # Extension validation
            if file.filename:
                file_extension = Path(file.filename).suffix.lower()
                if file_extension not in [ext.lower() for ext in self.allowed_extensions]:
                    errors.append(f"File extension '{file_extension}' not allowed. "
                                 f"Allowed extensions: {self.allowed_extensions}")
            
            # Content validation
            if len(content) > 0:
                content_validation = await self._validate_file_content(content, file.filename)
                errors.extend(content_validation.get('errors', []))
                warnings.extend(content_validation.get('warnings', []))
            
            return {
                'is_valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'file_size': len(content),
                'content_type': file.content_type
            }
            
        except Exception as e:
            logger.error(f"Error during file validation: {e}")
            return {
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': warnings,
                'file_size': len(content) if content else 0,
                'content_type': file.content_type
            }
    
    async def _validate_file_content(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate file content based on file type.
        
        Args:
            content: File content bytes
            filename: Original filename
            
        Returns:
            dict: Content validation results
        """
        errors = []
        warnings = []
        
        try:
            # Decode content
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_content = content.decode('latin-1')
                    warnings.append("File encoding detected as latin-1, UTF-8 preferred")
                except UnicodeDecodeError:
                    errors.append("File encoding not supported (must be UTF-8 or latin-1)")
                    return {'errors': errors, 'warnings': warnings}
            
            # JSON validation
            file_extension = Path(filename).suffix.lower()
            if file_extension == '.json':
                try:
                    json_data = json.loads(text_content)
                    
                    # Additional JSON validations
                    if isinstance(json_data, dict) and len(json_data) == 0:
                        warnings.append("JSON file contains empty object")
                    elif isinstance(json_data, list) and len(json_data) == 0:
                        warnings.append("JSON file contains empty array")
                    
                except json.JSONDecodeError as e:
                    errors.append(f"Invalid JSON format: {str(e)}")
            
            # CSV validation (basic)
            elif file_extension == '.csv':
                lines = text_content.split('\n')
                if len(lines) < 2:
                    warnings.append("CSV file has fewer than 2 lines (header + data)")
                
                # Check for consistent column count
                if len(lines) >= 2:
                    header_cols = len(lines[0].split(','))
                    for i, line in enumerate(lines[1:3], 1):  # Check first few data lines
                        if line.strip():  # Skip empty lines
                            data_cols = len(line.split(','))
                            if data_cols != header_cols:
                                warnings.append(f"Inconsistent column count on line {i+1}")
                                break
            
            return {'errors': errors, 'warnings': warnings}
            
        except Exception as e:
            logger.error(f"Error validating file content: {e}")
            return {
                'errors': [f"Content validation error: {str(e)}"],
                'warnings': warnings
            }
    
    async def _analyze_file_content(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        Analyze file content and extract metadata.
        
        Args:
            content: File content bytes
            filename: Original filename
            
        Returns:
            dict: File metadata information
        """
        analysis_start = datetime.utcnow()
        
        try:
            # Basic analysis
            file_extension = Path(filename).suffix.lower()
            content_hash = hashlib.sha256(content).hexdigest()
            
            # Detect encoding
            encoding = 'utf-8'
            try:
                content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content.decode('latin-1')
                    encoding = 'latin-1'
                except UnicodeDecodeError:
                    encoding = 'unknown'
            
            # Text analysis
            line_count = None
            record_count = None
            content_preview = None
            is_valid_json = False
            is_valid_csv = False
            validation_errors = []
            
            if encoding != 'unknown':
                try:
                    text_content = content.decode(encoding)
                    lines = text_content.split('\n')
                    line_count = len(lines)
                    
                    # Create preview (first 500 characters)
                    content_preview = text_content[:500]
                    if len(text_content) > 500:
                        content_preview += "..."
                    
                    # Format-specific analysis
                    if file_extension == '.json':
                        try:
                            json_data = json.loads(text_content)
                            is_valid_json = True
                            
                            if isinstance(json_data, list):
                                record_count = len(json_data)
                            elif isinstance(json_data, dict):
                                record_count = 1
                                
                        except json.JSONDecodeError as e:
                            validation_errors.append(f"JSON parsing error: {str(e)}")
                    
                    elif file_extension == '.csv':
                        is_valid_csv = True
                        if line_count > 1:  # Header + data
                            record_count = line_count - 1  # Exclude header
                        
                except Exception as e:
                    validation_errors.append(f"Text analysis error: {str(e)}")
            
            analysis_end = datetime.utcnow()
            analysis_duration = (analysis_end - analysis_start).total_seconds() * 1000
            
            return {
                'file_type': file_extension.lstrip('.') if file_extension else 'unknown',
                'encoding': encoding,
                'line_count': line_count,
                'record_count': record_count,
                'content_hash': content_hash,
                'content_preview': content_preview,
                'is_valid_json': is_valid_json,
                'is_valid_csv': is_valid_csv,
                'validation_errors': validation_errors,
                'analysis_duration_ms': int(analysis_duration)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing file content: {e}")
            return {
                'file_type': 'unknown',
                'encoding': 'unknown',
                'content_hash': hashlib.sha256(content).hexdigest(),
                'validation_errors': [f"Analysis error: {str(e)}"],
                'analysis_duration_ms': 0
            }
    
    def generate_unique_filename(self, original_name: str) -> str:
        """
        Generate unique filename based on original name.
        
        Args:
            original_name: Original filename
            
        Returns:
            str: Unique filename
        """
        # This is handled by StorageService.save_file() with UUID generation
        # This method is kept for compatibility
        import uuid
        file_extension = Path(original_name).suffix
        return f"{uuid.uuid4()}{file_extension}"
    
    async def get_processing_record(self, record_id: str) -> Optional[ProcessingRecord]:
        """
        Get processing record by ID.
        
        Args:
            record_id: Processing record ID
            
        Returns:
            ProcessingRecord or None if not found
        """
        try:
            return await self.database_service.get_processing_record_by_id(record_id)
        except Exception as e:
            logger.error(f"Error getting processing record {record_id}: {e}")
            return None
    
    async def update_processing_status(self, record_id: str, status: str, 
                                     error_message: Optional[str] = None) -> bool:
        """
        Update processing record status.
        
        Args:
            record_id: Processing record ID
            status: New status
            error_message: Optional error message
            
        Returns:
            bool: True if updated successfully
        """
        try:
            return await self.database_service.update_processing_status(
                record_id, status, error_message
            )
        except Exception as e:
            logger.error(f"Error updating processing status {record_id}: {e}")
            return False
    
    async def cleanup_failed_uploads(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Clean up failed uploads and orphaned files.
        
        Args:
            max_age_hours: Maximum age for cleanup
            
        Returns:
            dict: Cleanup statistics
        """
        try:
            logger.info(f"Starting cleanup of failed uploads older than {max_age_hours} hours")
            
            # Clean up storage files
            storage_cleanup = self.storage_service.cleanup_temp_files(max_age_hours)
            
            # Get database cleanup stats
            db_stats = await self.database_service.get_database_stats()
            
            return {
                'success': True,
                'storage_files_cleaned': storage_cleanup,
                'database_stats': db_stats,
                'cleanup_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during failed uploads cleanup: {e}")
            return {
                'success': False,
                'error': str(e),
                'cleanup_timestamp': datetime.utcnow().isoformat()
            }