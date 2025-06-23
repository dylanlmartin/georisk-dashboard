from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import redis.asyncio as redis
from datetime import datetime
import os

from ...database import get_db
from ...models import Country, RiskScoreV2
from ...core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["health"])

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive health check endpoint
    Tests database connectivity, data availability, and system status
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0",
        "checks": {}
    }
    
    overall_healthy = True
    
    # Database connectivity check
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        overall_healthy = False
    
    # Data availability check
    try:
        # Check if we have countries
        country_count = await db.execute(select(Country).limit(1))
        countries_exist = country_count.scalar_one_or_none() is not None
        
        if countries_exist:
            # Check for recent risk scores
            recent_scores = await db.execute(
                select(RiskScoreV2)
                .order_by(RiskScoreV2.created_at.desc())
                .limit(1)
            )
            latest_score = recent_scores.scalar_one_or_none()
            
            if latest_score:
                health_status["checks"]["data"] = {
                    "status": "healthy",
                    "message": f"Data available, latest score from {latest_score.score_date}",
                    "latest_score_date": latest_score.score_date.isoformat()
                }
            else:
                health_status["checks"]["data"] = {
                    "status": "warning",
                    "message": "Countries exist but no risk scores found"
                }
        else:
            health_status["checks"]["data"] = {
                "status": "unhealthy",
                "message": "No country data found"
            }
            overall_healthy = False
            
    except Exception as e:
        health_status["checks"]["data"] = {
            "status": "unhealthy",
            "message": f"Data check failed: {str(e)}"
        }
        overall_healthy = False
    
    # Redis connectivity check (optional)
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()
        await redis_client.close()
        
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "warning",
            "message": f"Redis connection failed: {str(e)}"
        }
        # Redis failure is not critical for basic operation
    
    # Environment check
    try:
        required_env_vars = ["DATABASE_URL"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            health_status["checks"]["environment"] = {
                "status": "unhealthy",
                "message": f"Missing environment variables: {', '.join(missing_vars)}"
            }
            overall_healthy = False
        else:
            health_status["checks"]["environment"] = {
                "status": "healthy",
                "message": "Required environment variables present"
            }
    except Exception as e:
        health_status["checks"]["environment"] = {
            "status": "unhealthy",
            "message": f"Environment check failed: {str(e)}"
        }
        overall_healthy = False
    
    # Update overall status
    if not overall_healthy:
        health_status["status"] = "unhealthy"
    
    # Return appropriate HTTP status
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@router.get("/health/simple")
async def simple_health_check():
    """Simple health check for load balancers"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}