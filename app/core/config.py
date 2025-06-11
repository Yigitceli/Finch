from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from pydantic import model_validator


class Settings(BaseSettings):
    """
    Application settings
    """
    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int
    POSTGRES_HOST: str = "db"  # Default to Docker service name
    DATABASE_URL: Optional[str] = None
    SYNC_DATABASE_URL: Optional[str] = None

    @model_validator(mode='after')
    def set_database_urls(self) -> 'Settings':
        """Set database URLs after all settings are loaded"""
        self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        self.SYNC_DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        return self

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