from fastapi import APIRouter
from app.api.v1 import bitcoin, health

api_router = APIRouter()

api_router.include_router(bitcoin.router, prefix="/bitcoin", tags=["bitcoin"])
api_router.include_router(health.router, prefix="/health", tags=["health"]) 