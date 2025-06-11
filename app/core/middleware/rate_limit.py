from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.redis import redis_client
from app.core.config import get_settings
from app.core.logging import setup_logging
import time

settings = get_settings()
logger = setup_logging("rate_limit_middleware")

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check endpoint
        if request.url.path == "/api/v1/health":
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Create a unique key for this client
        key = f"rate_limit:{client_ip}"
        
        try:
            # Get current request count
            current_count = redis_client.client.get(key)
            
            if current_count is None:
                # First request from this client
                redis_client.client.setex(key, 60, 1)  # Set expiry to 60 seconds
                current_count = 1
            else:
                current_count = int(current_count)
                
                # Check if rate limit is exceeded
                if current_count >= settings.API_RATE_LIMIT:
                    logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                    return JSONResponse(
                        status_code=429,
                        content={"detail": f"Rate limit exceeded. Maximum {settings.API_RATE_LIMIT} requests per minute allowed."},
                        headers={
                            "Retry-After": "60",
                            "X-RateLimit-Limit": str(settings.API_RATE_LIMIT),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(time.time()) + 60)
                        }
                    )
                
                # Increment request count
                redis_client.client.incr(key)
                current_count += 1
            
            # Process the request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(settings.API_RATE_LIMIT)
            response.headers["X-RateLimit-Remaining"] = str(settings.API_RATE_LIMIT - current_count)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)  # Reset time in Unix timestamp
            
            return response
            
        except Exception as e:
            logger.error(f"Error in rate limiting middleware: {str(e)}")
            # If Redis is down, allow the request to proceed but log the error
            response = await call_next(request)
            response.headers["X-RateLimit-Status"] = "Redis unavailable"
            return response 