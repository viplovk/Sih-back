"""Atmospheric weather regime detection engine.

Classifies current or forecasted weather states into distinct meteorological regimes
(NORMAL, HOT, HEAVY_RAIN, THUNDERSTORM, HIGH_WIND, EXTREME_HEAT, EXTREME_RAIN, EXTREME_COLD).
Employs deterministic physics rules with explicit signal traceability and confidence metrics.
"""

from typing import Dict, Any, List, Tuple


class AtmosphericRegimeDetector:
    """
    Transparent rule-based atmospheric regime classifier.
    Designed with modular evaluation so a scikit-learn / XGBoost model can be plugged in.
    """

    @staticmethod
    def detect_regime(
        temperature_c: float,
        humidity: float,
        wind_speed_kmh: float,
        pressure_hpa: float,
        precipitation_mm: float,
        weather_code: int = 0,
        apparent_temperature_c: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Evaluate meteorological parameters and determine primary atmospheric regime.
        Returns regime name, deterministic confidence score (0.0 to 1.0), and active signals.
        """
        signals: List[str] = []
        regime = "NORMAL"
        confidence = 0.85

        # Check Thunderstorm conditions first (convective instability)
        if weather_code in [95, 96, 99]:
            signals.append(f"convective lightning/thunderstorm detected (WMO code {weather_code})")
            if precipitation_mm > 15.0 or wind_speed_kmh > 45.0:
                signals.append("severe convective gust and intense precipitation")
                return {
                    "regime": "THUNDERSTORM",
                    "confidence": 0.94,
                    "signals": signals,
                }
            return {
                "regime": "THUNDERSTORM",
                "confidence": 0.89,
                "signals": signals,
            }

        # Extreme Rain vs Heavy Rain
        if precipitation_mm >= 50.0:
            signals.append(f"extreme precipitation rate ({precipitation_mm:.1f} mm/h >= 50 mm/h threshold)")
            if pressure_hpa < 1000.0:
                signals.append("deep cyclonic depression (pressure < 1000 hPa)")
            return {
                "regime": "EXTREME_RAIN",
                "confidence": min(0.98, 0.88 + (precipitation_mm - 50.0) * 0.002),
                "signals": signals,
            }
        elif precipitation_mm >= 20.0 or weather_code in [65, 82]:
            signals.append(f"heavy precipitation intensity ({precipitation_mm:.1f} mm/h)")
            return {
                "regime": "HEAVY_RAIN",
                "confidence": 0.88,
                "signals": signals,
            }

        # Extreme Heat vs Hot
        if temperature_c >= 42.0 or (temperature_c >= 40.0 and apparent_temperature_c >= 45.0):
            signals.append(f"severe surface heat ({temperature_c:.1f}°C)")
            if apparent_temperature_c >= 45.0:
                signals.append(f"dangerous heat index ({apparent_temperature_c:.1f}°C apparent)")
            return {
                "regime": "EXTREME_HEAT",
                "confidence": min(0.96, 0.85 + (temperature_c - 40.0) * 0.03),
                "signals": signals,
            }
        elif temperature_c >= 37.0:
            signals.append(f"elevated daytime temperature ({temperature_c:.1f}°C)")
            if humidity > 60:
                signals.append("high humidity compound heat stress")
            return {
                "regime": "HOT",
                "confidence": 0.86,
                "signals": signals,
            }

        # High Wind
        if wind_speed_kmh >= 50.0:
            signals.append(f"high surface wind speeds ({wind_speed_kmh:.1f} km/h >= 50 km/h threshold)")
            return {
                "regime": "HIGH_WIND",
                "confidence": min(0.95, 0.85 + (wind_speed_kmh - 50.0) * 0.003),
                "signals": signals,
            }

        # Extreme Cold
        if temperature_c <= 4.0:
            signals.append(f"severe cold wave conditions ({temperature_c:.1f}°C <= 4.0°C threshold)")
            if wind_speed_kmh > 15.0:
                signals.append("elevated wind chill factor")
            return {
                "regime": "EXTREME_COLD",
                "confidence": min(0.95, 0.85 + (4.0 - temperature_c) * 0.03),
                "signals": signals,
            }

        # Normal condition baseline
        signals.append("atmospheric indicators within standard climatological ranges")
        signals.append(f"ambient temperature: {temperature_c:.1f}°C, wind: {wind_speed_kmh:.1f} km/h")
        return {
            "regime": "NORMAL",
            "confidence": 0.88,
            "signals": signals,
        }


regime_detector = AtmosphericRegimeDetector()
