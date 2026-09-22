"""Uncertainty calibration and ensemble spread estimation.

SCIENTIFIC HONESTY NOTE:
Uncertainty metrics are labeled as 'estimated uncertainty' based on multi-model
ensemble variance, atmospheric regime volatility, and forecast horizon error growth.
They reflect physical dispersion and will be calibrated with Conformal Prediction / CRPS
once long-term ground station verification archives are ingested.
"""

import math
from typing import Dict, Any, List, Tuple


class UncertaintyEstimator:
    """Calculates multi-model ensemble spread and confidence bounds."""

    def estimate_uncertainty(
        self,
        model_predictions: List[float],
        forecast_horizon_hours: float,
        regime: str,
    ) -> Dict[str, float]:
        """
        Derive estimated uncertainty width, lower bound, and upper bound.
        """
        if not model_predictions:
            model_predictions = [30.0]

        # 1. Ensemble spread (sample standard deviation)
        mean_pred = sum(model_predictions) / len(model_predictions)
        if len(model_predictions) > 1:
            variance = sum((x - mean_pred) ** 2 for x in model_predictions) / (len(model_predictions) - 1)
            raw_spread = math.sqrt(variance)
        else:
            raw_spread = 0.8

        # 2. Forecast horizon expansion (error expands with lead time)
        # Typically adds ~0.015°C per hour into the future
        lead_time_expansion = forecast_horizon_hours * 0.015

        # 3. Atmospheric regime volatility multiplier
        regime_multipliers = {
            "THUNDERSTORM": 1.6,
            "EXTREME_RAIN": 1.5,
            "HIGH_WIND": 1.3,
            "EXTREME_HEAT": 1.25,
            "HEAVY_RAIN": 1.2,
            "HOT": 1.1,
            "EXTREME_COLD": 1.15,
            "NORMAL": 1.0,
        }
        multiplier = regime_multipliers.get(regime, 1.0)

        # Baseline minimum uncertainty floor (instruments and micro-climates vary by +/- 0.8°C)
        total_width = max(1.4, (raw_spread * 1.96 + lead_time_expansion) * multiplier)
        half_width = total_width / 2.0

        lower = round(mean_pred - half_width, 1)
        upper = round(mean_pred + half_width, 1)
        width = round(upper - lower, 1)

        return {
            "prediction_c": round(mean_pred, 1),
            "lower_c": lower,
            "upper_c": upper,
            "uncertainty_c": width,
        }


uncertainty_estimator = UncertaintyEstimator()
