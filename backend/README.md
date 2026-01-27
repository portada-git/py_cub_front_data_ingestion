# PortAda Backend API

FastAPI backend for the PortAda data ingestion and analysis system.

## Features

- **Data Ingestion**: Upload and process JSON/YAML files for extraction data and known entities
- **Analysis Queries**: 
  - Missing dates analysis
  - Duplicates detection and analysis
  - Storage metadata queries
  - Process metadata queries
- **Asynchronous Processing**: Background task processing for large files
- **PortAda Integration**: Integration with PortAda library for data lake operations

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install PortAda Library

Follow the instructions provided to install the PortAda library in your virtual environment.

### 3. Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# PortAda Configuration
PORTADA_BASE_PATH=/path/to/your/data/lake
PORTADA_APP_NAME=PortAdaAPI
PORTADA_PROJECT_NAME=portada_ingestion

# FastAPI Configuration
SECRET_KEY=your-secret-key-here
```

### 4. Run the Server

```bash
# Development mode
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### Data Ingestion
- `POST /api/ingestion/upload` - Upload and process files
- `GET /api/ingestion/status/{task_id}` - Get processing status

### Analysis
- `POST /api/analysis/missing-dates` - Query missing dates
- `POST /api/analysis/duplicates` - Query duplicates metadata
- `GET /api/analysis/duplicates/{log_id}/details` - Get duplicate details
- `POST /api/analysis/storage-metadata` - Query storage metadata
- `GET /api/analysis/storage-metadata/{log_id}/lineage` - Get field lineage
- `POST /api/analysis/process-metadata` - Query process metadata

## PortAda Integration

The backend integrates with the PortAda library through the `PortAdaService` class. Key integration points:

### Data Ingestion
```python
# Extraction data
layer_news.ingest(data_path_delta_lake, local_path=json_path)

# Known entities
layer_entities.copy_ingested_entities(entity=known_entity_delta_lake, ...)
layer_entities.save_raw_entities(entity=known_entity_delta_lake, data=odata)
```

### Analysis Queries
```python
# Missing dates
layer_news.get_missing_dates_from_a_newspaper(publication_name="db")

# Metadata queries
metadata = DataLakeMetadataManager(layer_news.get_configuration())
df_meta = metadata.read_log("process_log")
df_dup = metadata.read_log("duplicates_log")
df_storage = metadata.read_log("storage_log")
df_lineage = metadata.read_log("field_lineage_log")
```

## File Formats Supported

### Ingestion Files
- **JSON**: Standard JSON format for extraction data
- **YAML/YML**: YAML format for known entities and configuration

### Date/Edition Lists (Missing Dates Query)
- **YAML**: `1850-10-01: [U]` format
- **JSON**: `[{"1850-10-01":["U"]}]` format  
- **Plain Text**: One date per line format

## Development Notes

- The current implementation includes mock data for testing
- Replace mock implementations with actual PortAda library calls
- Add proper error handling and logging
- Implement authentication and authorization
- Add input validation and sanitization
- Consider using Redis for task storage in production