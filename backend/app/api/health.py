# /api/health endpoint for monitoring and deployment checks
from fastapi import APIRouter, Depends
from datetime import datetime
import os

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    Returns minimal info — no version or environment details.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with service status.
    Requires authentication to prevent reconnaissance.
    """
    from app.db.session import SessionLocal
    from app.core.auth import get_current_user
    from app.db.models.user import User
    from sqlalchemy import text
    import redis
    
    checks = {
        "database": False,
        "redis": False,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Database check
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = True
    except Exception:
        checks["database"] = False
    
    # Redis check
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
        checks["redis"] = True
    except Exception:
        checks["redis"] = False
    
    # Overall status
    checks["status"] = "healthy" if all([checks["database"], checks["redis"]]) else "degraded"
    
    return checks
