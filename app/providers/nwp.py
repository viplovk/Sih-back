"""Physics-based Numerical Weather Prediction (NWP) model adapter.

SCIENTIFIC HONESTY NOTE:
This is a demonstration adapter clearly marked as SIMULATED. It generates deterministic
synthetic NWP predictions (resembling high-resolution WRF/GFS physics models with
diurnal temperature amplitudes and physical hydrostatic lapse rates) based on real baseline
conditions. It allows the multi-model blending pipeline to be tested and benchmarked
before connecting live ECMWF/NCMRWF/GFS binary GRIB2 streams.
"""

import math
from typing import Dict, Any, List, Optional
from app.providers.base import ForecastModel
from app.schemas.forecast import ForecastPoint
from app.providers.open_meteo import get_weather_description


class DemoNWPModel(ForecastModel):
    """
    Simulated NWP Model Adapter.
    Characteristics:
    - Slightly higher thermal amplitude during day, cooler nocturnal minima (radiative cooling).
    - Conservative convective precipitation threshold.
    - Explicitly marked as SIMULATED.
    """

    def __init__(self):
        super().__init__(
            model_id="demo-nwp",
            name="NWP Demo",
            model_type="NWP",
            status="SIMULATED",
            is_demo=True,
            metadata={
                "description": "Simulated High-Resolution Numerical Weather Prediction (physics-based).",
                "grid_resolution": "0.1 degree (simulated)",
                "physics_core": "Eulerian hydrostatic primitive equations (simulated)",
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

            # Deterministic diurnal physics perturbation based on forecast hour index
            hour_mod = i % 24
            diurnal_factor = math.sin((hour_mod - 6) / 24.0 * 2.0 * math.pi)
            # NWP models often predict sharper diurnal swings (+0.6C at peak afternoon, -0.5C at dawn)
            t_nwp = round(t_base + 0.6 * diurnal_factor - 0.2, 1)
            feels_like = round(t_nwp + (0.3 if h_base > 65 else -0.2), 1)
            # Pressure variation
            p_nwp = round(p_base + 0.5 * math.cos(hour_mod / 12.0 * math.pi), 1)
            # Wind typically slightly higher in raw NWP gradient
            w_nwp = round(max(0.0, w_base * 1.05 + 0.4 * diurnal_factor), 1)
            # Precipitation with slightly higher peak localized intensity
            prec_nwp = round(prec_base * 1.1 if prec_base > 0.5 else prec_base, 1)
            prec_prob = min(100, int(prec_nwp * 18)) if prec_nwp > 0 else 10

            points.append(
                ForecastPoint(
                    time=times[i],
                    temperature_c=t_nwp,
                    feels_like_c=feels_like,
                    humidity=int(h_base),
                    wind_speed_kmh=w_nwp,
                    pressure_hpa=p_nwp,
                    precipitation_probability=prec_prob,
                    precipitation_mm=prec_nwp,
                    weather_code=c_base,
                    weather_description=get_weather_description(c_base),
                )
            )

        return points
