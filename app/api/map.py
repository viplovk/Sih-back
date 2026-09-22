"""Map visualization spatial endpoints: timeline, wind vectors, temperature, precipitation, and air quality."""

from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.map import (
    TimelineResponse,
    WindGridResponse,
    TemperatureGridResponse,
    PrecipitationGridResponse,
    AirQualityGridResponse,
)
from app.services.map_service import map_service

router = APIRouter(prefix="/api/v1/map", tags=["Map"])


@router.get(
    "/timeline",
    response_model=TimelineResponse,
    summary="Get synchronized map timeline",
    description="Returns available real timestamps for live and hourly forecast animation playback.",
)
async def get_map_timeline() -> TimelineResponse:
    return await map_service.get_timeline()


@router.get(
    "/wind",
    response_model=WindGridResponse,
    summary="Get real wind vector field",
    description="Returns meteorological wind vectors (u, v, speed, direction) for wind particle animation.",
)
async def get_wind_grid(
    valid_time: Optional[str] = Query(default=None, description="ISO valid timestamp (e.g. 2026-09-22T18:00:00Z) or 'live'"),
    width: int = Query(default=80, ge=10, le=120, description="Horizontal grid resolution"),
    height: int = Query(default=80, ge=10, le=120, description="Vertical grid resolution"),
) -> WindGridResponse:
    return await map_service.get_wind_field(valid_time=valid_time, width=width, height=height)


@router.get(
    "/temperature",
    response_model=TemperatureGridResponse,
    summary="Get real temperature field",
    description="Returns spatial temperature values (°C) interpolated from real Open-Meteo observations.",
)
async def get_temperature_grid(
    valid_time: Optional[str] = Query(default=None, description="ISO valid timestamp or 'live'"),
    forecast_hour: Optional[int] = Query(default=None, description="Forecast hour offset (optional)"),
    resolution: Optional[str] = Query(default=None, description="Resolution preset (e.g. 'demo', 'high')"),
    width: int = Query(default=80, ge=10, le=120, description="Horizontal grid resolution"),
    height: int = Query(default=80, ge=10, le=120, description="Vertical grid resolution"),
) -> TemperatureGridResponse:
    target_w = 40 if resolution == "demo" else width
    target_h = 40 if resolution == "demo" else height
    return await map_service.get_temperature_field(
        valid_time=valid_time,
        width=target_w,
        height=target_h,
        forecast_hour=forecast_hour,
    )


@router.get(
    "/precipitation",
    response_model=PrecipitationGridResponse,
    summary="Get real precipitation field",
    description="Returns spatial precipitation values (mm) interpolated from real Open-Meteo observations.",
)
async def get_precipitation_grid(
    valid_time: Optional[str] = Query(default=None, description="ISO valid timestamp or 'live'"),
    width: int = Query(default=80, ge=10, le=120, description="Horizontal grid resolution"),
    height: int = Query(default=80, ge=10, le=120, description="Vertical grid resolution"),
) -> PrecipitationGridResponse:
    return await map_service.get_precipitation_field(valid_time=valid_time, width=width, height=height)


@router.get(
    "/air-quality",
    response_model=AirQualityGridResponse,
    summary="Get real air quality field",
    description="Returns spatial air quality indices (AQI, PM2.5, PM10, NO2, O3) from Open-Meteo Air Quality API.",
)
async def get_air_quality_grid(
    valid_time: Optional[str] = Query(default=None, description="ISO valid timestamp or 'live'"),
    width: int = Query(default=80, ge=10, le=120, description="Horizontal grid resolution"),
    height: int = Query(default=80, ge=10, le=120, description="Vertical grid resolution"),
) -> AirQualityGridResponse:
    return await map_service.get_air_quality_field(valid_time=valid_time, width=width, height=height)
