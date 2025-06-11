from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.redis import redis_client
from app.db.session import get_db
from app.schemas.health import HealthResponse, ServiceHealth

router = APIRouter(tags=["health"])

@router.get("", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Check the health of all services.
    
    Returns:
        HealthResponse: Status of all services
    """
    # Check PostgreSQL
    postgres_health = await check_postgres(db)
    
    # Check Redis
    redis_health = check_redis()
    
    # Overall health
    is_healthy = postgres_health.is_healthy and redis_health.is_healthy
    
    return HealthResponse(
        is_healthy=is_healthy,
        services={
            "postgres": postgres_health,
            "redis": redis_health
        }
    )

@router.get("/postgres", response_model=ServiceHealth)
async def check_postgres(db: AsyncSession = Depends(get_db)) -> ServiceHealth:
    """
    Check PostgreSQL connection health.
    
    Returns:
        ServiceHealth: PostgreSQL service health status
    """
    try:
        # Try to execute a simple query
        await db.execute(text("SELECT 1"))
        return ServiceHealth(
            is_healthy=True,
            message="PostgreSQL is healthy"
        )
    except Exception as e:
        return ServiceHealth(
            is_healthy=False,
            message=f"PostgreSQL health check failed: {str(e)}"
        )

@router.get("/redis", response_model=ServiceHealth)
def check_redis() -> ServiceHealth:
    """
    Check Redis connection health.
    
    Returns:
        ServiceHealth: Redis service health status
    """
    try:
        is_healthy = redis_client.is_healthy()
        return ServiceHealth(
            is_healthy=is_healthy,
            message="Redis is healthy" if is_healthy else "Redis is not healthy"
        )
    except Exception as e:
        return ServiceHealth(
            is_healthy=False,
            message=f"Redis health check failed: {str(e)}"
        ) 