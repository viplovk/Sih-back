"""Consistent API exceptions and error models."""

import uuid
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class AlgoriotException(HTTPException):
    """Base exception for all domain errors in Algoriot backend."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_SERVER_ERROR",
        message: str = "An unexpected error occurred",
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.request_id = request_id or str(uuid.uuid4())
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "code": self.code,
            "message": self.message,
            "request_id": self.request_id,
        }
        if self.details:
            payload["details"] = self.details
        return {"error": payload}

    def to_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.status_code, content=self.to_dict())


class WeatherProviderError(AlgoriotException):
    """Raised when external weather data provider (Open-Meteo) fails."""

    def __init__(
        self,
        message: str = "Weather provider temporarily unavailable",
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="WEATHER_PROVIDER_ERROR",
            message=message,
            request_id=request_id,
            details=details,
        )


class LocationNotFoundError(AlgoriotException):
    """Raised when requested location is unknown or out of bounds."""

    def __init__(
        self,
        message: str = "Location not found or coordinates invalid",
        request_id: Optional[str] = None,
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="LOCATION_NOT_FOUND",
            message=message,
            request_id=request_id,
        )


class InvalidCoordinatesError(AlgoriotException):
    """Raised when latitude or longitude is invalid."""

    def __init__(
        self,
        message: str = "Latitude must be between -90 and 90, longitude between -180 and 180",
        request_id: Optional[str] = None,
    ):
        super().__init__(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            code="INVALID_COORDINATES",
            message=message,
            request_id=request_id,
        )


class ValidationError(AlgoriotException):
    """Raised when general parameter validation fails."""

    def __init__(
        self,
        message: str = "Invalid request parameters",
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            code="VALIDATION_ERROR",
            message=message,
            request_id=request_id,
            details=details,
        )


class ModelInferenceError(AlgoriotException):
    """Raised when model inference or blending calculation encounters an issue."""

    def __init__(
        self,
        message: str = "Model blending failed during forecast execution",
        request_id: Optional[str] = None,
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="MODEL_INFERENCE_ERROR",
            message=message,
            request_id=request_id,
        )
