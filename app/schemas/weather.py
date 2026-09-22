"""Pydantic schemas for raw and processed weather observations."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LocationInfo(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Delhi"})
    lat: float = Field(..., json_schema_extra={"example": 28.6139})
    lon: float = Field(..., json_schema_extra={"example": 77.2090})
    state: Optional[str] = Field(default=None, json_schema_extra={"example": "Delhi"})
    elevation_m: Optional[float] = Field(default=None, json_schema_extra={"example": 216.0})


class CurrentWeather(BaseModel):
    time: str = Field(..., json_schema_extra={"example": "2026-09-22T10:00:00Z"})
    temperature_c: float = Field(..., json_schema_extra={"example": 32.4})
    feels_like_c: float = Field(..., json_schema_extra={"example": 34.1})
    humidity: int = Field(..., json_schema_extra={"example": 55})
    wind_speed_kmh: float = Field(..., json_schema_extra={"example": 12.5})
    wind_direction_deg: Optional[float] = Field(default=None, json_schema_extra={"example": 280.0})
    pressure_hpa: float = Field(..., json_schema_extra={"example": 1006.2})
    precipitation_mm: float = Field(default=0.0, json_schema_extra={"example": 0.0})
    weather_code: int = Field(..., json_schema_extra={"example": 1})
    weather_description: Optional[str] = Field(default="Mainly Clear", json_schema_extra={"example": "Mainly Clear"})


class WeatherResponse(BaseModel):
    location: LocationInfo
    current: CurrentWeather
    source: str = Field(default="Open-Meteo", json_schema_extra={"example": "Open-Meteo"})
    retrieved_at: str
