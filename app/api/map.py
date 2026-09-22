"""Geospatial temperature map API endpoint."""

from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.map import MapTemperatureResponse
from app.services.map_service import map_service
from app.utils.validation import validate_grid_resolution

router = APIRouter(prefix="/api/v1/map", tags=["Geospatial Map"])


@router.get(
    "/temperature",
    response_model=MapTemperatureResponse,
    summary="Get India temperature heatmap grid",
    description="Returns geospatial temperature grid across India for rendering dynamic heatmaps in the frontend.",
)
async def get_temperature_map(
    time: Optional[str] = Query(default=None, description="ISO timestamp for target map hour"),
    forecast_hour: Optional[int] = Query(default=0, description="Lead time in hours (0 to 168)"),
    resolution: Optional[str] = Query(default="demo", description="Grid resolution: 'demo', 'medium', 'high', '0.25', '0.5', '1.0'"),
) -> MapTemperatureResponse:
    validated_res = validate_grid_resolution(resolution or "demo")
    return map_service.generate_temperature_map(
        time_iso=time,
        forecast_hour=forecast_hour or 0,
        resolution=validated_res,
    )
