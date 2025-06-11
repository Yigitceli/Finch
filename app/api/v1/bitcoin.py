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
from app.core.logging import setup_logging

router = APIRouter()
logger = setup_logging("bitcoin_api")

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
        logger.info("Fetching current Bitcoin price")
        price = await bitcoin_service.get_current_price(db)
        logger.info(f"Successfully fetched Bitcoin price: ${price:,.2f}")
        return BitcoinPriceResponse(price=price)
    except CoinGeckoError as e:
        logger.error(f"CoinGecko API error: {str(e)}")
        # Re-raise CoinGecko errors as they are already HTTPExceptions
        raise e
    except Exception as e:
        logger.error(f"Unexpected error while fetching Bitcoin price: {str(e)}", exc_info=True)
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
        logger.info(f"Fetching Bitcoin price history from {start_time} to {end_time}")
        
        if end_time < start_time:
            logger.warning(f"Invalid time range: end_time ({end_time}) is before start_time ({start_time})")
            raise HTTPException(
                status_code=400,
                detail="End time must be after start time"
            )
            
        prices = await bitcoin_service.get_historical_prices(db, start_time, end_time)
        logger.info(f"Successfully fetched {len(prices)} historical Bitcoin prices")
        return BitcoinPriceHistoryResponse(prices=prices)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while fetching Bitcoin price history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        ) 