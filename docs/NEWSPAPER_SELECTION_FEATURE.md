# Newspaper Selection Feature - Implementation Summary

## Status: ✅ COMPLETED

## Overview
Added newspaper selection functionality to the data ingestion view, allowing users to specify which newspaper the extraction data belongs to. This organizes uploaded files by newspaper source in the data lake.

## Changes Made

### 1. Frontend Changes

#### Created: `frontend/src/data/newspapers.json`
- JSON file containing 6 historical newspapers
- Each newspaper has: id, name, code, and description
- Dynamically loaded into the ingestion view

#### Modified: `frontend/src/views/IngestionView.tsx`
- Added newspaper selector UI (only visible for "extraction" type)
- Added `selectedNewspaper` state management
- Updated button validation to require newspaper selection for extraction
- Replaced mock API call with real fetch to backend
- Added newspaper parameter to FormData when submitting
- Added form reset after successful submission

### 2. Backend Changes

#### Modified: `backend/app/api/routes/ingestion.py`
- Added `newspaper` parameter to upload endpoint (Optional[str])
- Added validation: newspaper is required for extraction type
- Updated background task to pass newspaper parameter
- Updated process_ingestion_task signature to accept newspaper

#### Modified: `backend/app/services/portada_service.py`
- Updated `ingest_extraction_data` method to accept newspaper parameter
- Modified destination path to include newspaper: `{data_path}/{newspaper}/`
- Updated success message to show full destination path

### 3. Documentation

#### Updated: `INTEGRATION_GUIDE.md`
- Added comprehensive newspaper selection feature documentation
- Included API examples with newspaper parameter
- Documented data flow and validation rules
- Instructions for adding new newspapers

## Features

### User Experience
1. User selects "Extracción" as ingestion type
2. Newspaper selector appears automatically
3. User selects newspaper from dropdown (shows name, code, description)
4. User uploads file
5. "Procesar Datos" button is disabled until newspaper is selected
6. On submit, data is sent to backend with newspaper identifier
7. Success message shows task ID for tracking

### Validation
- Frontend: Button disabled if extraction type and no newspaper selected
- Backend: Returns 400 error if extraction type without newspaper parameter
- File type validation: Only .json, .yml, .yaml files accepted

### Data Organization
Files are organized in the data lake as:
```
ship_entries/
├── db/          # Diario de Barcelona
├── dm/          # Diario de la Marina
├── sm/          # Semanario de Málaga
├── gaceta/      # Gaceta de Madrid
├── liberal/     # El Liberal
└── imparcial/   # El Imparcial
```

## Available Newspapers

| ID | Name | Code | Description |
|---|---|---|---|
| db | Diario de Barcelona | DB | Periódico histórico catalán |
| dm | Diario de la Marina | DM | Periódico histórico cubano |
| sm | Semanario de Málaga | SM | Publicación histórica andaluza |
| gaceta | Gaceta de Madrid | GM | Boletín oficial histórico |
| liberal | El Liberal | EL | Periódico histórico español |
| imparcial | El Imparcial | EI | Diario histórico madrileño |

## API Specification

### Endpoint: POST /api/ingestion/upload

**Parameters:**
- `file` (UploadFile, required): The file to upload
- `ingestion_type` (IngestionType, required): "extraction" or "known_entities"
- `newspaper` (string, optional): Newspaper identifier (required for extraction type)

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/ingestion/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data.json" \
  -F "ingestion_type=extraction" \
  -F "newspaper=dm"
```

**Response:**
```json
{
  "success": true,
  "message": "File uploaded successfully. Processing started in background.",
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Testing

### Manual Testing Steps
1. Start backend: `cd backend && ./start.sh`
2. Start frontend: `cd frontend && bun run dev`
3. Navigate to Ingestion view
4. Select "Extracción" type
5. Verify newspaper selector appears
6. Select a newspaper
7. Upload a JSON file
8. Click "Procesar Datos"
9. Verify success message with task ID

### Expected Behavior
- ✅ Newspaper selector only shows for extraction type
- ✅ Button disabled without newspaper selection
- ✅ Backend validates newspaper parameter
- ✅ Files organized by newspaper in data lake
- ✅ Form resets after successful submission

## Future Enhancements

### Potential Improvements
1. Add user tracking to newspaper selection (who uploaded what)
2. Add newspaper statistics in analysis view
3. Filter analysis queries by newspaper
4. Add newspaper metadata to ingestion status
5. Support bulk upload with different newspapers

### Adding New Newspapers
Edit `frontend/src/data/newspapers.json`:
```json
{
  "newspapers": [
    {
      "id": "new_paper",
      "name": "New Newspaper Name",
      "code": "NP",
      "description": "Description of the new newspaper"
    }
  ]
}
```

No backend changes required - newspapers are dynamically loaded.

## Files Modified

### Frontend
- ✅ `frontend/src/views/IngestionView.tsx` (modified)
- ✅ `frontend/src/data/newspapers.json` (created)

### Backend
- ✅ `backend/app/api/routes/ingestion.py` (modified)
- ✅ `backend/app/services/portada_service.py` (modified)

### Documentation
- ✅ `INTEGRATION_GUIDE.md` (updated)
- ✅ `docs/NEWSPAPER_SELECTION_FEATURE.md` (created)

## Completion Date
January 21, 2026

## Notes
- Implementation follows the user's requirement to organize data by newspaper source
- Newspaper selection is only required for extraction type, not for known entities
- The feature is fully integrated with the existing PortAda library integration
- All code passes diagnostics with no errors
