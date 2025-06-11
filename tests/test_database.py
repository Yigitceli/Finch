import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from app.services.bitcoin import BitcoinService
from app.core.exceptions import DatabaseError
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_database_connection_error():
    """Test handling of database connection errors."""
    service = BitcoinService()
    mock_db = AsyncMock()
    
    # Simulate database connection error
    mock_db.execute.side_effect = OperationalError(
        statement="SELECT * FROM bitcoin_prices",
        params={},
        orig=Exception("Connection refused")
    )
    
    # Use valid datetime parameters
    start_time = datetime.now(timezone.utc)
    end_time = datetime.now(timezone.utc)
    
    with pytest.raises(DatabaseError) as exc_info:
        await service.get_historical_prices(mock_db, start_time=start_time, end_time=end_time)
    
    assert exc_info.value.status_code == 503
    assert "Database connection failed" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_database_transaction_error():
    """Test handling of database transaction errors."""
    service = BitcoinService()
    mock_db = AsyncMock()
    
    # Simulate transaction error
    mock_db.commit.side_effect = SQLAlchemyError("Transaction failed")
    
    with pytest.raises(DatabaseError) as exc_info:
        await service.get_current_price(mock_db)
    
    assert exc_info.value.status_code == 500
    assert "Database transaction failed" in str(exc_info.value.detail) 