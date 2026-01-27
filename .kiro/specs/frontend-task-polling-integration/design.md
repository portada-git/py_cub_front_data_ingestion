# Design Document: Frontend Task Status Polling Integration

## Overview

This design addresses the integration of an enhanced upload system into existing ingestion endpoints to resolve frontend task status polling issues. The solution creates a unified system that preserves all enhanced functionality while maintaining complete backward compatibility with existing frontend code.

The core challenge is that the frontend expects responses in `IngestionResponse` and `IngestionStatusResponse` formats from `/ingestion/upload` and `/ingestion/status/{task_id}` endpoints, but the enhanced system uses different response formats and endpoints. The solution involves creating an adapter layer that bridges these systems while leveraging all enhanced capabilities.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    Frontend[Frontend Client] --> |POST /ingestion/upload| UnifiedIngestion[Unified Ingestion Controller]
    Frontend --> |GET /ingestion/status/{task_id}| UnifiedIngestion
    
    UnifiedIngestion --> |delegates to| EnhancedSystem[Enhanced Upload System]
    UnifiedIngestion --> |adapts responses| ResponseAdapter[Response Adapter]
    
    EnhancedSystem --> StorageService[Storage Service]
    EnhancedSystem --> DatabaseService[Database Service]
    EnhancedSystem --> SessionManager[Session Manager]
    EnhancedSystem --> ConcurrentUploadManager[Concurrent Upload Manager]
    EnhancedSystem --> EntityValidator[Entity Validator]
    
    ResponseAdapter --> |transforms| IngestionModels[Ingestion Response Models]
    
    subgraph "Legacy Components (Deprecated)"
        LegacyTaskService[Task Service]
        LegacyFileService[File Service]
        LegacyPortadaService[Portada Service]
    end
    
    UnifiedIngestion -.-> |migrates from| LegacyTaskService
```

### Component Integration Strategy

The integration follows a **Facade Pattern** where the unified ingestion controller acts as a facade over the enhanced system, providing the original API contract while leveraging enhanced functionality internally.

## Components and Interfaces

### 1. Unified Ingestion Controller

**Purpose**: Primary integration component that maintains original API contracts while delegating to enhanced system.

**Key Responsibilities**:
- Receive requests at original endpoints (`/ingestion/upload`, `/ingestion/status/{task_id}`)
- Validate and transform requests for enhanced system compatibility
- Delegate processing to enhanced upload system
- Transform enhanced system responses to match expected formats
- Maintain backward compatibility for all existing functionality

**Interface**:
```python
class UnifiedIngestionController:
    async def upload_data(
        self, 
        file: UploadFile, 
        ingestion_type: IngestionType,
        publication: Optional[str] = None,
        entity_name: Optional[str] = None,
        data_path_delta_lake: Optional[str] = None,
        current_user: dict = None
    ) -> IngestionResponse
    
    async def get_ingestion_status(
        self, 
        task_id: str, 
        current_user: dict = None
    ) -> IngestionStatusResponse
```

### 2. Enhanced System Adapter

**Purpose**: Adapter layer that bridges enhanced system capabilities with legacy interfaces.

**Key Responsibilities**:
- Transform enhanced system requests/responses to match legacy formats
- Map enhanced system task IDs to legacy task ID format
- Provide unified task state management across both systems
- Handle response format conversion

**Interface**:
```python
class EnhancedSystemAdapter:
    async def submit_upload_request(
        self, 
        request: IngestionRequest, 
        file: UploadFile, 
        session_id: str,
        user_context: dict
    ) -> Tuple[str, Dict[str, Any]]  # Returns (task_id, enhanced_response)
    
    async def get_task_status(
        self, 
        task_id: str
    ) -> Optional[Dict[str, Any]]
    
    def transform_to_ingestion_response(
        self, 
        enhanced_response: Dict[str, Any], 
        file_validation: FileValidation
    ) -> IngestionResponse
    
    def transform_to_status_response(
        self, 
        enhanced_status: Dict[str, Any]
    ) -> IngestionStatusResponse
```

### 3. Task ID Mapping Service

**Purpose**: Manages mapping between legacy task IDs and enhanced system task IDs to ensure continuity.

**Key Responsibilities**:
- Generate legacy-compatible task IDs
- Maintain bidirectional mapping between legacy and enhanced task IDs
- Handle task ID resolution for status queries
- Provide migration path for existing task IDs

**Interface**:
```python
class TaskIdMappingService:
    def create_legacy_task_id(self, enhanced_task_id: str) -> str
    def get_enhanced_task_id(self, legacy_task_id: str) -> Optional[str]
    def register_task_mapping(self, legacy_id: str, enhanced_id: str) -> None
    async def migrate_existing_tasks(self) -> Dict[str, int]
```

### 4. Response Format Adapter

**Purpose**: Transforms enhanced system responses to match expected legacy response formats.

**Key Responsibilities**:
- Convert enhanced upload responses to `IngestionResponse` format
- Transform enhanced status responses to `IngestionStatusResponse` format
- Preserve all required fields and maintain data integrity
- Handle error response format conversion

**Interface**:
```python
class ResponseFormatAdapter:
    def adapt_upload_response(
        self, 
        enhanced_response: Dict[str, Any], 
        task_id: str,
        file_validation: Optional[FileValidation] = None
    ) -> IngestionResponse
    
    def adapt_status_response(
        self, 
        enhanced_status: Dict[str, Any], 
        task_id: str
    ) -> IngestionStatusResponse
    
    def extract_file_validation(
        self, 
        enhanced_response: Dict[str, Any]
    ) -> Optional[FileValidation]
```

### 5. Session Bridge Service

**Purpose**: Manages session integration between frontend requests and enhanced system session management.

**Key Responsibilities**:
- Create or retrieve sessions for frontend requests
- Bridge session context between systems
- Handle session lifecycle management
- Provide session-based task tracking

**Interface**:
```python
class SessionBridgeService:
    async def get_or_create_session(
        self, 
        request: Request, 
        response: Response, 
        user_context: dict
    ) -> str
    
    async def associate_task_with_session(
        self, 
        session_id: str, 
        task_id: str, 
        metadata: Dict[str, Any]
    ) -> None
```

## Data Models

### Task Mapping Model

```python
@dataclass
class TaskMapping:
    legacy_task_id: str
    enhanced_task_id: str
    created_at: datetime
    user_id: str
    ingestion_type: str
    status: str
    metadata: Dict[str, Any]
```

### Enhanced Response Wrapper

```python
@dataclass
class EnhancedResponseWrapper:
    success: bool
    task_id: str
    enhanced_task_id: str
    session_id: str
    status: str
    message: str
    file_info: Dict[str, Any]
    processing_info: Dict[str, Any]
    timestamp: str
    error_details: Optional[Dict[str, Any]] = None
```

### Status Mapping Configuration

```python
@dataclass
class StatusMappingConfig:
    enhanced_status_map: Dict[str, IngestionStatus] = field(default_factory=lambda: {
        "queued": IngestionStatus.PENDING,
        "processing": IngestionStatus.PROCESSING,
        "completed": IngestionStatus.COMPLETED,
        "failed": IngestionStatus.FAILED,
        "cancelled": IngestionStatus.FAILED
    })
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the prework analysis, the following properties ensure the unified system maintains compatibility while leveraging enhanced functionality:

### Property 1: Enhanced System Component Integration
*For any* upload request processed through `/ingestion/upload`, the unified system should utilize all enhanced system components (StorageService, DatabaseService, SessionManager, ConcurrentUploadManager, EntityValidator) for processing
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

### Property 2: Response Format Compliance
*For any* upload or status request, the unified system should return responses that conform exactly to the expected IngestionResponse or IngestionStatusResponse schemas with all required fields present
**Validates: Requirements 1.2, 5.1, 5.2, 5.4, 5.5**

### Property 3: Response Format Transformation
*For any* enhanced system response, the unified system should successfully transform it to match the expected legacy response format while preserving all essential information
**Validates: Requirements 5.3**

### Property 4: Task ID Mapping Consistency
*For any* task created through the unified system, querying the task status should return consistent information regardless of whether the task ID is legacy or enhanced format
**Validates: Requirements 3.4, 6.2, 6.3**

### Property 5: Backward Compatibility Preservation
*For any* valid legacy task ID, file format, or API request, the unified system should process it correctly and return responses in the expected legacy format
**Validates: Requirements 1.3, 4.1, 4.2, 4.3, 4.4**

### Property 6: Unique Task Identifier Generation
*For any* set of tasks created through the unified system, all task identifiers should be unique across both legacy and enhanced formats
**Validates: Requirements 6.1**

### Property 7: Enhanced Error Handling Integration
*For any* error condition (upload errors, validation failures, client errors), the unified system should use enhanced error handling capabilities while returning error responses in expected legacy formats with appropriate HTTP status codes
**Validates: Requirements 2.6, 7.1, 7.2, 7.3, 7.4, 7.5**

### Property 8: Concurrent Processing Integration
*For any* set of simultaneous upload requests, the unified system should use ConcurrentUploadManager for processing while maintaining response format compatibility
**Validates: Requirements 8.1**

### Property 9: Task Management Unification
*For any* upload operation, the unified system should use a single task management system that maintains audit trails and provides consistent task status across all access methods
**Validates: Requirements 3.3, 6.4**

### Property 10: Schema Preservation Round Trip
*For any* valid IngestionRequest, processing it through the unified system and then querying its status should preserve all request information in the response metadata
**Validates: Requirements 1.5**

<function_calls>
<invoke name="prework">
<parameter name="featureName">frontend-task-polling-integration