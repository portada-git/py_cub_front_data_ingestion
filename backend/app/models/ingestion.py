"""
Pydantic models for data ingestion operations
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class IngestionType(str, Enum):
    """Types of data ingestion supported"""
    EXTRACTION_DATA = "extraction_data"
    KNOWN_ENTITIES = "known_entities"


class FileFormat(str, Enum):
    """Supported file formats"""
    JSON = "json"
    YAML = "yaml"
    YML = "yml"


class IngestionRequest(BaseModel):
    """Request model for data ingestion"""
    ingestion_type: IngestionType = Field(..., description="Type of ingestion to perform")
    publication: Optional[str] = Field(None, description="Publication identifier (required for extraction data)")
    entity_name: Optional[str] = Field("known_entities", description="Entity name (for known entities ingestion)")
    data_path_delta_lake: Optional[str] = Field("ship_entries", description="Destination path in delta lake")
    
    @validator('publication')
    def validate_publication_for_extraction(cls, v, values):
        """Validate publication is provided for extraction data"""
        if values.get('ingestion_type') == IngestionType.EXTRACTION_DATA and not v:
            raise ValueError("Publication is required for extraction data ingestion")
        return v
    
    @validator('publication')
    def validate_publication_format(cls, v):
        """Validate publication format"""
        if v and not v.strip():
            raise ValueError("Publication cannot be empty")
        return v.strip() if v else v


class FileValidation(BaseModel):
    """Model for file validation results"""
    is_valid: bool = Field(..., description="Whether the file is valid")
    file_size: int = Field(..., description="File size in bytes")
    file_format: FileFormat = Field(..., description="Detected file format")
    record_count: Optional[int] = Field(None, description="Number of records in file")
    validation_errors: List[str] = Field(default_factory=list, description="List of validation errors")
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """Validate file size is reasonable"""
        max_size = 100 * 1024 * 1024  # 100MB
        if v > max_size:
            raise ValueError(f"File size {v} bytes exceeds maximum allowed size of {max_size} bytes")
        return v


class IngestionStatus(str, Enum):
    """Status of ingestion process"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionResponse(BaseModel):
    """Response model for data ingestion"""
    task_id: str = Field(..., description="Unique task identifier")
    status: IngestionStatus = Field(..., description="Current status of the ingestion")
    message: str = Field(..., description="Status message or error description")
    records_processed: int = Field(0, description="Number of records processed")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="When the ingestion started")
    completed_at: Optional[datetime] = Field(None, description="When the ingestion completed")
    file_validation: Optional[FileValidation] = Field(None, description="File validation results")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class IngestionStatusResponse(BaseModel):
    """Response model for ingestion status queries"""
    task_id: str = Field(..., description="Task identifier")
    status: IngestionStatus = Field(..., description="Current status")
    message: str = Field(..., description="Current status message")
    progress_percentage: Optional[float] = Field(None, description="Progress percentage (0-100)")
    records_processed: int = Field(0, description="Records processed so far")
    estimated_total: Optional[int] = Field(None, description="Estimated total records")
    started_at: datetime = Field(..., description="When the task started")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProcessIsolationStatus(BaseModel):
    """Model for process isolation status"""
    is_processing: bool = Field(..., description="Whether any ingestion is currently processing")
    current_task_id: Optional[str] = Field(None, description="ID of currently running task")
    current_ingestion_type: Optional[IngestionType] = Field(None, description="Type of current ingestion")
    queue_length: int = Field(0, description="Number of tasks in queue")
    estimated_wait_time: Optional[int] = Field(None, description="Estimated wait time in seconds")