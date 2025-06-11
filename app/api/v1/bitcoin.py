from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.schemas.bitcoin import BitcoinPriceResponse, BitcoinPriceHistoryResponse
from app.services.bitcoin import bitcoin_service

router = APIRouter()

@router.get("/current-price", response_model=BitcoinPriceResponse)
async def get_price(db: AsyncSession = Depends(get_db)):
    """
    Get current Bitcoin price.
    
    Returns:
        BitcoinPriceResponse: Current Bitcoin price in USD
    """
    try:
        price = await bitcoin_service.get_current_price(db)
        return BitcoinPriceResponse(price=price)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/price-history", response_model=BitcoinPriceHistoryResponse)
async def get_price_history(
    start_time: datetime = Query(..., description="Start time in ISO format (e.g., 2024-01-01T00:00:00Z)"),
    end_time: datetime = Query(..., description="End time in ISO format (e.g., 2024-01-02T00:00:00Z)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Bitcoin price history within a time range.
    
    Args:
        start_time: Start of time range
        end_time: End of time range
        
    Returns:
        BitcoinPriceHistoryResponse: List of Bitcoin prices with timestamps
    """
    try:
        if end_time < start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        if (end_time - start_time).total_seconds() > 90 * 24 * 3600:  # 90 days
            raise HTTPException(status_code=400, detail="Time range cannot exceed 90 days")
        
        prices = await bitcoin_service.get_historical_prices(db, start_time, end_time)
        return BitcoinPriceHistoryResponse(prices=prices)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 