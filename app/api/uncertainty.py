"""Ensemble forecast uncertainty endpoint."""

from typing import Optional
from fastapi import APIRouter, Query
from app.schemas.uncertainty import UncertaintyResponse
from app.services.forecast_service import forecast_service
from app.services.uncertainty_service import uncertainty_service
from app.utils.validation import validate_coordinates, validate_forecast_hours

router = APIRouter(prefix="/api/v1", tags=["Uncertainty"])


@router.get(
    "/uncertainty",
    response_model=UncertaintyResponse,
    summary="Get forecast uncertainty bounds",
    description="Returns estimated multi-model ensemble spread, confidence intervals (lower and upper bounds), and regime calibration details.",
)
async def get_forecast_uncertainty(
    lat: Optional[float] = Query(default=None, description="Latitude (-90.0 to 90.0)"),
    lon: Optional[float] = Query(default=None, description="Longitude (-180.0 to 180.0)"),
    hours: Optional[int] = Query(default=24, description="Horizon in hours"),
    location: Optional[str] = Query(default=None, description="Named Indian location"),
) -> UncertaintyResponse:
    validated_lat, validated_lon, loc_name = validate_coordinates(lat, lon, location)
    horizon = validate_forecast_hours(forecast_hours=hours)

    _, om_pts, ai_pts, nwp_pts, regimes = await forecast_service.get_forecast(
        lat=validated_lat,
        lon=validated_lon,
        forecast_hours=horizon,
        location_name=loc_name,
        blend=True,
    )

    return uncertainty_service.compute_series_uncertainty(
        location=loc_name,
        open_meteo_points=om_pts,
        ai_points=ai_pts,
        nwp_points=nwp_pts,
        regimes=regimes,
    )
