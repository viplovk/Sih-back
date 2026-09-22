"""Simulated Foundation AI Weather Model Adapter (GraphCast / Pangu Architecture).

SCIENTIFIC HONESTY NOTE:
This is a demonstration adapter clearly marked as SIMULATED. It generates deterministic
synthetic AI model predictions (resembling GraphCast/Pangu-Weather spatio-temporal graph
neural network rollouts with characteristic smooth synoptic gradients) based on real baseline
conditions. It allows evaluating the meta-learning dynamic weighting and ensemble architecture
prior to integrating large foundation model weights.
"""

import math
from typing import Dict, Any, List, Optional
from app.providers.base import ForecastModel
from app.schemas.forecast import ForecastPoint
from app.providers.open_meteo import get_weather_description


class DemoAIModel(ForecastModel):
    """
    Simulated AI Foundation Model Adapter.
    Characteristics:
    - Slightly smoother temporal temperature variations (reduced extreme noise).
    - Excellent synoptic wind field coherence.
    - Slower precipitation onset with slightly diffuse probability envelope.
    - Explicitly marked as SIMULATED.
    """

    def __init__(self):
        super().__init__(
            model_id="demo-ai",
            name="AI Forecast Demo",
            model_type="AI",
            status="SIMULATED",
            is_demo=True,
            metadata={
                "description": "Simulated foundation AI model (GraphCast / Pangu architecture adapter).",
                "backbone": "Graph Neural Network / Hierarchical Transformer (simulated)",
                "lead_time_efficiency": "High",
            },
        )

    async def forecast(
        self,
        lat: float,
        lon: float,
        forecast_hours: int = 72,
        base_observations: Optional[Dict[str, Any]] = None,
    ) -> List[ForecastPoint]:
        if not base_observations or "hourly" not in base_observations:
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            times = [(now + timedelta(hours=h)).strftime("%Y-%m-%dT%H:00:00Z") for h in range(forecast_hours)]
            temps = [30.0 for _ in range(forecast_hours)]
            humids = [55 for _ in range(forecast_hours)]
            winds = [12.0 for _ in range(forecast_hours)]
            pressures = [1010.0 for _ in range(forecast_hours)]
            precips = [0.0 for _ in range(forecast_hours)]
            codes = [1 for _ in range(forecast_hours)]
        else:
            hourly = base_observations["hourly"]
            times = hourly.get("time", [])[:forecast_hours]
            temps = hourly.get("temperature_2m", [])[:forecast_hours]
            humids = hourly.get("relative_humidity_2m", [])[:forecast_hours]
            winds = hourly.get("wind_speed_10m", [])[:forecast_hours]
            pressures = hourly.get("surface_pressure", [])[:forecast_hours]
            precips = hourly.get("precipitation", [])[:forecast_hours]
            codes = hourly.get("weather_code", [])[:forecast_hours]

        points: List[ForecastPoint] = []
        for i in range(len(times)):
            t_base = temps[i] if i < len(temps) and temps[i] is not None else 30.0
            h_base = humids[i] if i < len(humids) and humids[i] is not None else 60
            w_base = winds[i] if i < len(winds) and winds[i] is not None else 10.0
            p_base = pressures[i] if i < len(pressures) and pressures[i] is not None else 1010.0
            prec_base = precips[i] if i < len(precips) and precips[i] is not None else 0.0
            c_base = codes[i] if i < len(codes) and codes[i] is not None else 1

            # AI models exhibit dampening of rapid diurnal extremes and smooth trajectory rollouts
            hour_mod = i % 24
            lead_day = i // 24
            # Slight smooth offset based on location coordinates for deterministic diversity
            coord_seed = math.sin(lat * 0.1) * math.cos(lon * 0.1)
            t_ai = round(t_base - 0.3 * math.sin((hour_mod - 6) / 24.0 * 2.0 * math.pi) + 0.2 * coord_seed, 1)
            feels_like = round(t_ai + (0.4 if h_base > 65 else -0.1), 1)
            p_ai = round(p_base + 0.3 * coord_seed, 1)
            w_ai = round(max(0.0, w_base * 0.98 - 0.2), 1)
            # Smooth rain probability distribution
            prec_ai = round(prec_base * 0.95, 1)
            prec_prob = min(100, int(prec_ai * 22)) if prec_ai > 0 else 5

            points.append(
                ForecastPoint(
                    time=times[i],
                    temperature_c=t_ai,
                    feels_like_c=feels_like,
                    humidity=int(h_base),
                    wind_speed_kmh=w_ai,
                    pressure_hpa=p_ai,
                    precipitation_probability=prec_prob,
                    precipitation_mm=prec_ai,
                    weather_code=c_base,
                    weather_description=get_weather_description(c_base),
                )
            )

        return points
