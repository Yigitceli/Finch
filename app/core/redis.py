from typing import Optional, Any
import json
from redis import Redis
from redis.exceptions import RedisError
from app.core.config import get_settings

settings = get_settings()

class RedisClient:
    def __init__(self):
        self.client: Optional[Redis] = None
        self._connect()

    def _connect(self) -> None:
        """Initialize Redis connection with settings from config."""
        try:
            self.client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,  # Automatically decode responses to strings
                socket_timeout=5,  # 5 seconds timeout
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
        except RedisError as e:
            raise ConnectionError(f"Failed to connect to Redis: {str(e)}")

    def is_healthy(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            return bool(self.client and self.client.ping())
        except RedisError:
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis with error handling."""
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except (RedisError, json.JSONDecodeError) as e:
            raise ValueError(f"Error getting value from Redis: {str(e)}")

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with optional TTL."""
        try:
            serialized_value = json.dumps(value)
            if ttl:
                return bool(self.client.setex(key, ttl, serialized_value))
            return bool(self.client.set(key, serialized_value))
        except (RedisError, TypeError) as e:
            raise ValueError(f"Error setting value in Redis: {str(e)}")

    def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            return bool(self.client.delete(key))
        except RedisError as e:
            raise ValueError(f"Error deleting key from Redis: {str(e)}")

    def clear_cache(self) -> None:
        """Clear all keys from current database."""
        try:
            self.client.flushdb()
        except RedisError as e:
            raise ValueError(f"Error clearing Redis cache: {str(e)}")

# Create a singleton instance
redis_client = RedisClient() 