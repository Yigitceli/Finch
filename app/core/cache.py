from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast
import hashlib
import json
from app.core.redis import redis_client

T = TypeVar('T')

def generate_cache_key(func: Callable, exclude_args: Optional[list[str]] = None, *args: Any, **kwargs: Any) -> str:
    """Generate a unique cache key based on function name and arguments."""
    # Convert args and kwargs to a string representation
    key_parts = [func.__name__]
    
    # Add args (excluding any that should be excluded)
    if args:
        # Get function parameter names
        import inspect
        param_names = list(inspect.signature(func).parameters.keys())
        
        # Add args that are not in exclude_args
        for i, arg in enumerate(args):
            if param_names[i] not in (exclude_args or []):
                key_parts.append(str(arg))
    
    # Add kwargs (sorted for consistency, excluding any that should be excluded)
    if kwargs:
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in (exclude_args or [])}
        if filtered_kwargs:
            key_parts.extend([f"{k}:{v}" for k, v in sorted(filtered_kwargs.items())])
    
    # Create a hash of the key parts
    key_string = ":".join(key_parts)
    return f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"

async def get_cache(key: str) -> Optional[str]:
    """Get value from cache."""
    if not redis_client.is_healthy():
        return None
    return redis_client.get(key)

async def set_cache(key: str, value: str, ttl: Optional[int] = None) -> None:
    """Set value in cache with optional TTL."""
    if not redis_client.is_healthy():
        return
    redis_client.set(key, value, ttl)

def cache(
    ttl: Optional[int] = 3600,  # Default 1 hour
    key_prefix: Optional[str] = None,
    exclude_args: Optional[list[str]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Cache decorator for caching function results in Redis.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Optional prefix for cache keys
        exclude_args: List of argument names to exclude from cache key generation
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Skip caching if Redis is not healthy
            if not redis_client.is_healthy():
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = generate_cache_key(func, exclude_args, *args, **kwargs)
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result is not None:
                print(f"Data retrieved from cache for key: {cache_key}")
                return cast(T, cached_result)
            else:
                print(f"No data found in cache for key: {cache_key}")
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.set(cache_key, result, ttl)
            
            return result
        
        return cast(Callable[..., T], wrapper)
    return decorator

def invalidate_cache(pattern: str) -> None:
    """
    Invalidate cache entries matching the given pattern.
    
    Args:
        pattern: Redis key pattern to match (e.g., "cache:user:*")
    """
    if not redis_client.is_healthy():
        return
    
    try:
        # Get all keys matching the pattern
        keys = redis_client.client.keys(pattern)
        if keys:
            redis_client.client.delete(*keys)
    except Exception as e:
        # Log error but don't raise
        print(f"Error invalidating cache: {str(e)}") 