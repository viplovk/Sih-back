"""Pydantic schemas for single-model and blended forecasts."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.weather import LocationInfo


class ForecastPoint(BaseModel):
    time: str = Field(..., json_schema_extra={"example": "2026-09-22T12:00:00Z"})
    temperature_c: float = Field(..., json_schema_extra={"example": 30.2})
    feels_like_c: float = Field(..., json_schema_extra={"example": 32.1})
    humidity: int = Field(..., json_schema_extra={"example": 62})
    wind_speed_kmh: float = Field(..., json_schema_extra={"example": 14.2})
    pressure_hpa: float = Field(..., json_schema_extra={"example": 1004.5})
    precipitation_probability: Optional[int] = Field(default=20, json_schema_extra={"example": 20})
    precipitation_mm: Optional[float] = Field(default=0.0, json_schema_extra={"example": 0.0})
    weather_code: int = Field(..., json_schema_extra={"example": 2})
    weather_description: Optional[str] = Field(default="Partly Cloudy", json_schema_extra={"example": "Partly Cloudy"})


class BlendedForecastPoint(ForecastPoint):
    regime: Optional[str] = Field(default="NORMAL", json_schema_extra={"example": "NORMAL"})
    uncertainty_c: Optional[float] = Field(default=1.8, json_schema_extra={"example": 1.8})
    lower_bound_c: Optional[float] = Field(default=29.3, json_schema_extra={"example": 29.3})
    upper_bound_c: Optional[float] = Field(default=31.1, json_schema_extra={"example": 31.1})
    contributing_weights: Optional[Dict[str, float]] = Field(
        default=None,
        json_schema_extra={"example": {"Open-Meteo": 0.45, "AI-Demo": 0.30, "NWP-Demo": 0.25}}
    )


class ForecastResponse(BaseModel):
    location: LocationInfo
    forecast: List[ForecastPoint]
    source: str = Field(default="Open-Meteo", json_schema_extra={"example": "Open-Meteo"})
    generated_at: Optional[str] = None
    forecast_horizon_hours: Optional[int] = 72
    is_blended: Optional[bool] = False
