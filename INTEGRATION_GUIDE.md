# PortAda Integration Guide

## 📁 Project Structure

```
├── frontend/          # React TypeScript application
│   ├── src/
│   │   ├── views/     # Analysis and ingestion views
│   │   ├── services/  # API integration layer
│   │   └── ...
│   └── package.json
├── backend/           # FastAPI Python application
│   ├── app/
│   │   ├── api/routes/     # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── models/         # Pydantic models
│   │   └── core/           # Configuration
│   ├── main.py        # FastAPI app entry point
│   └── requirements.txt
└── docs/              # Documentation
```

## 🚀 Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install PortAda library (follow your specific instructions)
# pip install portada-builder  # or your specific installation method

# Configure environment
cp .env.example .env
# Edit .env with your PortAda configuration

# Start backend
python main.py
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
# or
bun install

# Start development server
npm run dev
# or
bun dev
```

## 🔧 PortAda Library Integration

### Current Implementation Status

The backend is **ready for PortAda integration** with placeholder implementations. Here's what needs to be replaced:

### 📍 Integration Points

#### 1. **PortAda Service** (`backend/app/services/portada_service.py`)

**Current**: Mock implementations
**Replace with**: Actual PortAda library calls

```python
# TODO: Replace these imports with actual PortAda library
from portada_builder import PortadaBuilder
from portada_metadata import DataLakeMetadataManager

class PortAdaService:
    def _get_builder(self):
        # Replace mock with actual implementation
        self._builder = (
            PortadaBuilder()
            .protocol("file://")
            .base_path(self.base_path)
            .app_name(self.app_name)
            .project_name(self.project_name)
        )
        return self._builder
    
    def _get_news_layer(self):
        # Replace mock with actual implementation
        builder = self._get_builder()
        self._layer_news = builder.build(builder.NEWS_TYPE)
        self._layer_news.start_session()
        return self._layer_news
    
    # ... etc for other methods
```

#### 2. **Data Ingestion Methods**

**Extraction Data**:
```python
async def ingest_extraction_data(self, file_path: str, data_path_delta_lake: str = "ship_entries"):
    layer_news = self._get_news_layer()
    # Replace mock with:
    layer_news.ingest(data_path_delta_lake, local_path=file_path)
```

**Known Entities**:
```python
async def ingest_known_entities(self, file_path: str, entity_name: str = "known_entities"):
    layer_entities = self._get_entities_layer()
    # Replace mock with:
    data, dest = layer_entities.copy_ingested_entities(entity=entity_name, ...)
    odata = {"source_path": dest, "data": data}
    layer_entities.save_raw_entities(entity=entity_name, data=odata)
```

#### 3. **Analysis Methods**

**Missing Dates**:
```python
async def get_missing_dates(self, publication_name: str, ...):
    layer_news = self._get_news_layer()
    # Replace mock with:
    missing_dates = layer_news.get_missing_dates_from_a_newspaper(
        publication_name=publication_name,
        start_date=start_date,
        end_date=end_date
    )
```

**Metadata Queries**:
```python
async def get_duplicates_metadata(self, ...):
    metadata = self._get_metadata_manager()
    # Replace mock with:
    df_dup_md = metadata.read_log("duplicates_log")
    # Apply filters as specified in your example
```

## 📋 Implemented Features

### ✅ Frontend (React TypeScript)

1. **Ingestion Interface**
   - Dropdown selection: Extraction vs Known Entities
   - Single file upload with validation
   - Asynchronous processing feedback
   - Progress tracking and status updates

2. **Analysis Interfaces**
   - **Missing Dates**: File upload or date range query
   - **Duplicates**: Master-detail view with expandable rows
   - **Storage Metadata**: Field lineage tracking
   - **Process Metadata**: Execution history and error details

3. **UI/UX Features**
   - Responsive design with dark theme
   - Loading states and error handling
   - Sidebar navigation with dropdown
   - Real-time status updates

### ✅ Backend (FastAPI)

1. **API Endpoints**
   - `POST /api/ingestion/upload` - File upload with background processing
   - `GET /api/ingestion/status/{task_id}` - Processing status
   - `POST /api/analysis/missing-dates` - Missing dates query
   - `POST /api/analysis/duplicates` - Duplicates analysis
   - `POST /api/analysis/storage-metadata` - Storage metadata
   - `POST /api/analysis/process-metadata` - Process metadata

2. **Features**
   - Async file processing with task tracking
   - Comprehensive error handling
   - Input validation and sanitization
   - CORS configuration for frontend
   - Auto-generated API documentation

## 🔄 Integration Steps

### Step 1: Install PortAda Library
```bash
cd backend
source venv/bin/activate
# Follow your specific PortAda installation instructions
```

### Step 2: Update Imports
Replace mock imports in `backend/app/services/portada_service.py`:
```python
# Replace these lines:
# from portada_builder import PortadaBuilder
# from portada_metadata import DataLakeMetadataManager

# With actual imports based on your library structure
```

### Step 3: Replace Mock Methods
Go through each method in `PortAdaService` and replace mock implementations with actual PortAda calls.

### Step 4: Test Integration
```bash
# Start backend
cd backend && python main.py

# Start frontend  
cd frontend && npm run dev

# Test file upload and analysis queries
```

### Step 5: Configure Data Paths
Update `.env` files with your actual data lake paths:
```env
PORTADA_BASE_PATH=/your/actual/data/path
PORTADA_PROJECT_NAME=your_project_name
```

## 📊 API Examples

### Upload File
```bash
curl -X POST "http://localhost:8000/api/ingestion/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_data.json" \
  -F "ingestion_type=extraction"
```

### Query Missing Dates
```bash
curl -X POST "http://localhost:8000/api/analysis/missing-dates" \
  -H "Content-Type: application/json" \
  -d '{
    "publication_name": "db",
    "query_mode": "date_range",
    "start_date": "1850-01-01",
    "end_date": "1850-12-31"
  }'
```

## 🎯 Next Steps

1. **Install PortAda Library**: Follow your specific installation instructions
2. **Replace Mock Implementations**: Update `portada_service.py` with actual library calls
3. **Test with Real Data**: Use your actual JSON/YAML files
4. **Configure Production**: Set up proper authentication, logging, and error handling
5. **Deploy**: Configure for your production environment

## 📞 Support

The implementation follows the exact specifications from your rectification document:
- ✅ Separated ingestion processes (dropdown selection)
- ✅ Simplified upload responses (asynchronous processing)
- ✅ Analysis dropdown with 4 query types
- ✅ Individual query definition screens
- ✅ Master-detail views with proper filtering
- ✅ All PortAda integration points prepared

Ready for your PortAda library integration! 🚀