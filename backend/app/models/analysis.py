"""
Pydantic models for data analysis operations
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, date


class DateFormat(str, Enum):
    """Supported date formats"""
    YYYY_MM_DD = "YYYY-MM-DD"
    DD_MM_YYYY = "DD/MM/YYYY"
    MM_DD_YYYY = "MM/DD/YYYY"


class FileFormat(str, Enum):
    """Supported file formats for analysis"""
    JSON = "json"
    YAML = "yaml"
    YML = "yml"
    TXT = "txt"


# Missing Dates Models
class MissingDateEntry(BaseModel):
    """Model for missing date entry"""
    date: str = Field(..., description="Missing date in YYYY-MM-DD format")
    edition: str = Field("U", description="Edition identifier")
    gap_duration: Optional[str] = Field(None, description="Duration of the gap")
    
    @validator('date')
    def validate_date_format(cls, v):
        """Validate date format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")


class MissingDatesRequest(BaseModel):
    """Request model for missing dates analysis"""
    publication_name: str = Field(..., description="Publication identifier (e.g., 'db', 'dm', 'sm')")
    data_path: str = Field("ship_entries", description="Path to data in delta lake")
    
    # File-based query parameters
    date_file: Optional[str] = Field(None, description="Path to uploaded file with dates")
    date_and_edition_list: Optional[str] = Field(None, description="List of dates and editions as text (YAML/JSON/TXT)")
    file_format: Optional[FileFormat] = Field(None, description="Format of the uploaded file")
    
    # Date range query parameters
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        """Validate date format"""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate end date is after start date"""
        if v and values.get('start_date'):
            start = datetime.strptime(values['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')
            if end < start:
                raise ValueError("End date must be after start date")
        return v


class MissingDatesResponse(BaseModel):
    """Response model for missing dates analysis"""
    publication_name: str = Field(..., description="Publication analyzed")
    query_type: str = Field(..., description="Type of query performed (file-based or date-range)")
    missing_dates: List[MissingDateEntry] = Field(..., description="List of missing dates")
    total_missing: int = Field(..., description="Total number of missing dates")
    date_range_analyzed: Optional[str] = Field(None, description="Date range that was analyzed")


# Duplicates Models
class DuplicateRecord(BaseModel):
    """Model for duplicate record metadata"""
    log_id: str = Field(..., description="Unique log identifier")
    date: str = Field(..., description="Date of the duplicates")
    edition: str = Field(..., description="Edition identifier")
    publication: str = Field(..., description="Publication name")
    uploaded_by: str = Field(..., description="User who uploaded the data")
    duplicate_count: int = Field(..., description="Number of duplicates found")
    duplicates_filter: str = Field(..., description="Filter used to identify duplicates")
    duplicate_ids: List[str] = Field(..., description="List of duplicate record IDs")


class DuplicateDetail(BaseModel):
    """Model for detailed duplicate information"""
    record_id: str = Field(..., description="Record identifier")
    title: Optional[str] = Field(None, description="Article title")
    content_hash: Optional[str] = Field(None, description="Content hash for comparison")
    similarity_score: Optional[float] = Field(None, description="Similarity score with other duplicates")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DuplicatesRequest(BaseModel):
    """Request model for duplicates analysis"""
    user_responsible: Optional[str] = Field(None, description="Filter by user responsible")
    publication: Optional[str] = Field(None, description="Filter by publication")
    start_date: Optional[str] = Field(None, description="Start date filter (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date filter (YYYY-MM-DD)")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        """Validate date format"""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class DuplicatesResponse(BaseModel):
    """Response model for duplicates analysis"""
    duplicates: List[DuplicateRecord] = Field(..., description="List of duplicate records")
    total_duplicates: int = Field(..., description="Total number of duplicate entries")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied")


class DuplicateDetailsResponse(BaseModel):
    """Response model for duplicate details"""
    log_id: str = Field(..., description="Log identifier")
    duplicate_details: List[DuplicateDetail] = Field(..., description="Detailed duplicate information")
    total_records: int = Field(..., description="Total number of duplicate records")


# Storage and Process Metadata Models
class StorageRecord(BaseModel):
    """Model for storage metadata record"""
    log_id: str = Field(..., description="Storage log identifier")
    table_name: str = Field(..., description="Name of the table")
    process_name: str = Field(..., description="Name of the process")
    stage: int = Field(..., description="Process stage")
    records_stored: int = Field(..., description="Number of records stored")
    storage_path: str = Field(..., description="Path where data is stored")
    created_at: datetime = Field(..., description="When the record was created")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class FieldLineage(BaseModel):
    """Model for field lineage information"""
    field_name: str = Field(..., description="Name of the field")
    source_table: str = Field(..., description="Source table name")
    target_table: str = Field(..., description="Target table name")
    transformation: Optional[str] = Field(None, description="Transformation applied")
    lineage_path: List[str] = Field(..., description="Full lineage path")


class ProcessRecord(BaseModel):
    """Model for process metadata record"""
    log_id: str = Field(..., description="Process log identifier")
    process_name: str = Field(..., description="Name of the process")
    stage: int = Field(0, description="Process stage (default 0)")
    status: str = Field(..., description="Process status")
    started_at: datetime = Field(..., description="When the process started")
    completed_at: Optional[datetime] = Field(None, description="When the process completed")
    records_processed: int = Field(..., description="Number of records processed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional process metadata")


class StorageMetadataRequest(BaseModel):
    """Request model for storage metadata analysis"""
    table_name: Optional[str] = Field(None, description="Filter by table name")
    process_name: Optional[str] = Field(None, description="Filter by process name")
    stage: int = Field(0, description="Filter by stage (default 0)")
    start_date: Optional[str] = Field(None, description="Start date filter (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date filter (YYYY-MM-DD)")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        """Validate date format"""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class StorageMetadataResponse(BaseModel):
    """Response model for storage metadata analysis"""
    storage_records: List[StorageRecord] = Field(..., description="List of storage records")
    total_records: int = Field(..., description="Total number of records")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied")


class FieldLineageResponse(BaseModel):
    """Response model for field lineage analysis"""
    log_id: str = Field(..., description="Storage log identifier")
    field_lineages: List[FieldLineage] = Field(..., description="Field lineage information")
    total_fields: int = Field(..., description="Total number of fields")


class ProcessMetadataRequest(BaseModel):
    """Request model for process metadata analysis"""
    process_name: Optional[str] = Field(None, description="Filter by process name")
    stage: int = Field(0, description="Filter by stage (default 0)")
    start_date: Optional[str] = Field(None, description="Start date filter (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date filter (YYYY-MM-DD)")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        """Validate date format"""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class ProcessMetadataResponse(BaseModel):
    """Response model for process metadata analysis"""
    process_records: List[ProcessRecord] = Field(..., description="List of process records")
    total_records: int = Field(..., description="Total number of records")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied")


# Basic Analysis Models
class KnownEntitiesResponse(BaseModel):
    """Response model for known entities query"""
    entities: List[Dict[str, Any]] = Field(..., description="List of known entities")
    total_entities: int = Field(..., description="Total number of entities")
    entity_types: List[str] = Field(..., description="Types of entities found")


class KnownEntityDetailResponse(BaseModel):
    """Response model for detailed entity information"""
    name: str = Field(..., description="Entity identifier")
    type: str = Field(..., description="Entity type")
    data: List[Dict[str, Any]] = Field(..., description="Content of the entity file")
    total_records: int = Field(..., description="Total number of records in the entity")


class DailyEntriesRequest(BaseModel):
    """Request model for daily entries analysis"""
    publication: str = Field(..., description="Publication identifier")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        """Validate date format"""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
                return v
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class DailyEntriesResponse(BaseModel):
    """Response model for daily entries analysis"""
    publication: str = Field(..., description="Publication analyzed")
    daily_counts: List[Dict[str, Any]] = Field(..., description="Daily entry counts")
    total_entries: int = Field(..., description="Total entries in the period")
    date_range: Dict[str, str] = Field(..., description="Date range analyzed")