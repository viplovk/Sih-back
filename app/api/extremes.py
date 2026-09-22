"""Extreme weather events endpoint."""

from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.extremes import ExtremesResponse
from app.services.forecast_service import forecast_service
from app.services.extreme_event_service import extreme_event_service
from app.utils.validation import validate_coordinates, validate_forecast_hours

router = APIRouter(prefix="/api/v1", tags=["Extremes"])


@router.get(
    "/extremes",
    response_model=ExtremesResponse,
    summary="Detect extreme weather events",
    description="Identifies potential heatwaves, heavy rainfall, high winds, and cold spells across the forecast horizon against configured demonstration thresholds.",
)
async def get_extreme_events(
    lat: Optional[float] = Query(default=None, description="Latitude (-90.0 to 90.0)"),
    lon: Optional[float] = Query(default=None, description="Longitude (-180.0 to 180.0)"),
    hours: Optional[int] = Query(default=72, description="Analysis horizon in hours (1 to 168)"),
    location: Optional[str] = Query(default=None, description="Named Indian location"),
) -> ExtremesResponse:
    validated_lat, validated_lon, loc_name = validate_coordinates(lat, lon, location)
    horizon = validate_forecast_hours(forecast_hours=hours)

    forecast_resp, _, _, _, _ = await forecast_service.get_forecast(
        lat=validated_lat,
        lon=validated_lon,
        forecast_hours=horizon,
        location_name=loc_name,
        blend=True,
    )

    return extreme_event_service.detect_extremes_in_forecast(
        forecast_points=forecast_resp.forecast,
        location_name=loc_name,
    )
