"""Pydantic schemas for geospatial temperature map endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field


class MapGridPoint(BaseModel):
    lat: float = Field(..., json_schema_extra={"example": 28.61})
    lon: float = Field(..., json_schema_extra={"example": 77.21})
    temperature_c: float = Field(..., json_schema_extra={"example": 31.4})
    name: Optional[str] = Field(default=None, json_schema_extra={"example": "Delhi"})


class MapTemperatureResponse(BaseModel):
    timestamp: str = Field(..., json_schema_extra={"example": "2026-09-22T12:00:00Z"})
    source: str = Field(default="Open-Meteo", json_schema_extra={"example": "Open-Meteo"})
    resolution: str = Field(default="demo", json_schema_extra={"example": "demo"})
    grid: List[MapGridPoint]
    min_temperature_c: Optional[float] = Field(default=None, json_schema_extra={"example": 18.5})
    max_temperature_c: Optional[float] = Field(default=None, json_schema_extra={"example": 39.2})
