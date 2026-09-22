"""Pydantic schemas for map spatial layers: timeline, wind, temperature, precipitation, air quality."""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class TimelineFrame(BaseModel):
    timestamp: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    mode: str = Field(..., json_schema_extra={"example": "live"})


class TimelineResponse(BaseModel):
    source: str = Field(default="open-meteo", json_schema_extra={"example": "open-meteo"})
    generated_at: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    current_time: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    frames: List[TimelineFrame]
    stale: bool = Field(default=False, json_schema_extra={"example": False})
    fetched_at: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    age_seconds: int = Field(default=0, json_schema_extra={"example": 10})


class MapBBox(BaseModel):
    north: float = Field(default=37.0, json_schema_extra={"example": 37.0})
    south: float = Field(default=6.0, json_schema_extra={"example": 6.0})
    west: float = Field(default=68.0, json_schema_extra={"example": 68.0})
    east: float = Field(default=98.0, json_schema_extra={"example": 98.0})


class WindGridResponse(BaseModel):
    source: str = Field(default="open-meteo", json_schema_extra={"example": "open-meteo"})
    mode: str = Field(default="live", json_schema_extra={"example": "live"})
    valid_time: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    requested_valid_time: Optional[str] = Field(default=None, json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    actual_valid_time: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    bbox: MapBBox = Field(default_factory=MapBBox)
    width: int = Field(..., json_schema_extra={"example": 80})
    height: int = Field(..., json_schema_extra={"example": 80})
    latitudes: List[float]
    longitudes: List[float]
    u: List[List[float]]
    v: List[List[float]]
    speed: List[List[float]]
    direction: List[List[float]]
    unit: str = Field(default="km/h", json_schema_extra={"example": "km/h"})
    stale: bool = Field(default=False, json_schema_extra={"example": False})
    fetched_at: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    age_seconds: int = Field(default=0, json_schema_extra={"example": 10})


class TemperaturePoint(BaseModel):
    lat: float
    lon: float
    temperature_c: float


class TemperatureGridResponse(BaseModel):
    source: str = Field(default="open-meteo", json_schema_extra={"example": "open-meteo"})
    mode: str = Field(default="live", json_schema_extra={"example": "live"})
    valid_time: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    requested_valid_time: Optional[str] = Field(default=None, json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    actual_valid_time: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    bbox: MapBBox = Field(default_factory=MapBBox)
    width: int = Field(..., json_schema_extra={"example": 80})
    height: int = Field(..., json_schema_extra={"example": 80})
    latitudes: List[float]
    longitudes: List[float]
    values: List[List[float]]
    unit: str = Field(default="°C", json_schema_extra={"example": "°C"})
    min: float = Field(..., json_schema_extra={"example": 14.2})
    max: float = Field(..., json_schema_extra={"example": 38.6})
    stale: bool = Field(default=False, json_schema_extra={"example": False})
    fetched_at: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    age_seconds: int = Field(default=0, json_schema_extra={"example": 10})

    # Backward compatibility with earlier prototype format
    timestamp: Optional[str] = None
    min_temperature_c: Optional[float] = None
    max_temperature_c: Optional[float] = None
    grid: Optional[List[TemperaturePoint]] = None


class PrecipitationGridResponse(BaseModel):
    source: str = Field(default="open-meteo", json_schema_extra={"example": "open-meteo"})
    mode: str = Field(default="live", json_schema_extra={"example": "live"})
    valid_time: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    requested_valid_time: Optional[str] = Field(default=None, json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    actual_valid_time: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    bbox: MapBBox = Field(default_factory=MapBBox)
    width: int = Field(..., json_schema_extra={"example": 80})
    height: int = Field(..., json_schema_extra={"example": 80})
    latitudes: List[float]
    longitudes: List[float]
    values: List[List[float]]
    unit: str = Field(default="mm", json_schema_extra={"example": "mm"})
    min: float = Field(..., json_schema_extra={"example": 0.0})
    max: float = Field(..., json_schema_extra={"example": 12.4})
    stale: bool = Field(default=False, json_schema_extra={"example": False})
    fetched_at: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    age_seconds: int = Field(default=0, json_schema_extra={"example": 10})


class AirQualityGridResponse(BaseModel):
    source: str = Field(default="open-meteo-air-quality", json_schema_extra={"example": "open-meteo-air-quality"})
    mode: str = Field(default="live", json_schema_extra={"example": "live"})
    valid_time: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    requested_valid_time: Optional[str] = Field(default=None, json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    actual_valid_time: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    bbox: MapBBox = Field(default_factory=MapBBox)
    width: int = Field(..., json_schema_extra={"example": 80})
    height: int = Field(..., json_schema_extra={"example": 80})
    latitudes: List[float]
    longitudes: List[float]
    aqi: List[List[float]]
    pm2_5: List[List[float]]
    pm10: List[List[float]]
    no2: List[List[float]]
    o3: List[List[float]]
    min: float = Field(..., json_schema_extra={"example": 32.0})
    max: float = Field(..., json_schema_extra={"example": 240.0})
    stale: bool = Field(default=False, json_schema_extra={"example": False})
    fetched_at: str = Field(..., json_schema_extra={"example": "2026-09-22T17:15:00Z"})
    age_seconds: int = Field(default=0, json_schema_extra={"example": 10})
