import pytest
from unittest.mock import AsyncMock, patch
from app.services.bitcoin import BitcoinService
from app.core.exceptions import CoinGeckoRateLimitError, CoinGeckoNetworkError, CoinGeckoInvalidResponseError, CoinGeckoUnknownSymbolError
from datetime import datetime, timezone
from app.schemas.bitcoin import BitcoinPriceBase
from app.models.bitcoin import BitcoinPrice

@pytest.mark.asyncio
async def test_get_current_price_success():
    service = BitcoinService()
    mock_db = AsyncMock()
    mock_response = {"bitcoin": {"usd": 12345.67}}

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response
        )
        price = await service.get_current_price(mock_db)
        assert price == 12345.67
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_get_current_price_rate_limit():
    service = BitcoinService()
    mock_db = AsyncMock()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=429,
            headers={"Retry-After": "60"},
            json=lambda: {}
        )
        with pytest.raises(CoinGeckoRateLimitError) as exc_info:
            await service.get_current_price(mock_db)
        assert exc_info.value.status_code == 429
        assert "rate limit" in str(exc_info.value.detail).lower()

@pytest.mark.asyncio
async def test_get_current_price_network_error():
    service = BitcoinService()
    mock_db = AsyncMock()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = Exception("Network error")
        with pytest.raises(CoinGeckoNetworkError) as exc_info:
            await service.get_current_price(mock_db)
        assert exc_info.value.status_code == 503
        assert "network error" in str(exc_info.value.detail).lower()

@pytest.mark.asyncio
async def test_get_current_price_invalid_response():
    service = BitcoinService()
    mock_db = AsyncMock()

    # 1. API response missing 'bitcoin' key
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"notbitcoin": {"usd": 1}}
        )
        with pytest.raises(CoinGeckoUnknownSymbolError):
            await service.get_current_price(mock_db)

    # 2. API response with wrong type
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"bitcoin": {"usd": "not_a_number"}}
        )
        with pytest.raises(CoinGeckoInvalidResponseError):
            await service.get_current_price(mock_db)

@pytest.mark.asyncio
async def test_get_historical_prices_empty():
    service = BitcoinService()
    mock_db = AsyncMock()
    # Mock DB result: no prices
    mock_scalars = AsyncMock()
    mock_scalars.all.return_value = []
    mock_result = AsyncMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result
    start = datetime(2025, 1, 1, 0, 0, 0)
    end = datetime(2025, 1, 2, 0, 0, 0)
    prices = await service.get_historical_prices(mock_db, start, end)
    assert prices == []

@pytest.mark.asyncio
async def test_get_historical_prices_single():
    service = BitcoinService()
    mock_db = AsyncMock()
    # Mock DB result: one price
    price_obj = BitcoinPrice(
        price_usd=100.0,
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        source="coingecko"
    )
    mock_scalars = AsyncMock()
    mock_scalars.all.return_value = [price_obj]
    mock_result = AsyncMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result
    start = datetime(2025, 1, 1, 0, 0, 0)
    end = datetime(2025, 1, 2, 0, 0, 0)
    prices = await service.get_historical_prices(mock_db, start, end)
    assert len(prices) == 1
    assert prices[0].price_usd == 100.0
    assert prices[0].timestamp == datetime(2025, 1, 1, 12, 0, 0)
    assert prices[0].source == "coingecko"

@pytest.mark.asyncio
async def test_get_historical_prices_multiple():
    service = BitcoinService()
    mock_db = AsyncMock()
    # Mock DB result: multiple prices
    price_objs = [
        BitcoinPrice(price_usd=200.0, timestamp=datetime(2025, 1, 2, 12, 0, 0), source="coingecko"),
        BitcoinPrice(price_usd=150.0, timestamp=datetime(2025, 1, 2, 10, 0, 0), source="coingecko"),
        BitcoinPrice(price_usd=100.0, timestamp=datetime(2025, 1, 2, 8, 0, 0), source="coingecko"),
    ]
    mock_scalars = AsyncMock()
    mock_scalars.all.return_value = price_objs
    mock_result = AsyncMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result
    start = datetime(2025, 1, 2, 0, 0, 0)
    end = datetime(2025, 1, 3, 0, 0, 0)
    prices = await service.get_historical_prices(mock_db, start, end)
    assert len(prices) == 3
    assert [p.price_usd for p in prices] == [200.0, 150.0, 100.0]
    assert all(isinstance(p, BitcoinPriceBase) for p in prices)

@pytest.mark.asyncio
async def test_get_historical_prices_timezone_aware():
    service = BitcoinService()
    mock_db = AsyncMock()
    # Mock DB result: one price
    price_obj = BitcoinPrice(
        price_usd=300.0,
        timestamp=datetime(2025, 1, 1, 15, 0, 0),
        source="coingecko"
    )
    mock_scalars = AsyncMock()
    mock_scalars.all.return_value = [price_obj]
    mock_result = AsyncMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result
    # Use timezone-aware datetimes
    start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2025, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    prices = await service.get_historical_prices(mock_db, start, end)
    assert len(prices) == 1
    assert prices[0].price_usd == 300.0
    assert prices[0].timestamp == datetime(2025, 1, 1, 15, 0, 0)
    assert prices[0].source == "coingecko" 