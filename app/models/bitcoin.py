from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BitcoinPrice(Base):
    """
    Model for storing Bitcoin price data.
    """
    __tablename__ = "bitcoin_prices"

    id = Column(Integer, primary_key=True, index=True)
    price_usd = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    source = Column(String(50), nullable=False, default="coingecko")  # For future extensibility
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<BitcoinPrice(price_usd={self.price_usd}, timestamp={self.timestamp})>" 