from datetime import datetime, timedelta, timezone
from typing import Optional, List
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import get_settings
from app.core.cache import cache, invalidate_cache
from app.models.bitcoin import BitcoinPrice
from app.schemas.bitcoin import BitcoinPriceCreate, BitcoinPriceBase

settings = get_settings()

class BitcoinService:
    def __init__(self):
        self.base_url = settings.COINGECKO_API_URL
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Finch/1.0"
        }
        self.current_price_ttl = settings.CURRENT_PRICE_CACHE_TTL
        self.historical_price_ttl = settings.HISTORICAL_PRICE_CACHE_TTL

    @cache(ttl=settings.CURRENT_PRICE_CACHE_TTL, key_prefix="bitcoin:current_price", exclude_args=["db"])
    async def get_current_price(self, db: AsyncSession) -> float:
        """Get current Bitcoin price from CoinGecko and save to database."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/simple/price",
                params={
                    "ids": "bitcoin",
                    "vs_currencies": "usd"
                },
                headers=self.headers
            )
            response.raise_for_status()
            price = float(response.json()["bitcoin"]["usd"])
            
            # Save to database
            bitcoin_price = BitcoinPrice(
                price_usd=price,
                timestamp=datetime.utcnow(),
                source="coingecko"
            )
            db.add(bitcoin_price)
            await db.commit()
            await db.refresh(bitcoin_price)
            
            return price

    async def get_historical_prices(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> List[BitcoinPriceBase]:
        """
        Get historical Bitcoin prices from database.
        
        Args:
            db: Database session
            start_time: Start of time range (timezone-aware)
            end_time: End of time range (timezone-aware)
            
        Returns:
            List of BitcoinPriceBase objects, sorted by timestamp (newest first)
        """
        # Convert timezone-aware timestamps to UTC naive timestamps
        if start_time.tzinfo is not None:
            start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)
        if end_time.tzinfo is not None:
            end_time = end_time.astimezone(timezone.utc).replace(tzinfo=None)
        
        # Query prices within time range
        query = (
            select(BitcoinPrice)
            .where(
                BitcoinPrice.timestamp >= start_time,
                BitcoinPrice.timestamp <= end_time
            )
            .order_by(BitcoinPrice.timestamp.desc())
        )
        
        result = await db.execute(query)
        db_prices = list(result.scalars().all())
        
        # Convert SQLAlchemy models to Pydantic models
        return [
            BitcoinPriceBase(
                price_usd=price.price_usd,
                timestamp=price.timestamp,
                source=price.source
            )
            for price in db_prices
        ]

    async def invalidate_price_cache(self) -> None:
        """Invalidate all Bitcoin price related caches."""
        invalidate_cache("bitcoin:current_price:*")
        invalidate_cache("bitcoin:historical_prices:*")

# Create a singleton instance
bitcoin_service = BitcoinService() 