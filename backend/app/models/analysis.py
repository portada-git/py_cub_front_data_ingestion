"""
Pydantic models for analysis endpoints
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Missing Dates Models
class MissingDatesRequest(BaseModel):
    """Request model for missing dates query"""
    publication_name: str
    query_mode: str  # "file" or "date_range"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    date_and_edition_list: Optional[str] = None  # For file mode

class MissingDateEntry(BaseModel):
    """Single missing date entry"""
    date: str
    edition: str
    gap_duration: Optional[str] = None

class MissingDatesResponse(BaseModel):
    """Response model for missing dates query"""
    success: bool
    publication_name: str
    missing_dates: List[MissingDateEntry]
    total_missing: int

# Duplicates Models
class DuplicatesRequest(BaseModel):
    """Request model for duplicates query"""
    user_responsible: Optional[str] = None
    publication: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class DuplicateRecord(BaseModel):
    """Duplicate record metadata"""
    log_id: str
    date: str
    edition: str
    publication: str
    uploaded_by: str
    duplicate_count: int
    duplicates_filter: str
    duplicate_ids: List[str]

class DuplicateDetail(BaseModel):
    """Detailed duplicate record"""
    entry_id: str
    content: str
    similarity_score: Optional[float] = None

class DuplicatesResponse(BaseModel):
    """Response model for duplicates query"""
    success: bool
    duplicates_metadata: List[DuplicateRecord]
    total_records: int

# Storage Metadata Models
class StorageMetadataRequest(BaseModel):
    """Request model for storage metadata query"""
    table_name: Optional[str] = None
    process: Optional[str] = None

class StorageRecord(BaseModel):
    """Storage metadata record"""
    log_id: str
    table_name: str
    process: str
    timestamp: datetime
    record_count: int
    stage: int

class FieldLineage(BaseModel):
    """Field lineage information"""
    field_name: str
    operation: str
    old_value: str
    new_value: str
    timestamp: datetime

class StorageMetadataResponse(BaseModel):
    """Response model for storage metadata query"""
    success: bool
    storage_records: List[StorageRecord]
    total_records: int

# Process Metadata Models
class ProcessMetadataRequest(BaseModel):
    """Request model for process metadata query"""
    process_name: Optional[str] = None

class ProcessRecord(BaseModel):
    """Process execution record"""
    log_id: str
    process: str
    timestamp: datetime
    duration: Optional[float] = None
    status: str
    records_processed: int
    stage: int
    error_message: Optional[str] = None

class ProcessMetadataResponse(BaseModel):
    """Response model for process metadata query"""
    success: bool
    process_records: List[ProcessRecord]
    total_records: int