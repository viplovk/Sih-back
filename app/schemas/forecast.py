"""Pydantic schemas for real single-model and blended forecasts."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.weather import LocationInfo


class ForecastPoint(BaseModel):
    time: str = Field(..., json_schema_extra={"example": "2026-09-22T18:00:00Z"})
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
        json_schema_extra={"example": {"Open-Meteo": 0.45, "AI-Demo": 0.30, "NWP-Demo": 0.25}},
    )


class ForecastFrame(BaseModel):
    timestamp: str = Field(..., json_schema_extra={"example": "2026-09-22T18:00:00Z"})
    valid_time: str = Field(..., json_schema_extra={"example": "2026-09-22T18:00:00Z"})
    temperature: float = Field(..., json_schema_extra={"example": 30.2})
    temperature_c: Optional[float] = Field(default=None, json_schema_extra={"example": 30.2})
    feels_like_c: Optional[float] = Field(default=None, json_schema_extra={"example": 32.1})
    precipitation: float = Field(default=0.0, json_schema_extra={"example": 0.2})
    precipitation_mm: Optional[float] = Field(default=0.0, json_schema_extra={"example": 0.2})
    precipitation_probability: Optional[int] = Field(default=0, json_schema_extra={"example": 20})
    rain: float = Field(default=0.0, json_schema_extra={"example": 0.2})
    humidity: int = Field(..., json_schema_extra={"example": 61})
    pressure: float = Field(..., json_schema_extra={"example": 1008.2})
    pressure_hpa: Optional[float] = Field(default=None, json_schema_extra={"example": 1008.2})
    wind_speed: float = Field(..., json_schema_extra={"example": 14.5})
    wind_speed_kmh: Optional[float] = Field(default=None, json_schema_extra={"example": 14.5})
    wind_direction: float = Field(..., json_schema_extra={"example": 285.0})
    wind_gusts: Optional[float] = Field(default=None, json_schema_extra={"example": 22.0})
    cloud_cover: int = Field(default=0, json_schema_extra={"example": 40})
    weather_code: int = Field(..., json_schema_extra={"example": 2})
    weather_description: str = Field(default="Partly Cloudy", json_schema_extra={"example": "Partly Cloudy"})


class ForecastResponse(BaseModel):
    source: str = Field(default="open-meteo", json_schema_extra={"example": "open-meteo"})
    location: LocationInfo
    mode: str = Field(default="forecast", json_schema_extra={"example": "forecast"})
    fetched_at: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:30Z"})
    valid_time: str = Field(..., json_schema_extra={"example": "2026-09-22T18:00:00Z"})
    stale: bool = Field(default=False, json_schema_extra={"example": False})
    age_seconds: int = Field(default=0, json_schema_extra={"example": 15})

    frames: List[ForecastFrame] = Field(default_factory=list)
    # Backward compatibility with existing forecast point array
    forecast: List[ForecastPoint] = Field(default_factory=list)
    generated_at: Optional[str] = None
    forecast_horizon_hours: Optional[int] = 48
    is_blended: Optional[bool] = False
