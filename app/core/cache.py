from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast
import hashlib
import json
from app.core.redis import redis_client

T = TypeVar('T')

def generate_cache_key(func: Callable, *args: Any, **kwargs: Any) -> str:
    """Generate a unique cache key based on function name and arguments."""
    # Convert args and kwargs to a string representation
    key_parts = [func.__name__]
    
    # Add args
    if args:
        key_parts.extend([str(arg) for arg in args])
    
    # Add kwargs (sorted for consistency)
    if kwargs:
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
    
    # Create a hash of the key parts
    key_string = ":".join(key_parts)
    return f"cache:{hashlib.md5(key_string.encode()).hexdigest()}"

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
            
            # Filter out excluded arguments
            filtered_kwargs = kwargs.copy()
            if exclude_args:
                for arg in exclude_args:
                    filtered_kwargs.pop(arg, None)
            
            # Generate cache key
            cache_key = generate_cache_key(func, *args, **filtered_kwargs)
            if key_prefix:
                cache_key = f"{key_prefix}:{cache_key}"
            
            # Try to get from cache
            cached_result = redis_client.get(cache_key)
            if cached_result is not None:
                return cast(T, cached_result)
            
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