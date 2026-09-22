"""Extreme weather detection and event clustering service."""

from typing import List, Dict, Any, Optional
from app.data.demo_data import DEMO_THRESHOLDS
from app.schemas.extremes import ExtremeEvent, ExtremesResponse
from app.schemas.forecast import ForecastPoint


class ExtremeEventService:
    """Detects and clusters meteorological extremes across the forecast horizon."""

    def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
        self.thresholds = thresholds or DEMO_THRESHOLDS

    def detect_extremes_in_forecast(
        self,
        forecast_points: List[ForecastPoint],
        location_name: str = "Location",
    ) -> ExtremesResponse:
        """
        Scan time-series forecast points for threshold exceedances and cluster into events.
        """
        events: List[ExtremeEvent] = []
        if not forecast_points:
            return ExtremesResponse(events=[], analyzed_hours=0, location=location_name)

        heat_thresh = self.thresholds["EXTREME_HEAT"]["temperature_c"]
        cold_thresh = self.thresholds["EXTREME_COLD"]["temperature_c"]
        rain_thresh = self.thresholds["HEAVY_RAIN"]["precipitation_mm"]
        wind_thresh = self.thresholds["HIGH_WIND"]["wind_speed_kmh"]

        # Track ongoing sequences
        current_heat_seq: List[ForecastPoint] = []
        current_cold_seq: List[ForecastPoint] = []
        current_rain_seq: List[ForecastPoint] = []
        current_wind_seq: List[ForecastPoint] = []

        def finalize_seq(seq: List[ForecastPoint], event_type: str, metric: str, thresh: float, severity: str):
            if not seq:
                return
            if metric == "temperature_c":
                if event_type == "EXTREME_HEAT":
                    peak = max(p.temperature_c for p in seq)
                else:
                    peak = min(p.temperature_c for p in seq)
            elif metric == "precipitation_mm":
                peak = max((p.precipitation_mm or 0.0) for p in seq)
            elif metric == "wind_speed_kmh":
                peak = max(p.wind_speed_kmh for p in seq)
            else:
                peak = 0.0

            signals = [
                f"Peak {metric} reached {peak:.1f}, exceeding configured demonstration threshold of {thresh}",
                f"Duration: {len(seq)} consecutive forecast hours",
            ]

            events.append(
                ExtremeEvent(
                    type=event_type,
                    severity=severity,
                    start=seq[0].time,
                    end=seq[-1].time,
                    peak_value=round(peak, 1),
                    location=location_name,
                    threshold=thresh,
                    metric=metric,
                    signals=signals,
                    is_official_warning=False,
                )
            )

        for p in forecast_points:
            # Heat
            if p.temperature_c >= heat_thresh:
                current_heat_seq.append(p)
            else:
                if current_heat_seq:
                    finalize_seq(current_heat_seq, "EXTREME_HEAT", "temperature_c", heat_thresh, "HIGH")
                    current_heat_seq = []

            # Cold
            if p.temperature_c <= cold_thresh:
                current_cold_seq.append(p)
            else:
                if current_cold_seq:
                    finalize_seq(current_cold_seq, "EXTREME_COLD", "temperature_c", cold_thresh, "MEDIUM")
                    current_cold_seq = []

            # Rain
            if (p.precipitation_mm or 0.0) >= rain_thresh:
                current_rain_seq.append(p)
            else:
                if current_rain_seq:
                    finalize_seq(current_rain_seq, "HEAVY_RAIN", "precipitation_mm", rain_thresh, "HIGH")
                    current_rain_seq = []

            # Wind
            if p.wind_speed_kmh >= wind_thresh:
                current_wind_seq.append(p)
            else:
                if current_wind_seq:
                    finalize_seq(current_wind_seq, "HIGH_WIND", "wind_speed_kmh", wind_thresh, "HIGH")
                    current_wind_seq = []

        # Flush any open sequences at end of series
        if current_heat_seq:
            finalize_seq(current_heat_seq, "EXTREME_HEAT", "temperature_c", heat_thresh, "HIGH")
        if current_cold_seq:
            finalize_seq(current_cold_seq, "EXTREME_COLD", "temperature_c", cold_thresh, "MEDIUM")
        if current_rain_seq:
            finalize_seq(current_rain_seq, "HEAVY_RAIN", "precipitation_mm", rain_thresh, "HIGH")
        if current_wind_seq:
            finalize_seq(current_wind_seq, "HIGH_WIND", "wind_speed_kmh", wind_thresh, "HIGH")

        return ExtremesResponse(
            events=events,
            analyzed_hours=len(forecast_points),
            location=location_name,
            threshold_basis="configured demonstration thresholds",
        )


extreme_event_service = ExtremeEventService()
