from datetime import datetime, timedelta
from typing import Optional, List
import httpx
from app.core.config import get_settings
from app.core.cache import cache, invalidate_cache
from app.models.bitcoin import BitcoinPrice
from app.schemas.bitcoin import BitcoinPriceCreate

settings = get_settings()

class BitcoinService:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Finch/1.0"
        }

    @cache(ttl=300, key_prefix="btc_price")  # Cache for 5 minutes
    async def get_current_price(self) -> float:
        """Get current Bitcoin price from CoinGecko."""
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
            return float(response.json()["bitcoin"]["usd"])

    @cache(ttl=3600, key_prefix="btc_historical")  # Cache for 1 hour
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
        invalidate_cache("btc_price:*")
        invalidate_cache("btc_historical:*")

# Create a singleton instance
bitcoin_service = BitcoinService() 