from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from app.api import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()
logger = setup_logging("app")

app = FastAPI(
    title="Finch Crypto Price Service",
    description="A service that fetches and stores Bitcoin prices from CoinGecko API",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests and their processing time."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request started: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"Status: {response.status_code} Duration: {process_time:.2f}s"
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"Error: {str(e)} Duration: {process_time:.2f}s",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info(
        f"Starting Finch Crypto Price Service v{app.version} "
        f"in {settings.ENVIRONMENT} environment"
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Shutting down Finch Crypto Price Service")

# Include API router
app.include_router(api_router)
logger.info("API router included successfully") 