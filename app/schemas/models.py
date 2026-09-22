"""Pydantic schemas for participating models and weighting contribution."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    id: str = Field(..., json_schema_extra={"example": "open-meteo"})
    name: str = Field(..., json_schema_extra={"example": "Open-Meteo"})
    type: str = Field(..., json_schema_extra={"example": "weather-provider"})
    status: str = Field(..., json_schema_extra={"example": "active"})
    is_demo: bool = Field(..., json_schema_extra={"example": False})
    description: Optional[str] = Field(default=None)


class ModelsResponse(BaseModel):
    models: List[ModelInfo]


class ModelWeightExplanation(BaseModel):
    regime: str = Field(..., json_schema_extra={"example": "NORMAL"})
    horizon_hours: float = Field(..., json_schema_extra={"example": 24.0})
    primary_factors: List[str] = Field(
        default_factory=list,
        json_schema_extra={"example": ["moderate humidity", "standard diurnal cycle", "mid-range lead time"]}
    )
    confidence: float = Field(default=0.85, json_schema_extra={"example": 0.85})


class ModelContributionResponse(BaseModel):
    available: bool = Field(default=True, json_schema_extra={"example": True})
    message: Optional[str] = None
    source: Optional[str] = None
    location: Optional[str] = Field(default=None, json_schema_extra={"example": "Delhi"})
    time: Optional[str] = Field(default=None, json_schema_extra={"example": "2026-09-22T12:00:00Z"})
    regime: Optional[str] = Field(default=None, json_schema_extra={"example": "NORMAL"})
    weights: Optional[Dict[str, float]] = Field(
        default=None,
        json_schema_extra={"example": {"Open-Meteo": 0.45, "AI-Demo": 0.30, "NWP-Demo": 0.25}}
    )
    reasoning: Optional[ModelWeightExplanation] = None
