from fastapi import HTTPException
from typing import Optional, Dict, Any

class CoinGeckoError(HTTPException):
    """Base exception for CoinGecko API errors."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class CoinGeckoRateLimitError(CoinGeckoError):
    """Exception for CoinGecko API rate limit errors."""
    def __init__(self, retry_after: Optional[int] = None):
        headers = {"Retry-After": str(retry_after)} if retry_after else None
        super().__init__(
            status_code=429,
            detail="CoinGecko API rate limit exceeded. Please try again later.",
            headers=headers
        )

class CoinGeckoNetworkError(CoinGeckoError):
    """Exception for CoinGecko API network errors."""
    def __init__(self, detail: str = "Failed to connect to CoinGecko API"):
        super().__init__(
            status_code=503,
            detail=detail
        )

class CoinGeckoInvalidResponseError(CoinGeckoError):
    """Exception for invalid responses from CoinGecko API."""
    def __init__(self, detail: str = "Invalid response from CoinGecko API"):
        super().__init__(
            status_code=502,
            detail=detail
        )

class CoinGeckoUnknownSymbolError(CoinGeckoError):
    """Exception for unknown cryptocurrency symbols."""
    def __init__(self, symbol: str):
        super().__init__(
            status_code=404,
            detail=f"Unknown cryptocurrency symbol: {symbol}"
        )

class DatabaseError(HTTPException):
    """Base exception for database errors."""
    def __init__(
        self,
        status_code: int,
        detail: str
    ):
        super().__init__(status_code=status_code, detail=detail) 