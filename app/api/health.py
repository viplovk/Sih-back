"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.core.config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str = Field(default="ok", json_schema_extra={"example": "ok"})
    service: str = Field(default="algoriot-backend", json_schema_extra={"example": "algoriot-backend"})
    version: str = Field(default="1.0.0", json_schema_extra={"example": "1.0.0"})
    environment: str = Field(default="development", json_schema_extra={"example": "development"})


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Root health status",
    description="Returns backend operational health and service metadata.",
)
@router.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="Versioned API health status",
    description="Returns backend operational health and service metadata.",
)
async def get_health() -> HealthResponse:
    """Return service health status without exposing sensitive configuration."""
    return HealthResponse(
        status="ok",
        service=settings.SERVICE_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )
