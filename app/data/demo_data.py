"""Deterministic baseline constants and offsets for simulated/demo models.

SCIENTIFIC HONESTY NOTE:
These values are mathematical perturbations applied to real baseline data to demonstrate
multi-model ensemble blending, regime sensitivity, and uncertainty calibration during the
SIH MVP demonstration. They are deterministically generated based on latitude, longitude,
forecast horizon, and time of day, ensuring consistent and reproducible responses.
"""

from typing import Dict, Any


DEMO_MODELS_METADATA = [
    {
        "id": "open-meteo",
        "name": "Open-Meteo",
        "type": "weather-provider",
        "status": "active",
        "is_demo": False,
        "description": "Real operational NWP multi-model composite (ECMWF, GFS, ICON).",
        "base_accuracy": 0.88,
    },
    {
        "id": "demo-ai",
        "name": "AI Forecast Demo",
        "type": "AI",
        "status": "SIMULATED",
        "is_demo": True,
        "description": "Simulated foundation AI model (GraphCast / Pangu architecture adapter).",
        "base_accuracy": 0.84,
    },
    {
        "id": "demo-nwp",
        "name": "NWP Demo",
        "type": "NWP",
        "status": "SIMULATED",
        "is_demo": True,
        "description": "Simulated High-Resolution Numerical Weather Prediction (physics-based).",
        "base_accuracy": 0.82,
    },
]


# Configured demonstration thresholds for Indian weather conditions
# NOTE: Configured demonstration thresholds, to be replaced by official IMD warning criteria
DEMO_THRESHOLDS = {
    "EXTREME_HEAT": {
        "temperature_c": 40.0,
        "apparent_temperature_c": 44.0,
        "severity": "HIGH",
    },
    "EXTREME_COLD": {
        "temperature_c": 5.0,
        "severity": "MEDIUM",
    },
    "HEAVY_RAIN": {
        "precipitation_mm": 20.0,
        "severity": "MEDIUM",
    },
    "EXTREME_RAIN": {
        "precipitation_mm": 50.0,
        "severity": "HIGH",
    },
    "HIGH_WIND": {
        "wind_speed_kmh": 50.0,
        "severity": "HIGH",
    },
    "THUNDERSTORM": {
        "weather_codes": [95, 96, 99],
        "severity": "HIGH",
    },
}
