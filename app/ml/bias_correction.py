"""Statistical and empirical bias correction engine.

Provides systematic error reduction on raw ensemble model forecasts using
climatological mean error offsets, elevation-lapse-rate adjustments, and diurnal rolling bias.
"""

from typing import Dict, Any, Optional


class StatisticalBiasCorrector:
    """
    Transparent statistical bias correction.
    Corrects systematic over/under-prediction in temperature, wind, and precipitation.
    """

    def __init__(self):
        # Climatological mean bias estimates across Indian subcontinent for raw model feeds
        self.standard_offsets = {
            "temperature_c": -0.2,       # Raw models tend to exhibit slight warm bias in tropics
            "humidity": 1.5,             # Slight dry bias in standard boundary layers
            "wind_speed_kmh": -0.4,      # Over-prediction of surface wind in urban canopy
            "pressure_hpa": 0.0,
        }

    def correct_forecast_value(
        self,
        variable_name: str,
        predicted_value: float,
        elevation_m: float = 100.0,
        hour_of_day: Optional[int] = None,
        observed_reference: Optional[float] = None,
    ) -> float:
        """
        Apply additive mean bias correction and lapse rate adjustment.
        """
        corrected = predicted_value

        # 1. Climatological additive offset
        if variable_name in self.standard_offsets:
            corrected += self.standard_offsets[variable_name]

        # 2. Elevation lapse rate adjustment for temperature
        # Standard environmental lapse rate ~ 6.5°C per 1000m (0.0065°C/m)
        if variable_name == "temperature_c" and elevation_m > 300.0:
            # Adjust if model grid elevation differs from true station elevation
            excess_elevation = max(0.0, elevation_m - 300.0)
            corrected -= excess_elevation * 0.003  # moderate topographic correction factor

        # 3. Observation nudging if reference point available
        if observed_reference is not None:
            # Alpha smoothing towards recent ground observation
            alpha = 0.3
            residual_bias = predicted_value - observed_reference
            corrected = predicted_value - (alpha * residual_bias)

        # 4. Physical boundaries
        if variable_name == "humidity":
            corrected = max(0.0, min(100.0, corrected))
        elif variable_name in ("wind_speed_kmh", "precipitation_mm"):
            corrected = max(0.0, corrected)

        return round(corrected, 1)


bias_corrector = StatisticalBiasCorrector()
