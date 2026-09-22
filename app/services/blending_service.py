"""Hybrid Multi-Model Forecast Blending Engine (Core of ALGORIOT).

Executes the end-to-end scientific pipeline:
  NWP model (simulated) + AI weather model (simulated) + Open-Meteo composite
          ↓
  Atmospheric Feature Preprocessing
          ↓
  Atmospheric Regime Detection
          ↓
  Dynamic Meta-Learner Weighting
          ↓
  Statistical Bias Correction
          ↓
  Extreme Event Peak Preservation
          ↓
  Ensemble Uncertainty Calibration
          ↓
  Final Blended Forecast
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from app.schemas.forecast import ForecastPoint, BlendedForecastPoint
from app.ml.feature_engineering import extract_atmospheric_features
from app.ml.regime_detector import regime_detector
from app.ml.meta_learner import meta_learner
from app.ml.bias_correction import bias_corrector
from app.ml.uncertainty_calibration import uncertainty_estimator
from app.providers.open_meteo import get_weather_description


class HybridBlendingEngine:
    """Core multi-model forecast synthesis engine."""

    def blend_forecasts(
        self,
        lat: float,
        lon: float,
        elevation_m: float,
        open_meteo_points: List[ForecastPoint],
        ai_points: List[ForecastPoint],
        nwp_points: List[ForecastPoint],
    ) -> Tuple[List[BlendedForecastPoint], List[str]]:
        """
        Merge individual forecast streams into a calibrated hybrid forecast.
        """
        blended_series: List[BlendedForecastPoint] = []
        regimes_series: List[str] = []

        total_hours = min(len(open_meteo_points), len(ai_points), len(nwp_points))

        for i in range(total_hours):
            p_om = open_meteo_points[i]
            p_ai = ai_points[i]
            p_nwp = nwp_points[i]

            time_str = p_om.time
            lead_hours = float(i)

            # 1. Feature Preprocessing
            features = extract_atmospheric_features(
                temperature_c=p_om.temperature_c,
                humidity=float(p_om.humidity),
                wind_speed_kmh=p_om.wind_speed_kmh,
                pressure_hpa=p_om.pressure_hpa,
                precipitation_mm=p_om.precipitation_mm or 0.0,
                time_iso=time_str,
                lat=lat,
                lon=lon,
                forecast_horizon_hours=lead_hours,
            )

            # 2. Regime Detection
            regime_result = regime_detector.detect_regime(
                temperature_c=p_om.temperature_c,
                humidity=float(p_om.humidity),
                wind_speed_kmh=p_om.wind_speed_kmh,
                pressure_hpa=p_om.pressure_hpa,
                precipitation_mm=p_om.precipitation_mm or 0.0,
                weather_code=p_om.weather_code,
                apparent_temperature_c=p_om.feels_like_c,
            )
            regime = regime_result["regime"]
            regimes_series.append(regime)

            # 3. Dynamic Model Weighting via Meta-Learner
            weights, explanations = meta_learner.compute_weights(features, regime)
            w_om = weights.get("Open-Meteo", 0.45)
            w_ai = weights.get("AI-Demo", 0.30)
            w_nwp = weights.get("NWP-Demo", 0.25)

            # 4. Weighted multi-model ensemble synthesis
            raw_blended_temp = (
                w_om * p_om.temperature_c
                + w_ai * p_ai.temperature_c
                + w_nwp * p_nwp.temperature_c
            )

            raw_blended_wind = (
                w_om * p_om.wind_speed_kmh
                + w_ai * p_ai.wind_speed_kmh
                + w_nwp * p_nwp.wind_speed_kmh
            )

            raw_blended_pressure = (
                w_om * p_om.pressure_hpa
                + w_ai * p_ai.pressure_hpa
                + w_nwp * p_nwp.pressure_hpa
            )

            raw_blended_precip = (
                w_om * (p_om.precipitation_mm or 0.0)
                + w_ai * (p_ai.precipitation_mm or 0.0)
                + w_nwp * (p_nwp.precipitation_mm or 0.0)
            )

            # 5. Statistical Bias Correction
            corrected_temp = bias_corrector.correct_forecast_value(
                variable_name="temperature_c",
                predicted_value=raw_blended_temp,
                elevation_m=elevation_m,
                hour_of_day=int(features["hour_of_day"]),
            )

            # 6. Extreme Event Handling (avoid smoothing away critical heatwaves or flood rains)
            if regime in ("EXTREME_HEAT", "HOT"):
                # Preserve peak temperature from the highest participating model
                peak_model_temp = max(p_om.temperature_c, p_ai.temperature_c, p_nwp.temperature_c)
                # Nudge towards peak by 40% to prevent disaster under-reporting
                corrected_temp = round(0.6 * corrected_temp + 0.4 * peak_model_temp, 1)

            if regime in ("EXTREME_RAIN", "HEAVY_RAIN"):
                peak_model_precip = max(
                    p_om.precipitation_mm or 0.0,
                    p_ai.precipitation_mm or 0.0,
                    p_nwp.precipitation_mm or 0.0,
                )
                raw_blended_precip = round(0.5 * raw_blended_precip + 0.5 * peak_model_precip, 1)

            # 7. Uncertainty Calibration
            model_temps = [p_om.temperature_c, p_ai.temperature_c, p_nwp.temperature_c]
            unc = uncertainty_estimator.estimate_uncertainty(
                model_predictions=model_temps,
                forecast_horizon_hours=lead_hours,
                regime=regime,
            )

            # Synthesize feels like and weather code
            blended_feels = round(
                corrected_temp + (1.5 if p_om.humidity > 60 else -0.5), 1
            )
            precip_prob = max(
                p_om.precipitation_probability or 0,
                int(raw_blended_precip * 20),
            )
            precip_prob = min(100, precip_prob)

            blended_series.append(
                BlendedForecastPoint(
                    time=time_str,
                    temperature_c=corrected_temp,
                    feels_like_c=blended_feels,
                    humidity=p_om.humidity,
                    wind_speed_kmh=round(raw_blended_wind, 1),
                    pressure_hpa=round(raw_blended_pressure, 1),
                    precipitation_probability=precip_prob,
                    precipitation_mm=round(raw_blended_precip, 1),
                    weather_code=p_om.weather_code,
                    weather_description=get_weather_description(p_om.weather_code),
                    regime=regime,
                    uncertainty_c=unc["uncertainty_c"],
                    lower_bound_c=unc["lower_c"],
                    upper_bound_c=unc["upper_c"],
                    contributing_weights=weights,
                )
            )

        return blended_series, regimes_series


blending_engine = HybridBlendingEngine()
