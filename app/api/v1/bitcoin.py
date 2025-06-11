from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.schemas.bitcoin import BitcoinPriceResponse, BitcoinPriceHistoryResponse
from app.services.bitcoin import bitcoin_service
from app.core.exceptions import (
    CoinGeckoError,
    CoinGeckoRateLimitError,
    CoinGeckoNetworkError,
    CoinGeckoInvalidResponseError,
    CoinGeckoUnknownSymbolError
)

router = APIRouter()

@router.get("/current-price", response_model=BitcoinPriceResponse)
async def get_price(db: AsyncSession = Depends(get_db)):
    """
    Get current Bitcoin price.
    
    Returns:
        BitcoinPriceResponse: Current Bitcoin price in USD
        
    Raises:
        HTTPException: Various HTTP errors based on CoinGecko API response
    """
    try:
        price = await bitcoin_service.get_current_price(db)
        return BitcoinPriceResponse(price=price)
    except CoinGeckoError as e:
        # Re-raise CoinGecko errors as they are already HTTPExceptions
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

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
        
    Raises:
        HTTPException: Various HTTP errors based on input validation or database errors
    """
    try:
        if end_time < start_time:
            raise HTTPException(
                status_code=400,
                detail="End time must be after start time"
            )
        prices = await bitcoin_service.get_historical_prices(db, start_time, end_time)
        return BitcoinPriceHistoryResponse(prices=prices)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        ) 