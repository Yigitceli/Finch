from datetime import datetime, timedelta, timezone
from typing import Optional, List
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from app.core.config import get_settings
from app.core.cache import cache, invalidate_cache
from app.models.bitcoin import BitcoinPrice
from app.schemas.bitcoin import BitcoinPriceCreate, BitcoinPriceBase
from app.core.exceptions import (
    CoinGeckoRateLimitError,
    CoinGeckoNetworkError,
    CoinGeckoInvalidResponseError,
    CoinGeckoUnknownSymbolError,
    DatabaseError
)
from app.core.logging import setup_logging

settings = get_settings()
logger = setup_logging("bitcoin_service")

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
        """
        Get current Bitcoin price from CoinGecko and save to database.
        
        Raises:
            CoinGeckoRateLimitError: When API rate limit is exceeded
            CoinGeckoNetworkError: When there are network issues
            CoinGeckoInvalidResponseError: When API response is invalid
            CoinGeckoUnknownSymbolError: When cryptocurrency symbol is unknown
            DatabaseError: When database operation fails
        """
        try:
            logger.debug("Making request to CoinGecko API for current price")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/simple/price",
                    params={
                        "ids": "bitcoin",
                        "vs_currencies": "usd"
                    },
                    headers=self.headers
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    logger.warning(f"Rate limit exceeded. Retry after: {retry_after}")
                    raise CoinGeckoRateLimitError(retry_after=int(retry_after) if retry_after else None)
                
                # Handle other HTTP errors
                response.raise_for_status()
                
                try:
                    data = response.json()
                    if "bitcoin" not in data:
                        logger.error("Bitcoin symbol not found in CoinGecko response")
                        raise CoinGeckoUnknownSymbolError("bitcoin")
                    
                    price = float(data["bitcoin"]["usd"])
                    logger.debug(f"Successfully fetched Bitcoin price: ${price:,.2f}")
                except (KeyError, ValueError, TypeError) as e:
                    logger.error(f"Invalid response format from CoinGecko: {str(e)}")
                    raise CoinGeckoInvalidResponseError(f"Invalid response format: {str(e)}")
                
                # Save to database
                try:
                    logger.debug("Saving price to database")
                    bitcoin_price = BitcoinPrice(
                        price_usd=price,
                        timestamp=datetime.utcnow(),
                        source="coingecko"
                    )
                    db.add(bitcoin_price)
                    await db.commit()
                    await db.refresh(bitcoin_price)
                    logger.debug("Successfully saved price to database")
                except SQLAlchemyError as e:
                    logger.error(f"Database error while saving price: {str(e)}")
                    await db.rollback()
                    raise DatabaseError(
                        status_code=500,
                        detail=f"Database transaction failed: {str(e)}"
                    )
                
                return price
                
        except httpx.TimeoutException:
            logger.error("Request to CoinGecko API timed out")
            raise CoinGeckoNetworkError("Request to CoinGecko API timed out")
        except httpx.RequestError as e:
            logger.error(f"Network error while requesting CoinGecko API: {str(e)}")
            raise CoinGeckoNetworkError(f"Network error: {str(e)}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.error("Bitcoin symbol not found in CoinGecko API")
                raise CoinGeckoUnknownSymbolError("bitcoin")
            logger.error(f"HTTP error from CoinGecko API: {str(e)}")
            raise CoinGeckoNetworkError(f"HTTP error: {str(e)}")
        except Exception as e:
            if isinstance(e, (CoinGeckoRateLimitError, CoinGeckoUnknownSymbolError, CoinGeckoInvalidResponseError, DatabaseError)):
                raise
            logger.error(f"Unexpected error while getting current price: {str(e)}", exc_info=True)
            raise CoinGeckoNetworkError(f"Unexpected error: {str(e)}")

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
        try:
            logger.debug(f"Querying historical prices from {start_time} to {end_time}")
            # Convert timezone-aware timestamps to UTC naive timestamps
            if start_time.tzinfo is not None:
                start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)
            if end_time.tzinfo is not None:
                end_time = end_time.astimezone(timezone.utc).replace(tzinfo=None)

            query = select(BitcoinPrice).where(
                BitcoinPrice.timestamp.between(start_time, end_time)
            ).order_by(BitcoinPrice.timestamp.desc())

            result = await db.execute(query)
            prices = result.scalars().all()
            logger.debug(f"Found {len(prices)} historical prices in database")

            return [BitcoinPriceBase.model_validate(price) for price in prices]
        except OperationalError as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise DatabaseError(
                status_code=503,
                detail=f"Database connection failed: {str(e)}"
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error while querying historical prices: {str(e)}")
            raise DatabaseError(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )

    async def invalidate_price_cache(self) -> None:
        """Invalidate all Bitcoin price related caches."""
        logger.debug("Invalidating Bitcoin price caches")
        invalidate_cache("bitcoin:current_price:*")
        invalidate_cache("bitcoin:historical_prices:*")
        logger.debug("Successfully invalidated Bitcoin price caches")

# Create a singleton instance
bitcoin_service = BitcoinService() 