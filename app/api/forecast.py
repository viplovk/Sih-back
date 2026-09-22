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
    summary="Get hourly weather forecast",
    description="Retrieve real hourly forecast frames directly from Open-Meteo with verified timestamps.",
)
async def get_forecast(
    lat: Optional[float] = Query(default=None, description="Latitude (-90.0 to 90.0)"),
    lon: Optional[float] = Query(default=None, description="Longitude (-180.0 to 180.0)"),
    latitude: Optional[float] = Query(default=None, description="Latitude alias"),
    longitude: Optional[float] = Query(default=None, description="Longitude alias"),
    hours: Optional[int] = Query(default=None, description="Forecast horizon in hours"),
    forecast_hours: Optional[int] = Query(default=48, description="Forecast horizon in hours (min 24)"),
    location: Optional[str] = Query(default=None, description="Named location (e.g. Delhi, Mumbai)"),
) -> ForecastResponse:
    effective_lat = latitude if latitude is not None else lat
    effective_lon = longitude if longitude is not None else lon
    validated_lat, validated_lon, loc_name = validate_coordinates(effective_lat, effective_lon, location)

    raw_horizon = hours if hours is not None else forecast_hours
    effective_horizon = max(24, min(raw_horizon or 48, 168))

    return await forecast_service.get_forecast(
        lat=validated_lat,
        lon=validated_lon,
        forecast_hours=effective_horizon,
        location_name=loc_name,
        blend=False,
    )
