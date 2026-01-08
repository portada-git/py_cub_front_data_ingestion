"""
Pydantic models for ingestion endpoints
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

class IngestionType(str, Enum):
    """Types of ingestion supported"""
    EXTRACTION = "extraction"
    KNOWN_ENTITIES = "known_entities"

class IngestionRequest(BaseModel):
    """Request model for data ingestion"""
    ingestion_type: IngestionType
    filename: str
    file_size: int

class IngestionResponse(BaseModel):
    """Response model for data ingestion"""
    success: bool
    message: str
    task_id: Optional[str] = None
    records_processed: Optional[int] = None

class IngestionStatus(BaseModel):
    """Status of an ingestion task"""
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: Optional[int] = None
    message: Optional[str] = None
    records_processed: Optional[int] = None
    error_details: Optional[str] = None