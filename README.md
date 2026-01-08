# PortAda Data Ingestion & Analysis Platform

A full-stack application for data ingestion and analysis using the PortAda library, built with FastAPI (backend) and React TypeScript (frontend).

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start development environment
./docker-run.sh dev

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### Option 2: Local Development

#### Backend
```bash
cd backend
./start.sh
```

#### Frontend
```bash
cd frontend
bun install
bun run dev
```

## 📋 Features

### Data Ingestion
- **Extraction Data**: Upload and process JSON files from data extractors
- **Known Entities**: Upload and manage YAML entity files
- **Asynchronous Processing**: Background task processing with status tracking
- **File Validation**: Comprehensive input validation and error handling

### Analysis Queries
- **Missing Dates**: Find gaps in publication data by date ranges
- **Duplicates**: Identify and analyze duplicate records with detailed views
- **Storage Metadata**: Track field lineage and storage information
- **Process Metadata**: Monitor execution history and error details

### UI/UX
- **Modern Interface**: Clean, responsive design with dark theme
- **Real-time Updates**: Live status tracking and progress indicators
- **Intuitive Navigation**: Sidebar with dropdown menus for easy access
- **Error Handling**: Comprehensive error messages and recovery options

## 🛠 Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **UV**: Fast Python package manager
- **Pydantic**: Data validation and settings management
- **Uvicorn**: ASGI server for production deployment

### Frontend
- **React 18**: Modern React with TypeScript
- **Vite**: Fast build tool and development server
- **Bun**: Fast JavaScript runtime and package manager
- **Tailwind CSS**: Utility-first CSS framework

### Infrastructure
- **Docker**: Containerization for consistent environments
- **Docker Compose**: Multi-container orchestration
- **Health Checks**: Service monitoring and reliability

## 📁 Project Structure

```
├── frontend/              # React TypeScript application
│   ├── src/
│   │   ├── views/         # Analysis and ingestion screens
│   │   ├── services/      # API integration layer
│   │   ├── components/    # Reusable UI components
│   │   └── types/         # TypeScript type definitions
│   └── Dockerfile
├── backend/               # FastAPI Python application
│   ├── app/
│   │   ├── api/routes/    # API endpoints
│   │   ├── services/      # Business logic & PortAda integration
│   │   ├── models/        # Pydantic models
│   │   └── core/          # Configuration
│   ├── pyproject.toml     # UV dependencies
│   └── Dockerfile
├── docker-compose.yml     # Production setup
├── docker-compose.dev.yml # Development setup
└── docker-run.sh          # Docker management script
```

## 🔧 Development

### Prerequisites
- **Docker & Docker Compose** (for containerized development)
- **UV** (for local Python development)
- **Bun** (for local frontend development)

### Docker Commands
```bash
./docker-run.sh dev     # Start development environment
./docker-run.sh prod    # Start production environment
./docker-run.sh stop    # Stop all services
./docker-run.sh logs    # Show logs
./docker-run.sh clean   # Clean up containers and volumes
./docker-run.sh build   # Build all images
```

### Local Development
```bash
# Backend
cd backend
uv sync --no-build
uv run python main.py

# Frontend
cd frontend
bun install
bun run dev
```

## 🔌 PortAda Integration

The backend is **ready for PortAda library integration**. All integration points are prepared in `backend/app/services/portada_service.py` with mock implementations that need to be replaced with actual PortAda library calls.

### Integration Steps
1. Install the PortAda library in the backend environment
2. Replace mock implementations in `portada_service.py`
3. Update configuration with your data paths
4. Test with real data files

See `INTEGRATION_GUIDE.md` for detailed integration instructions.

## 📊 API Endpoints

### Ingestion
- `POST /api/ingestion/upload` - Upload files for processing
- `GET /api/ingestion/status/{task_id}` - Check processing status

### Analysis
- `POST /api/analysis/missing-dates` - Query missing publication dates
- `POST /api/analysis/duplicates` - Find duplicate records
- `POST /api/analysis/storage-metadata` - Get storage metadata
- `POST /api/analysis/process-metadata` - Get process execution data

### Documentation
- `GET /api/docs` - Swagger UI documentation
- `GET /api/redoc` - ReDoc documentation
- `GET /api/health` - Health check endpoint

## 🎯 Next Steps

1. **Install PortAda Library**: Follow your specific installation instructions
2. **Replace Mock Implementations**: Update `portada_service.py` with actual library calls
3. **Configure Data Paths**: Set up your actual data lake paths in `.env`
4. **Test with Real Data**: Use your actual JSON/YAML files
5. **Deploy**: Configure for your production environment

## 📞 Support

The implementation follows the exact specifications from your rectification document and is ready for PortAda library integration. All UI improvements and analysis features have been implemented according to your requirements.

Ready to integrate with your PortAda library! 🚀