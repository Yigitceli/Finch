import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from app.main import app
from app.services.bitcoin import BitcoinService
from app.core.exceptions import CoinGeckoRateLimitError, CoinGeckoNetworkError, CoinGeckoInvalidResponseError
from app.schemas.bitcoin import BitcoinPriceBase

client = TestClient(app)

@pytest.mark.asyncio
async def test_get_current_price_success():
    # Mock BitcoinService.get_current_price
    with patch.object(BitcoinService, 'get_current_price', new_callable=AsyncMock) as mock_get_price:
        mock_get_price.return_value = 12345.67
        
        response = client.get("/api/v1/bitcoin/current-price")
        
        assert response.status_code == 200
        data = response.json()
        assert "price" in data
        assert data["price"] == 12345.67

@pytest.mark.asyncio
async def test_get_current_price_rate_limit():
    with patch.object(BitcoinService, 'get_current_price', new_callable=AsyncMock) as mock_get_price:
        mock_get_price.side_effect = CoinGeckoRateLimitError(retry_after=60)
        
        response = client.get("/api/v1/bitcoin/current-price")
        
        assert response.status_code == 429
        data = response.json()
        assert "detail" in data
        assert "rate limit" in data["detail"].lower()
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "60"

@pytest.mark.asyncio
async def test_get_current_price_network_error():
    with patch.object(BitcoinService, 'get_current_price', new_callable=AsyncMock) as mock_get_price:
        mock_get_price.side_effect = CoinGeckoNetworkError("Network error occurred while fetching price")
        
        response = client.get("/api/v1/bitcoin/current-price")
        
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "network error" in data["detail"].lower()

@pytest.mark.asyncio
async def test_get_current_price_invalid_response():
    with patch.object(BitcoinService, 'get_current_price', new_callable=AsyncMock) as mock_get_price:
        mock_get_price.side_effect = CoinGeckoInvalidResponseError("Invalid response from CoinGecko API")
        
        response = client.get("/api/v1/bitcoin/current-price")
        
        assert response.status_code == 502
        data = response.json()
        assert "detail" in data
        assert "invalid response" in data["detail"].lower()

@pytest.mark.asyncio
async def test_get_historical_prices_success():
    # Mock BitcoinService.get_historical_prices
    with patch.object(BitcoinService, 'get_historical_prices', new_callable=AsyncMock) as mock_get_prices:
        # Create test data
        test_prices = [
            BitcoinPriceBase(
                price_usd=200.0,
                timestamp=datetime(2024, 1, 2, 12, 0, 0),
                source="coingecko"
            ),
            BitcoinPriceBase(
                price_usd=150.0,
                timestamp=datetime(2024, 1, 2, 10, 0, 0),
                source="coingecko"
            ),
            BitcoinPriceBase(
                price_usd=100.0,
                timestamp=datetime(2024, 1, 2, 8, 0, 0),
                source="coingecko"
            )
        ]
        mock_get_prices.return_value = test_prices
        
        # Test with query parameters
        response = client.get(
            "/api/v1/bitcoin/price-history",
            params={
                "start_time": "2024-01-02T00:00:00Z",
                "end_time": "2024-01-03T00:00:00Z"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "prices" in data
        assert len(data["prices"]) == 3
        
        # Verify price data
        prices = data["prices"]
        assert prices[0]["price_usd"] == 200.0
        assert prices[1]["price_usd"] == 150.0
        assert prices[2]["price_usd"] == 100.0
        
        # Verify timestamps
        assert prices[0]["timestamp"] == "2024-01-02T12:00:00"
        assert prices[1]["timestamp"] == "2024-01-02T10:00:00"
        assert prices[2]["timestamp"] == "2024-01-02T08:00:00"
        
        # Verify source
        assert all(price["source"] == "coingecko" for price in prices)

@pytest.mark.asyncio
async def test_get_historical_prices_empty():
    with patch.object(BitcoinService, 'get_historical_prices', new_callable=AsyncMock) as mock_get_prices:
        mock_get_prices.return_value = []
        
        response = client.get(
            "/api/v1/bitcoin/price-history",
            params={
                "start_time": "2024-01-02T00:00:00Z",
                "end_time": "2024-01-03T00:00:00Z"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "prices" in data
        assert len(data["prices"]) == 0

@pytest.mark.asyncio
async def test_get_historical_prices_invalid_dates():
    # Test with invalid date format
    response = client.get(
        "/api/v1/bitcoin/price-history",
        params={
            "start_time": "invalid-date",
            "end_time": "2024-01-03T00:00:00Z"
        }
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

    # Test with end_time before start_time
    response = client.get(
        "/api/v1/bitcoin/price-history",
        params={
            "start_time": "2024-01-03T00:00:00Z",
            "end_time": "2024-01-02T00:00:00Z"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "End time must be after start time" in data["detail"] 