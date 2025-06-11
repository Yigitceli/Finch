from datetime import datetime, timedelta
from typing import Optional, List
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.cache import cache, invalidate_cache
from app.models.bitcoin import BitcoinPrice
from app.schemas.bitcoin import BitcoinPriceCreate

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

    @cache(ttl=settings.HISTORICAL_PRICE_CACHE_TTL, key_prefix="bitcoin:historical_prices")
    async def get_historical_prices(
        self,
        days: int = 7,
        interval: str = "daily"
    ) -> List[BitcoinPrice]:
        """Get historical Bitcoin prices from CoinGecko."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/coins/bitcoin/market_chart",
                params={
                    "vs_currency": "usd",
                    "days": days,
                    "interval": interval
                },
                headers=self.headers
            )
            response.raise_for_status()
            
            prices = []
            for timestamp, price in response.json()["prices"]:
                prices.append(
                    BitcoinPriceCreate(
                        price_usd=float(price),
                        timestamp=datetime.fromtimestamp(timestamp / 1000),
                        source="coingecko"
                    )
                )
            return prices

    async def invalidate_price_cache(self) -> None:
        """Invalidate all Bitcoin price related caches."""
        invalidate_cache("bitcoin:current_price:*")
        invalidate_cache("bitcoin:historical_prices:*")

# Create a singleton instance
bitcoin_service = BitcoinService() 