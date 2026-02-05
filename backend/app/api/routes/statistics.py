"""
API routes for statistics and data analysis
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException

from app.services.portada_service import portada_service
from app.core.exceptions import PortAdaBaseException

router = APIRouter()


@router.get("/daily-ingestion-summary", response_model=List[Dict[str, Any]])
async def get_daily_ingestion_summary(
    newspaper: str = Query(..., description="Newspaper identifier (e.g., 'db', 'dm')"),
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
):
    """
    Get a summary of daily ingestion counts with subtotals for years, months, and days.
    """
    try:
        summary = await portada_service.get_daily_ingestion_summary(
            newspaper=newspaper,
            start_date=start_date,
            end_date=end_date,
        )
        return summary
    except PortAdaBaseException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
