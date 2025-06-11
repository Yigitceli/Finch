from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings
    """
    # Database settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "bitcoin_prices"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:{POSTGRES_PORT}/{POSTGRES_DB}"

    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    # Cache settings
    CURRENT_PRICE_CACHE_TTL: int = 300  # 5 minutes
    HISTORICAL_PRICE_CACHE_TTL: int = 3600  # 1 hour

    # API settings
    COINGECKO_API_URL: str = "https://api.coingecko.com/api/v3"
    API_RATE_LIMIT: int

    # Application settings
    DEBUG: bool = True
    ENVIRONMENT: str
    APP_PORT: int

    # pgAdmin settings
    PGADMIN_EMAIL: str
    PGADMIN_PASSWORD: str
    PGADMIN_PORT: int

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings() 