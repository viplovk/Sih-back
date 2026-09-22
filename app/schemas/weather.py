"""Pydantic schemas for real live and current weather observations."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class LocationInfo(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Delhi"})
    latitude: float = Field(..., json_schema_extra={"example": 28.6139})
    longitude: float = Field(..., json_schema_extra={"example": 77.2090})
    lat: float = Field(..., json_schema_extra={"example": 28.6139})
    lon: float = Field(..., json_schema_extra={"example": 77.2090})
    state: Optional[str] = Field(default=None, json_schema_extra={"example": "Delhi"})
    elevation_m: Optional[float] = Field(default=None, json_schema_extra={"example": 216.0})


class CurrentWeather(BaseModel):
    time: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
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
    source: str = Field(default="open-meteo", json_schema_extra={"example": "open-meteo"})
    location: LocationInfo
    mode: str = Field(default="live", json_schema_extra={"example": "live"})
    observed_at: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15"})

    # Core weather variables
    temperature: float = Field(..., json_schema_extra={"example": 32.4})
    temperature_c: Optional[float] = Field(default=None, json_schema_extra={"example": 32.4})
    feels_like: Optional[float] = Field(default=None, json_schema_extra={"example": 34.1})
    feels_like_c: Optional[float] = Field(default=None, json_schema_extra={"example": 34.1})
    humidity: int = Field(..., json_schema_extra={"example": 55})
    pressure: float = Field(..., json_schema_extra={"example": 1006.2})
    pressure_hpa: Optional[float] = Field(default=None, json_schema_extra={"example": 1006.2})
    wind_speed: float = Field(..., json_schema_extra={"example": 12.5})
    wind_speed_kmh: Optional[float] = Field(default=None, json_schema_extra={"example": 12.5})
    wind_direction: float = Field(..., json_schema_extra={"example": 280.0})
    wind_direction_deg: Optional[float] = Field(default=None, json_schema_extra={"example": 280.0})
    wind_gusts: Optional[float] = Field(default=None, json_schema_extra={"example": 18.2})
    precipitation: float = Field(default=0.0, json_schema_extra={"example": 0.0})
    precipitation_mm: Optional[float] = Field(default=0.0, json_schema_extra={"example": 0.0})
    rain: float = Field(default=0.0, json_schema_extra={"example": 0.0})
    cloud_cover: int = Field(default=0, json_schema_extra={"example": 25})
    weather_code: int = Field(..., json_schema_extra={"example": 1})
    weather_description: str = Field(default="Mainly Clear", json_schema_extra={"example": "Mainly Clear"})

    # Freshness metadata
    fetched_at: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:30Z"})
    valid_time: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15"})
    stale: bool = Field(default=False, json_schema_extra={"example": False})
    age_seconds: int = Field(default=0, json_schema_extra={"example": 15})

    # Backward compatibility nested current
    current: Optional[CurrentWeather] = None
    retrieved_at: Optional[str] = None
