"""Forecasting models information and contribution endpoints."""

from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.models import ModelsResponse, ModelContributionResponse
from app.services.model_service import model_service
from app.utils.validation import validate_coordinates

router = APIRouter(prefix="/api/v1/models", tags=["Models"])


@router.get(
    "",
    response_model=ModelsResponse,
    summary="List active forecasting models",
    description="Returns list of models participating in the hybrid blending system with capabilities and status tags.",
)
async def list_models() -> ModelsResponse:
    return model_service.get_models()


@router.get(
    "/contribution",
    response_model=ModelContributionResponse,
    summary="Get dynamic model weights and explainability reasoning",
    description="Calculates meta-learner weights and scientific attribution reasoning for a location and forecast horizon.",
)
async def get_model_contribution(
    location: Optional[str] = Query(default="Delhi", description="Named Indian location"),
    lat: Optional[float] = Query(default=None, description="Latitude"),
    lon: Optional[float] = Query(default=None, description="Longitude"),
    time: Optional[str] = Query(default=None, description="ISO timestamp"),
    forecast_hour: Optional[int] = Query(default=24, description="Forecast horizon in hours"),
) -> ModelContributionResponse:
    validated_lat, validated_lon, loc_name = validate_coordinates(lat, lon, location)

    return model_service.calculate_contribution(
        location=loc_name,
        lat=validated_lat,
        lon=validated_lon,
        time_iso=time,
        forecast_horizon_hours=float(forecast_hour or 24),
    )
