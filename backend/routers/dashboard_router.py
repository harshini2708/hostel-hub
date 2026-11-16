from fastapi import APIRouter, Depends
from backend.database import db
from backend.auth import require_warden

router = APIRouter(prefix="/api/admin/dashboard", tags=["Admin Dashboard Analytics"])

@router.get("")
async def get_dashboard_analytics(warden: dict = Depends(require_warden)):
    """Warden only: get aggregated real-time analytics across all 6 modules."""
    return db.get_dashboard_analytics()
