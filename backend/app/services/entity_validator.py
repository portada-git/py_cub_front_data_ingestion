"""
Entity Validator for ensuring data consistency between backend and frontend
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from ..database.models import ProcessingRecord, Session, FileMetadata

logger = logging.getLogger(__name__)


class EntityValidator:
    """
    Validates and transforms database entities into frontend-compatible JSON structures.
    
    Ensures all required fields are present, properly formatted, and handles null values
    with appropriate defaults to prevent frontend errors.
    """
    
    def __init__(self):
        """Initialize the EntityValidator"""
        logger.info("EntityValidator initialized")
    
    def validate_processing_record(self, record: ProcessingRecord) -> Dict[str, Any]:
        """
        Validate and transform a processing record for frontend consumption.
        
        Args:
            record: ProcessingRecord instance to validate
            
        Returns:
            dict: Validated and transformed processing record
        """
        try:
            if not record:
                logger.warning("Received null processing record")
                return self._get_default_processing_record()
            
            # Transform to dictionary
            record_dict = record.to_dict()
            
            # Validate and sanitize required fields
            validated_record = {
                'id': self._validate_string(record_dict.get('id'), 'unknown'),
                'session_id': self._validate_string(record_dict.get('session_id'), 'unknown'),
                'original_filename': self._validate_string(record_dict.get('original_filename'), 'unknown.json'),
                'stored_filename': self._validate_string(record_dict.get('stored_filename'), 'unknown.json'),
                'file_size': self._validate_integer(record_dict.get('file_size'), 0),
                'file_path': self._validate_string(record_dict.get('file_path'), ''),
                'upload_timestamp': self._validate_iso_timestamp(record_dict.get('upload_timestamp')),
                'processing_status': self._validate_processing_status(record_dict.get('processing_status')),
                'processing_started_at': self._validate_iso_timestamp(record_dict.get('processing_started_at')),
                'processing_completed_at': self._validate_iso_timestamp(record_dict.get('processing_completed_at')),
                'processing_duration_seconds': self._validate_float(record_dict.get('processing_duration_seconds')),
                'error_message': self._validate_string(record_dict.get('error_message')),
                'retry_count': self._validate_integer(record_dict.get('retry_count'), 0),
                'metadata': self._validate_metadata(record_dict.get('metadata')),
                'is_complete': self._validate_boolean(record_dict.get('is_complete'), False)
            }
            
            logger.debug(f"Validated processing record: {validated_record['id']}")
            return validated_record
            
        except Exception as e:
            logger.error(f"Error validating processing record: {e}")
            return self._get_default_processing_record()
    
    def validate_session(self, session: Session) -> Dict[str, Any]:
        """
        Validate and transform a session for frontend consumption.
        
        Args:
            session: Session instance to validate
            
        Returns:
            dict: Validated and transformed session
        """
        try:
            if not session:
                logger.warning("Received null session")
                return self._get_default_session()
            
            # Transform to dictionary
            session_dict = session.to_dict()
            
            # Validate and sanitize required fields
            validated_session = {
                'id': self._validate_string(session_dict.get('id'), 'unknown'),
                'created_at': self._validate_iso_timestamp(session_dict.get('created_at')),
                'last_accessed': self._validate_iso_timestamp(session_dict.get('last_accessed')),
                'expires_at': self._validate_iso_timestamp(session_dict.get('expires_at')),
                'is_expired': self._validate_boolean(session_dict.get('is_expired'), True),
                'metadata': self._validate_metadata(session_dict.get('metadata'))
            }
            
            logger.debug(f"Validated session: {validated_session['id']}")
            return validated_session
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return self._get_default_session()
    
    def validate_file_metadata(self, metadata: FileMetadata) -> Dict[str, Any]:
        """
        Validate and transform file metadata for frontend consumption.
        
        Args:
            metadata: FileMetadata instance to validate
            
        Returns:
            dict: Validated and transformed file metadata
        """
        try:
            if not metadata:
                logger.warning("Received null file metadata")
                return self._get_default_file_metadata()
            
            # Transform to dictionary
            metadata_dict = metadata.to_dict()
            
            # Validate and sanitize required fields
            validated_metadata = {
                'id': self._validate_string(metadata_dict.get('id'), 'unknown'),
                'processing_record_id': self._validate_string(metadata_dict.get('processing_record_id'), 'unknown'),
                'file_type': self._validate_string(metadata_dict.get('file_type'), 'unknown'),
                'encoding': self._validate_string(metadata_dict.get('encoding'), 'unknown'),
                'line_count': self._validate_integer(metadata_dict.get('line_count')),
                'record_count': self._validate_integer(metadata_dict.get('record_count')),
                'content_hash': self._validate_string(metadata_dict.get('content_hash')),
                'content_preview': self._validate_string(metadata_dict.get('content_preview')),
                'is_valid_json': self._validate_boolean(metadata_dict.get('is_valid_json')),
                'is_valid_csv': self._validate_boolean(metadata_dict.get('is_valid_csv')),
                'validation_errors': self._validate_list(metadata_dict.get('validation_errors')),
                'analysis_timestamp': self._validate_iso_timestamp(metadata_dict.get('analysis_timestamp')),
                'analysis_duration_ms': self._validate_integer(metadata_dict.get('analysis_duration_ms')),
                'metadata': self._validate_metadata(metadata_dict.get('metadata'))
            }
            
            logger.debug(f"Validated file metadata: {validated_metadata['id']}")
            return validated_metadata
            
        except Exception as e:
            logger.error(f"Error validating file metadata: {e}")
            return self._get_default_file_metadata()
    
    def transform_for_frontend(self, records: List[Union[ProcessingRecord, Session, FileMetadata]]) -> List[Dict[str, Any]]:
        """
        Transform a list of database entities for frontend consumption.
        
        Args:
            records: List of database entities to transform
            
        Returns:
            list: List of validated and transformed entities
        """
        try:
            if not records:
                return []
            
            transformed_records = []
            
            for record in records:
                try:
                    if isinstance(record, ProcessingRecord):
                        validated = self.validate_processing_record(record)
                    elif isinstance(record, Session):
                        validated = self.validate_session(record)
                    elif isinstance(record, FileMetadata):
                        validated = self.validate_file_metadata(record)
                    else:
                        logger.warning(f"Unknown entity type: {type(record)}")
                        continue
                    
                    transformed_records.append(validated)
                    
                except Exception as e:
                    logger.error(f"Error transforming record {getattr(record, 'id', 'unknown')}: {e}")
                    # Skip invalid records rather than fail the entire operation
                    continue
            
            logger.info(f"Transformed {len(transformed_records)} records for frontend")
            return transformed_records
            
        except Exception as e:
            logger.error(f"Error transforming records for frontend: {e}")
            return []
    
    def sanitize_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize an entity dictionary by removing potentially harmful content.
        
        Args:
            entity: Entity dictionary to sanitize
            
        Returns:
            dict: Sanitized entity dictionary
        """
        try:
            if not isinstance(entity, dict):
                logger.warning(f"Expected dict, got {type(entity)}")
                return {}
            
            sanitized = {}
            
            for key, value in entity.items():
                # Skip private/internal fields
                if key.startswith('_'):
                    continue
                
                # Sanitize string values
                if isinstance(value, str):
                    sanitized[key] = self._sanitize_string(value)
                elif isinstance(value, dict):
                    sanitized[key] = self.sanitize_entity(value)
                elif isinstance(value, list):
                    sanitized[key] = [self.sanitize_entity(item) if isinstance(item, dict) else item for item in value]
                else:
                    sanitized[key] = value
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing entity: {e}")
            return {}
    
    def validate_required_fields(self, entity: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validate that an entity has all required fields.
        
        Args:
            entity: Entity dictionary to validate
            required_fields: List of required field names
            
        Returns:
            bool: True if all required fields are present and valid
        """
        try:
            if not isinstance(entity, dict):
                return False
            
            for field in required_fields:
                if field not in entity:
                    logger.warning(f"Missing required field: {field}")
                    return False
                
                value = entity[field]
                if value is None or (isinstance(value, str) and not value.strip()):
                    logger.warning(f"Required field '{field}' is empty")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating required fields: {e}")
            return False
    
    # Private validation methods
    
    def _validate_string(self, value: Any, default: Optional[str] = None) -> Optional[str]:
        """Validate and convert value to string"""
        if value is None:
            return default
        if isinstance(value, str):
            return value.strip() if value.strip() else default
        return str(value) if value is not None else default
    
    def _validate_integer(self, value: Any, default: Optional[int] = None) -> Optional[int]:
        """Validate and convert value to integer"""
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _validate_float(self, value: Any, default: Optional[float] = None) -> Optional[float]:
        """Validate and convert value to float"""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _validate_boolean(self, value: Any, default: bool = False) -> bool:
        """Validate and convert value to boolean"""
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    def _validate_iso_timestamp(self, value: Any) -> Optional[str]:
        """Validate ISO timestamp format"""
        if value is None:
            return None
        
        if isinstance(value, str):
            # Basic ISO format validation
            if 'T' in value and ('Z' in value or '+' in value or value.endswith('00')):
                return value
        
        # Try to convert datetime to ISO format
        try:
            if hasattr(value, 'isoformat'):
                return value.isoformat()
        except Exception:
            pass
        
        return None
    
    def _validate_processing_status(self, value: Any) -> str:
        """Validate processing status"""
        valid_statuses = ['uploaded', 'processing', 'completed', 'failed', 'cancelled']
        if value in valid_statuses:
            return value
        return 'uploaded'  # Default status
    
    def _validate_metadata(self, value: Any) -> Dict[str, Any]:
        """Validate metadata dictionary"""
        if isinstance(value, dict):
            return value
        return {}
    
    def _validate_list(self, value: Any) -> List[Any]:
        """Validate list value"""
        if isinstance(value, list):
            return value
        return []
    
    def _sanitize_string(self, value: str, max_length: int = 10000) -> str:
        """Sanitize string value"""
        if not isinstance(value, str):
            return str(value)
        
        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length] + "..."
        
        # Remove potentially harmful characters (basic sanitization)
        # In a production environment, you might want more sophisticated sanitization
        return value.replace('\x00', '').strip()
    
    # Default entity generators
    
    def _get_default_processing_record(self) -> Dict[str, Any]:
        """Get default processing record structure"""
        return {
            'id': 'unknown',
            'session_id': 'unknown',
            'original_filename': 'unknown.json',
            'stored_filename': 'unknown.json',
            'file_size': 0,
            'file_path': '',
            'upload_timestamp': datetime.utcnow().isoformat(),
            'processing_status': 'failed',
            'processing_started_at': None,
            'processing_completed_at': None,
            'processing_duration_seconds': None,
            'error_message': 'Entity validation failed',
            'retry_count': 0,
            'metadata': {},
            'is_complete': True
        }
    
    def _get_default_session(self) -> Dict[str, Any]:
        """Get default session structure"""
        return {
            'id': 'unknown',
            'created_at': datetime.utcnow().isoformat(),
            'last_accessed': datetime.utcnow().isoformat(),
            'expires_at': datetime.utcnow().isoformat(),
            'is_expired': True,
            'metadata': {}
        }
    
    def _get_default_file_metadata(self) -> Dict[str, Any]:
        """Get default file metadata structure"""
        return {
            'id': 'unknown',
            'processing_record_id': 'unknown',
            'file_type': 'unknown',
            'encoding': 'unknown',
            'line_count': None,
            'record_count': None,
            'content_hash': None,
            'content_preview': None,
            'is_valid_json': None,
            'is_valid_csv': None,
            'validation_errors': [],
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'analysis_duration_ms': None,
            'metadata': {}
        }

class ValidationError(Exception):
    """Custom exception for validation errors"""
    
    def __init__(self, message: str, field: str = None, entity_type: str = None):
        self.message = message
        self.field = field
        self.entity_type = entity_type
        super().__init__(self.message)


class EntityFilter:
    """
    Filters and processes entities based on various criteria.
    
    Handles unknown entities, validation failures, and provides
    filtering capabilities for frontend consumption.
    """
    
    def __init__(self, validator: EntityValidator):
        """
        Initialize EntityFilter with a validator instance.
        
        Args:
            validator: EntityValidator instance
        """
        self.validator = validator
        logger.info("EntityFilter initialized")
    
    def filter_valid_entities(self, entities: List[Dict[str, Any]], 
                            entity_type: str = 'processing_record') -> List[Dict[str, Any]]:
        """
        Filter out invalid entities and return only valid ones.
        
        Args:
            entities: List of entity dictionaries
            entity_type: Type of entities being filtered
            
        Returns:
            list: List of valid entities
        """
        try:
            valid_entities = []
            invalid_count = 0
            
            for entity in entities:
                try:
                    if self._is_valid_entity(entity, entity_type):
                        # Additional sanitization
                        sanitized = self.validator.sanitize_entity(entity)
                        valid_entities.append(sanitized)
                    else:
                        invalid_count += 1
                        logger.debug(f"Filtered out invalid {entity_type}: {entity.get('id', 'unknown')}")
                        
                except Exception as e:
                    invalid_count += 1
                    logger.warning(f"Error processing {entity_type} entity: {e}")
                    continue
            
            if invalid_count > 0:
                logger.info(f"Filtered out {invalid_count} invalid {entity_type} entities")
            
            return valid_entities
            
        except Exception as e:
            logger.error(f"Error filtering entities: {e}")
            return []
    
    def filter_by_status(self, processing_records: List[Dict[str, Any]], 
                        allowed_statuses: List[str]) -> List[Dict[str, Any]]:
        """
        Filter processing records by status.
        
        Args:
            processing_records: List of processing record dictionaries
            allowed_statuses: List of allowed status values
            
        Returns:
            list: Filtered processing records
        """
        try:
            filtered_records = []
            
            for record in processing_records:
                status = record.get('processing_status')
                if status in allowed_statuses:
                    filtered_records.append(record)
                else:
                    logger.debug(f"Filtered out record with status '{status}': {record.get('id', 'unknown')}")
            
            logger.debug(f"Filtered {len(processing_records)} records to {len(filtered_records)} by status")
            return filtered_records
            
        except Exception as e:
            logger.error(f"Error filtering by status: {e}")
            return processing_records  # Return original list on error
    
    def filter_by_date_range(self, entities: List[Dict[str, Any]], 
                           date_field: str, start_date: Optional[str] = None, 
                           end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Filter entities by date range.
        
        Args:
            entities: List of entity dictionaries
            date_field: Name of the date field to filter by
            start_date: Start date in ISO format (inclusive)
            end_date: End date in ISO format (inclusive)
            
        Returns:
            list: Filtered entities
        """
        try:
            if not start_date and not end_date:
                return entities
            
            filtered_entities = []
            
            for entity in entities:
                entity_date = entity.get(date_field)
                if not entity_date:
                    continue
                
                # Simple string comparison for ISO dates (works for ISO format)
                include_entity = True
                
                if start_date and entity_date < start_date:
                    include_entity = False
                
                if end_date and entity_date > end_date:
                    include_entity = False
                
                if include_entity:
                    filtered_entities.append(entity)
            
            logger.debug(f"Filtered {len(entities)} entities to {len(filtered_entities)} by date range")
            return filtered_entities
            
        except Exception as e:
            logger.error(f"Error filtering by date range: {e}")
            return entities  # Return original list on error
    
    def filter_unknown_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out entities with unknown or invalid IDs.
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            list: Filtered entities with valid IDs
        """
        try:
            filtered_entities = []
            unknown_count = 0
            
            for entity in entities:
                entity_id = entity.get('id')
                
                # Filter out entities with unknown, empty, or invalid IDs
                if (entity_id and 
                    entity_id != 'unknown' and 
                    isinstance(entity_id, str) and 
                    len(entity_id.strip()) > 0):
                    filtered_entities.append(entity)
                else:
                    unknown_count += 1
                    logger.debug(f"Filtered out entity with unknown ID: {entity_id}")
            
            if unknown_count > 0:
                logger.info(f"Filtered out {unknown_count} entities with unknown IDs")
            
            return filtered_entities
            
        except Exception as e:
            logger.error(f"Error filtering unknown entities: {e}")
            return entities  # Return original list on error
    
    def handle_validation_failure(self, entity: Any, error: Exception, 
                                entity_type: str = 'unknown') -> Optional[Dict[str, Any]]:
        """
        Handle validation failure by logging error and returning safe default.
        
        Args:
            entity: Original entity that failed validation
            error: Exception that occurred during validation
            entity_type: Type of entity that failed
            
        Returns:
            dict or None: Safe default entity or None to filter out
        """
        try:
            entity_id = getattr(entity, 'id', 'unknown') if hasattr(entity, 'id') else 'unknown'
            
            logger.error(f"Validation failed for {entity_type} {entity_id}: {error}")
            
            # Decide whether to return a safe default or filter out entirely
            if entity_type == 'processing_record':
                # For processing records, return a safe default to maintain UI consistency
                return self.validator._get_default_processing_record()
            elif entity_type == 'session':
                # For sessions, return a safe default
                return self.validator._get_default_session()
            elif entity_type == 'file_metadata':
                # For file metadata, return a safe default
                return self.validator._get_default_file_metadata()
            else:
                # For unknown types, filter out entirely
                return None
                
        except Exception as e:
            logger.error(f"Error handling validation failure: {e}")
            return None
    
    def validate_and_filter_batch(self, entities: List[Any], 
                                entity_type: str = 'processing_record') -> List[Dict[str, Any]]:
        """
        Validate and filter a batch of entities with comprehensive error handling.
        
        Args:
            entities: List of database entities
            entity_type: Type of entities being processed
            
        Returns:
            list: List of validated and filtered entities
        """
        try:
            if not entities:
                return []
            
            validated_entities = []
            error_count = 0
            
            for entity in entities:
                try:
                    # Validate based on entity type
                    if entity_type == 'processing_record':
                        validated = self.validator.validate_processing_record(entity)
                    elif entity_type == 'session':
                        validated = self.validator.validate_session(entity)
                    elif entity_type == 'file_metadata':
                        validated = self.validator.validate_file_metadata(entity)
                    else:
                        logger.warning(f"Unknown entity type: {entity_type}")
                        continue
                    
                    # Additional filtering
                    if self._is_valid_entity(validated, entity_type):
                        validated_entities.append(validated)
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    # Try to handle the validation failure
                    fallback = self.handle_validation_failure(entity, e, entity_type)
                    if fallback:
                        validated_entities.append(fallback)
            
            if error_count > 0:
                logger.warning(f"Encountered {error_count} validation errors in batch of {len(entities)} {entity_type} entities")
            
            logger.info(f"Successfully validated {len(validated_entities)} out of {len(entities)} {entity_type} entities")
            return validated_entities
            
        except Exception as e:
            logger.error(f"Error in batch validation and filtering: {e}")
            return []
    
    def _is_valid_entity(self, entity: Dict[str, Any], entity_type: str) -> bool:
        """
        Check if an entity is valid based on its type.
        
        Args:
            entity: Entity dictionary to validate
            entity_type: Type of entity
            
        Returns:
            bool: True if entity is valid
        """
        try:
            if not isinstance(entity, dict):
                return False
            
            # Common validations
            if not entity.get('id') or entity.get('id') == 'unknown':
                return False
            
            # Type-specific validations
            if entity_type == 'processing_record':
                required_fields = ['session_id', 'original_filename', 'processing_status']
                return self.validator.validate_required_fields(entity, required_fields)
            
            elif entity_type == 'session':
                required_fields = ['created_at', 'expires_at']
                return self.validator.validate_required_fields(entity, required_fields)
            
            elif entity_type == 'file_metadata':
                required_fields = ['processing_record_id', 'file_type']
                return self.validator.validate_required_fields(entity, required_fields)
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating entity: {e}")
            return False


# Enhanced EntityValidator with error handling integration
class EnhancedEntityValidator(EntityValidator):
    """
    Enhanced EntityValidator with integrated error handling and filtering capabilities.
    """
    
    def __init__(self):
        super().__init__()
        self.filter = EntityFilter(self)
        logger.info("EnhancedEntityValidator initialized with filtering capabilities")
    
    def validate_and_transform_batch(self, entities: List[Any], 
                                   entity_type: str = 'processing_record',
                                   apply_filters: bool = True) -> List[Dict[str, Any]]:
        """
        Validate, transform, and optionally filter a batch of entities.
        
        Args:
            entities: List of database entities
            entity_type: Type of entities
            apply_filters: Whether to apply additional filtering
            
        Returns:
            list: Processed entities ready for frontend consumption
        """
        try:
            # First pass: validate and transform
            validated_entities = self.filter.validate_and_filter_batch(entities, entity_type)
            
            if not apply_filters:
                return validated_entities
            
            # Second pass: apply additional filters
            filtered_entities = self.filter.filter_unknown_entities(validated_entities)
            filtered_entities = self.filter.filter_valid_entities(filtered_entities, entity_type)
            
            return filtered_entities
            
        except Exception as e:
            logger.error(f"Error in enhanced validation and transformation: {e}")
            return []
    
    def get_validation_summary(self, original_count: int, final_count: int, 
                             entity_type: str) -> Dict[str, Any]:
        """
        Get a summary of the validation process.
        
        Args:
            original_count: Original number of entities
            final_count: Final number of valid entities
            entity_type: Type of entities processed
            
        Returns:
            dict: Validation summary
        """
        filtered_count = original_count - final_count
        success_rate = (final_count / original_count * 100) if original_count > 0 else 0
        
        return {
            'entity_type': entity_type,
            'original_count': original_count,
            'final_count': final_count,
            'filtered_count': filtered_count,
            'success_rate_percent': round(success_rate, 2),
            'timestamp': datetime.utcnow().isoformat()
        }