"""Uncertainty analysis and ensemble quantification service."""

from typing import List, Dict, Any, Optional
from app.ml.uncertainty_calibration import uncertainty_estimator
from app.schemas.uncertainty import UncertaintyPoint, UncertaintyResponse
from app.schemas.forecast import ForecastPoint


class UncertaintyService:
    """Computes uncertainty metrics over multi-model forecasts."""

    def compute_point_uncertainty(
        self,
        location: str,
        time_iso: str,
        predictions: List[float],
        forecast_horizon_hours: float,
        regime: str,
    ) -> UncertaintyResponse:
        """Compute estimated uncertainty for a single forecast instant."""
        res = uncertainty_estimator.estimate_uncertainty(
            model_predictions=predictions,
            forecast_horizon_hours=forecast_horizon_hours,
            regime=regime,
        )

        return UncertaintyResponse(
            location=location,
            timestamp=time_iso,
            prediction_c=res["prediction_c"],
            lower_c=res["lower_c"],
            upper_c=res["upper_c"],
            uncertainty_c=res["uncertainty_c"],
            regime=regime,
            contributing_models=["Open-Meteo", "AI-Demo", "NWP-Demo"],
            time_series=None,
            calibration_note="estimated uncertainty - statistical calibration awaiting operational verification dataset",
        )

    def compute_series_uncertainty(
        self,
        location: str,
        open_meteo_points: List[ForecastPoint],
        ai_points: List[ForecastPoint],
        nwp_points: List[ForecastPoint],
        regimes: List[str],
    ) -> UncertaintyResponse:
        """Generate uncertainty bounds for entire time series."""
        time_series: List[UncertaintyPoint] = []
        n = min(len(open_meteo_points), len(ai_points), len(nwp_points))

        for i in range(n):
            preds = [
                open_meteo_points[i].temperature_c,
                ai_points[i].temperature_c,
                nwp_points[i].temperature_c,
            ]
            regime = regimes[i] if i < len(regimes) else "NORMAL"
            res = uncertainty_estimator.estimate_uncertainty(
                model_predictions=preds,
                forecast_horizon_hours=float(i),
                regime=regime,
            )

            time_series.append(
                UncertaintyPoint(
                    time=open_meteo_points[i].time,
                    prediction_c=res["prediction_c"],
                    lower_c=res["lower_c"],
                    upper_c=res["upper_c"],
                    uncertainty_c=res["uncertainty_c"],
                    regime=regime,
                    contributing_models=["Open-Meteo", "AI-Demo", "NWP-Demo"],
                    calibration_status="estimated uncertainty",
                )
            )

        # Baseline summary at horizon = 0
        first_point = time_series[0] if time_series else None
        return UncertaintyResponse(
            location=location,
            timestamp=first_point.time if first_point else "2026-09-22T00:00:00Z",
            prediction_c=first_point.prediction_c if first_point else 30.0,
            lower_c=first_point.lower_c if first_point else 28.5,
            upper_c=first_point.upper_c if first_point else 31.5,
            uncertainty_c=first_point.uncertainty_c if first_point else 3.0,
            regime=first_point.regime if first_point else "NORMAL",
            contributing_models=["Open-Meteo", "AI-Demo", "NWP-Demo"],
            time_series=time_series,
            calibration_note="estimated uncertainty - statistical calibration awaiting operational verification dataset",
        )


uncertainty_service = UncertaintyService()
