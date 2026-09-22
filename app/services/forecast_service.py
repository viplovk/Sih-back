"""Forecast orchestration service synthesizing data providers and hybrid blending."""

from typing import Optional, Dict, Any, List, Tuple
from app.core.logging import logger
from app.providers.open_meteo import open_meteo_client
from app.providers.open_meteo_model import OpenMeteoModel
from app.providers.ai_models import DemoAIModel
from app.providers.nwp import DemoNWPModel
from app.schemas.forecast import ForecastResponse, ForecastPoint, LocationInfo
from app.services.blending_service import blending_engine
from app.data.city_coordinates import find_nearest_city
from app.utils.time import now_utc_iso


class ForecastService:
    """Orchestrates multi-model forecast execution."""

    def __init__(self):
        self.model_open_meteo = OpenMeteoModel()
        self.model_ai = DemoAIModel()
        self.model_nwp = DemoNWPModel()

    async def get_forecast(
        self,
        lat: float,
        lon: float,
        forecast_hours: int = 72,
        location_name: Optional[str] = None,
        blend: bool = True,
    ) -> Tuple[ForecastResponse, List[ForecastPoint], List[ForecastPoint], List[ForecastPoint], List[str]]:
        """
        Produce a forecast for given coordinates.
        Returns: (ForecastResponse, om_points, ai_points, nwp_points, regimes)
        """
        nearest_city, dist_km = find_nearest_city(lat, lon)
        resolved_name = location_name or (
            nearest_city.name if dist_km < 35.0 else f"Location ({lat:.2f}, {lon:.2f})"
        )
        elevation = nearest_city.elevation_m if dist_km < 35.0 else 100.0

        # Retrieve base observations from Open-Meteo
        base_days = min(7, max(1, (forecast_hours // 24) + 1))
        try:
            base_data = await open_meteo_client.get_forecast(lat, lon, forecast_days=base_days)
        except Exception as exc:
            logger.warning(f"Error fetching base data from Open-Meteo: {exc}. Using fallback.")
            base_data = None

        # Execute 3 model streams
        om_points = await self.model_open_meteo.forecast(lat, lon, forecast_hours, base_data)
        ai_points = await self.model_ai.forecast(lat, lon, forecast_hours, base_data)
        nwp_points = await self.model_nwp.forecast(lat, lon, forecast_hours, base_data)

        # Fallback if provider was completely unreachable
        if not om_points:
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            om_points = [
                ForecastPoint(
                    time=(now + timedelta(hours=h)).strftime("%Y-%m-%dT%H:00:00Z"),
                    temperature_c=round(31.0 + 3.0 * (1 if 10 <= (now.hour + h) % 24 <= 16 else -1), 1),
                    feels_like_c=33.0,
                    humidity=55,
                    wind_speed_kmh=12.0,
                    pressure_hpa=1008.0,
                    precipitation_probability=10,
                    precipitation_mm=0.0,
                    weather_code=1,
                    weather_description="Mainly Clear",
                )
                for h in range(forecast_hours)
            ]
            ai_points = await self.model_ai.forecast(lat, lon, forecast_hours, {"hourly": {"time": [p.time for p in om_points]}})
            nwp_points = await self.model_nwp.forecast(lat, lon, forecast_hours, {"hourly": {"time": [p.time for p in om_points]}})

        regimes: List[str] = []
        if blend:
            blended_points, regimes = blending_engine.blend_forecasts(
                lat=lat,
                lon=lon,
                elevation_m=elevation,
                open_meteo_points=om_points,
                ai_points=ai_points,
                nwp_points=nwp_points,
            )
            # Output format matches ForecastPoint schema cleanly for frontend
            forecast_output = [
                ForecastPoint(
                    time=p.time,
                    temperature_c=p.temperature_c,
                    feels_like_c=p.feels_like_c,
                    humidity=p.humidity,
                    wind_speed_kmh=p.wind_speed_kmh,
                    pressure_hpa=p.pressure_hpa,
                    precipitation_probability=p.precipitation_probability,
                    precipitation_mm=p.precipitation_mm,
                    weather_code=p.weather_code,
                    weather_description=p.weather_description,
                )
                for p in blended_points
            ]
            source_tag = "Algoriot Hybrid Multi-Model (Open-Meteo + AI-Demo + NWP-Demo)"
            is_blended = True
        else:
            forecast_output = om_points
            source_tag = "Open-Meteo"
            is_blended = False

        loc_info = LocationInfo(
            name=resolved_name,
            lat=lat,
            lon=lon,
            state=nearest_city.state if dist_km < 35.0 else None,
            elevation_m=elevation,
        )

        resp = ForecastResponse(
            location=loc_info,
            forecast=forecast_output,
            source=source_tag,
            generated_at=now_utc_iso(),
            forecast_horizon_hours=forecast_hours,
            is_blended=is_blended,
        )

        return resp, om_points, ai_points, nwp_points, regimes


forecast_service = ForecastService()
