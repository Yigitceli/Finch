from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify service status
    """
    return {
        "status": "healthy",
        "service": "finch-crypto-price-service",
        "version": "1.0.0"
    } 