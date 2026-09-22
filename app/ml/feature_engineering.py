"""Meteorological feature extraction for dynamic weighting and regime classification."""

import math
from datetime import datetime
from typing import Dict, Any, List
from app.utils.time import parse_iso


def extract_atmospheric_features(
    temperature_c: float,
    humidity: float,
    wind_speed_kmh: float,
    pressure_hpa: float,
    precipitation_mm: float,
    time_iso: str,
    lat: float,
    lon: float,
    forecast_horizon_hours: float = 0.0,
) -> Dict[str, float]:
    """
    Compute structured physics-informed meteorological features.
    Deterministic and explainable.
    """
    dt = parse_iso(time_iso)
    hour = dt.hour
    month = dt.month

    # Diurnal solar cycle proxy: peak at 14:00 (hour 14)
    solar_angle = math.cos((hour - 14.0) / 24.0 * 2.0 * math.pi)

    # Seasonal proxy: peak summer in North India is May-June (month 5-6)
    seasonal_heat_factor = math.cos((month - 6.0) / 12.0 * 2.0 * math.pi)

    # Dew point approximation using Magnus-Tetens formula
    a = 17.27
    b = 237.7
    gamma = ((a * temperature_c) / (b + temperature_c)) + math.log(max(0.01, humidity / 100.0))
    dew_point_c = (b * gamma) / (a - gamma)

    # Vapor pressure deficit proxy
    vpd = max(0.0, (temperature_c - dew_point_c) * 0.1)

    # Barometric tendency proxy from standard sea level (1013.25 hPa)
    pressure_anomaly = pressure_hpa - 1013.25

    return {
        "temperature_c": float(temperature_c),
        "humidity": float(humidity),
        "wind_speed_kmh": float(wind_speed_kmh),
        "pressure_hpa": float(pressure_hpa),
        "precipitation_mm": float(precipitation_mm),
        "forecast_horizon_hours": float(forecast_horizon_hours),
        "hour_of_day": float(hour),
        "month": float(month),
        "lat": float(lat),
        "lon": float(lon),
        "solar_angle": round(solar_angle, 3),
        "seasonal_heat_factor": round(seasonal_heat_factor, 3),
        "dew_point_c": round(dew_point_c, 2),
        "vapor_pressure_deficit": round(vpd, 2),
        "pressure_anomaly": round(pressure_anomaly, 2),
    }
