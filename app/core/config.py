from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings
    """
    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int
    DATABASE_URL: str

    # Redis settings
    REDIS_PORT: int
    REDIS_URL: str

    # Cache settings
    CACHE_TTL: int

    # API settings
    COINGECKO_API_URL: str
    API_RATE_LIMIT: int

    # Application settings
    DEBUG: bool
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