"""Operational Open-Meteo model adapter wrapping live composite NWP data."""

from typing import Dict, Any, List, Optional
from app.providers.base import ForecastModel
from app.providers.open_meteo import open_meteo_client, get_weather_description
from app.schemas.forecast import ForecastPoint


class OpenMeteoModel(ForecastModel):
    """Real Operational weather provider adapter."""

    def __init__(self):
        super().__init__(
            model_id="open-meteo",
            name="Open-Meteo",
            model_type="weather-provider",
            status="active",
            is_demo=False,
            metadata={
                "description": "Real operational NWP multi-model composite (ECMWF, GFS, ICON).",
                "source": "Open-Meteo API",
            },
        )

    async def forecast(
        self,
        lat: float,
        lon: float,
        forecast_hours: int = 72,
        base_observations: Optional[Dict[str, Any]] = None,
    ) -> List[ForecastPoint]:
        data = base_observations
        if not data:
            data = await open_meteo_client.get_forecast(lat, lon, forecast_days=max(2, forecast_hours // 24 + 1))

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])[:forecast_hours]
        temps = hourly.get("temperature_2m", [])[:forecast_hours]
        feels = hourly.get("apparent_temperature", [])[:forecast_hours]
        humids = hourly.get("relative_humidity_2m", [])[:forecast_hours]
        winds = hourly.get("wind_speed_10m", [])[:forecast_hours]
        pressures = hourly.get("surface_pressure", [])[:forecast_hours]
        prec_probs = hourly.get("precipitation_probability", [])[:forecast_hours]
        precips = hourly.get("precipitation", [])[:forecast_hours]
        codes = hourly.get("weather_code", [])[:forecast_hours]

        points: List[ForecastPoint] = []
        for i in range(len(times)):
            t = temps[i] if i < len(temps) and temps[i] is not None else 28.0
            fl = feels[i] if i < len(feels) and feels[i] is not None else t
            h = int(humids[i]) if i < len(humids) and humids[i] is not None else 50
            w = winds[i] if i < len(winds) and winds[i] is not None else 10.0
            p = pressures[i] if i < len(pressures) and pressures[i] is not None else 1012.0
            pp = int(prec_probs[i]) if i < len(prec_probs) and prec_probs[i] is not None else 0
            pr = precips[i] if i < len(precips) and precips[i] is not None else 0.0
            c = codes[i] if i < len(codes) and codes[i] is not None else 1

            points.append(
                ForecastPoint(
                    time=times[i],
                    temperature_c=round(t, 1),
                    feels_like_c=round(fl, 1),
                    humidity=h,
                    wind_speed_kmh=round(w, 1),
                    pressure_hpa=round(p, 1),
                    precipitation_probability=pp,
                    precipitation_mm=round(pr, 1),
                    weather_code=c,
                    weather_description=get_weather_description(c),
                )
            )

        return points
