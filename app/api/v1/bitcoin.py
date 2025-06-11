from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.schemas.bitcoin import BitcoinPriceResponse
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
        price = await bitcoin_service.get_current_price()
        return BitcoinPriceResponse(price=price)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 