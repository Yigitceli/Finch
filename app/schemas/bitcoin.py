from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

class BitcoinPriceBase(BaseModel):
    """Base model for Bitcoin price data."""
    price_usd: float = Field(..., description="Price in USD")
    timestamp: datetime = Field(..., description="Timestamp of the price")
    source: str = Field(..., description="Source of the price data")

    model_config = {
        "from_attributes": True
    }

class BitcoinPriceCreate(BitcoinPriceBase):
    """Model for creating a new Bitcoin price record."""
    pass

class BitcoinPriceResponse(BaseModel):
    """Response model for current Bitcoin price."""
    price: float = Field(..., description="Current Bitcoin price in USD")

class BitcoinPriceHistoryResponse(BaseModel):
    """Response model for Bitcoin price history."""
    prices: List[BitcoinPriceBase] = Field(..., description="List of Bitcoin prices with timestamps") 