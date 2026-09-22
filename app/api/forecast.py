"""Forecast API endpoint."""

from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.forecast import ForecastResponse
from app.services.forecast_service import forecast_service
from app.utils.validation import validate_coordinates, validate_forecast_hours

router = APIRouter(prefix="/api/v1", tags=["Forecast"])


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="Get multi-model blended weather forecast",
    description="Generates hybrid forecast blending NWP, AI models, and Open-Meteo composite with dynamic weighting and bias correction.",
)
async def get_forecast(
    lat: Optional[float] = Query(default=None, description="Latitude (-90.0 to 90.0)"),
    lon: Optional[float] = Query(default=None, description="Longitude (-180.0 to 180.0)"),
    hours: Optional[int] = Query(default=None, description="Forecast horizon in hours (alias for forecast_hours)"),
    forecast_hours: Optional[int] = Query(default=72, description="Forecast horizon in hours (1 to 168)"),
    time: Optional[str] = Query(default=None, description="Target timestamp (optional)"),
    location: Optional[str] = Query(default=None, description="Named Indian location (e.g. Delhi, Mumbai)"),
) -> ForecastResponse:
    validated_lat, validated_lon, loc_name = validate_coordinates(lat, lon, location)
    horizon = validate_forecast_hours(hours=hours, forecast_hours=forecast_hours)

    resp, _, _, _, _ = await forecast_service.get_forecast(
        lat=validated_lat,
        lon=validated_lon,
        forecast_hours=horizon,
        location_name=loc_name,
        blend=True,
    )
    return resp
