from datetime import datetime
from pydantic import BaseModel

class BitcoinPriceResponse(BaseModel):
    price: float

class BitcoinPriceCreate(BaseModel):
    price_usd: float
    timestamp: datetime
    source: str 