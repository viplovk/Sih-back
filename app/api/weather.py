"""Current weather API endpoints."""

from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.weather import WeatherResponse
from app.services.weather_service import weather_service
from app.utils.validation import validate_coordinates

router = APIRouter(prefix="/api/v1", tags=["Weather"])


@router.get(
    "/weather",
    response_model=WeatherResponse,
    summary="Get current weather",
    description="Retrieve live observed weather metrics directly from Open-Meteo for specified coordinates or Indian city.",
)
async def get_current_weather(
    lat: Optional[float] = Query(default=None, description="Latitude (-90.0 to 90.0)"),
    lon: Optional[float] = Query(default=None, description="Longitude (-180.0 to 180.0)"),
    latitude: Optional[float] = Query(default=None, description="Latitude alias"),
    longitude: Optional[float] = Query(default=None, description="Longitude alias"),
    location: Optional[str] = Query(default=None, description="Named location (e.g. Delhi, Mumbai)"),
) -> WeatherResponse:
    effective_lat = latitude if latitude is not None else lat
    effective_lon = longitude if longitude is not None else lon
    validated_lat, validated_lon, loc_name = validate_coordinates(effective_lat, effective_lon, location)
    return await weather_service.get_current_weather(
        lat=validated_lat,
        lon=validated_lon,
        location_name=loc_name,
    )
