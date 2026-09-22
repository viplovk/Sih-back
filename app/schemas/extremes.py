"""Pydantic schemas for extreme meteorological events."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ExtremeEvent(BaseModel):
    type: str = Field(..., json_schema_extra={"example": "EXTREME_HEAT"})
    severity: str = Field(..., json_schema_extra={"example": "HIGH"})
    start: str = Field(..., json_schema_extra={"example": "2026-09-22T11:00:00Z"})
    end: str = Field(..., json_schema_extra={"example": "2026-09-22T17:00:00Z"})
    peak_value: float = Field(..., json_schema_extra={"example": 42.3})
    location: str = Field(..., json_schema_extra={"example": "Delhi"})
    threshold: Optional[float] = Field(default=40.0, json_schema_extra={"example": 40.0})
    metric: Optional[str] = Field(default="temperature_c", json_schema_extra={"example": "temperature_c"})
    signals: Optional[List[str]] = Field(
        default_factory=list,
        json_schema_extra={"example": ["exceeds heatwave threshold of 40°C", "sustained peak solar hours"]}
    )
    is_official_warning: bool = Field(
        default=False,
        json_schema_extra={"example": False},
        description="False for configured demonstration thresholds; True only when backed by official IMD feed."
    )


class ExtremesResponse(BaseModel):
    events: List[ExtremeEvent]
    analyzed_hours: int = Field(default=72, json_schema_extra={"example": 72})
    location: Optional[str] = Field(default=None, json_schema_extra={"example": "Delhi"})
    threshold_basis: str = Field(
        default="configured demonstration thresholds",
        json_schema_extra={"example": "configured demonstration thresholds"}
    )
