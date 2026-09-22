"""Pydantic schemas for ensemble uncertainty bounds and calibration."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class UncertaintyPoint(BaseModel):
    time: str = Field(..., json_schema_extra={"example": "2026-09-22T12:00:00Z"})
    prediction_c: float = Field(..., json_schema_extra={"example": 32.4})
    lower_c: float = Field(..., json_schema_extra={"example": 30.9})
    upper_c: float = Field(..., json_schema_extra={"example": 34.1})
    uncertainty_c: float = Field(..., json_schema_extra={"example": 3.2})
    regime: str = Field(..., json_schema_extra={"example": "NORMAL"})
    contributing_models: List[str] = Field(
        default_factory=lambda: ["Open-Meteo", "AI-Demo", "NWP-Demo"],
        json_schema_extra={"example": ["Open-Meteo", "AI-Demo", "NWP-Demo"]}
    )
    calibration_status: str = Field(
        default="estimated uncertainty",
        json_schema_extra={"example": "estimated uncertainty"}
    )


class UncertaintyResponse(BaseModel):
    location: str = Field(..., json_schema_extra={"example": "Delhi"})
    timestamp: str = Field(..., json_schema_extra={"example": "2026-09-22T12:00:00Z"})
    prediction_c: float = Field(..., json_schema_extra={"example": 32.4})
    lower_c: float = Field(..., json_schema_extra={"example": 30.9})
    upper_c: float = Field(..., json_schema_extra={"example": 34.1})
    uncertainty_c: float = Field(..., json_schema_extra={"example": 3.2})
    regime: str = Field(..., json_schema_extra={"example": "NORMAL"})
    contributing_models: List[str] = Field(
        default_factory=lambda: ["Open-Meteo", "AI-Demo", "NWP-Demo"],
        json_schema_extra={"example": ["Open-Meteo", "AI-Demo", "NWP-Demo"]}
    )
    time_series: Optional[List[UncertaintyPoint]] = None
    calibration_note: str = Field(
        default="estimated uncertainty - statistical calibration awaiting operational verification dataset",
        json_schema_extra={"example": "estimated uncertainty - statistical calibration awaiting operational verification dataset"}
    )
