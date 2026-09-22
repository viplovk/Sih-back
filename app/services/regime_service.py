"""Regime detection service."""

from typing import Dict, Any
from app.ml.regime_detector import regime_detector


class RegimeService:
    def detect(
        self,
        temperature_c: float,
        humidity: float,
        wind_speed_kmh: float,
        pressure_hpa: float,
        precipitation_mm: float,
        weather_code: int = 0,
        apparent_temperature_c: float = 30.0,
    ) -> Dict[str, Any]:
        return regime_detector.detect_regime(
            temperature_c=temperature_c,
            humidity=humidity,
            wind_speed_kmh=wind_speed_kmh,
            pressure_hpa=pressure_hpa,
            precipitation_mm=precipitation_mm,
            weather_code=weather_code,
            apparent_temperature_c=apparent_temperature_c,
        )


regime_service = RegimeService()
