from typing import Dict
from pydantic import BaseModel, Field

class ServiceHealth(BaseModel):
    """Health status of a single service."""
    is_healthy: bool = Field(..., description="Whether the service is healthy")
    message: str = Field(..., description="Health status message")

class HealthResponse(BaseModel):
    """Overall health status of the application."""
    is_healthy: bool = Field(..., description="Whether all services are healthy")
    services: Dict[str, ServiceHealth] = Field(
        ...,
        description="Health status of individual services"
    ) 