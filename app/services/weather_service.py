"""Weather service handling current conditions and operational retrieval."""

import time
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.providers.open_meteo import open_meteo_client, get_weather_description
from app.schemas.weather import WeatherResponse, CurrentWeather, LocationInfo
from app.utils.time import now_utc_iso
from app.data.city_coordinates import find_nearest_city


class WeatherService:
    """Orchestrates current weather observations and caching."""

    async def get_current_weather(
        self,
        lat: float,
        lon: float,
        location_name: Optional[str] = None,
    ) -> WeatherResponse:
        """Fetch current weather for given coordinates."""
        nearest_city, dist_km = find_nearest_city(lat, lon)
        resolved_name = location_name or (nearest_city.name if dist_km < 35.0 else f"Location ({lat:.2f}, {lon:.2f})")

        try:
            raw_data = await open_meteo_client.get_forecast(lat, lon, forecast_days=1)
            current_raw = raw_data.get("current", {})

            w_code = current_raw.get("weather_code", 0)
            current = CurrentWeather(
                time=current_raw.get("time", now_utc_iso()),
                temperature_c=round(current_raw.get("temperature_2m", 28.0), 1),
                feels_like_c=round(current_raw.get("apparent_temperature", 29.5), 1),
                humidity=int(current_raw.get("relative_humidity_2m", 50)),
                wind_speed_kmh=round(current_raw.get("wind_speed_10m", 10.0), 1),
                wind_direction_deg=current_raw.get("wind_direction_10m"),
                pressure_hpa=round(current_raw.get("surface_pressure", 1012.0), 1),
                precipitation_mm=round(current_raw.get("precipitation", 0.0), 1),
                weather_code=w_code,
                weather_description=get_weather_description(w_code),
            )
            source = "Open-Meteo"
        except Exception as exc:
            logger.warning(f"Error fetching live weather for ({lat}, {lon}): {exc}. Generating baseline state.")
            # Deterministic offline fallback if provider is down
            current = CurrentWeather(
                time=now_utc_iso(),
                temperature_c=31.2,
                feels_like_c=33.5,
                humidity=58,
                wind_speed_kmh=12.0,
                wind_direction_deg=270.0,
                pressure_hpa=1008.0,
                precipitation_mm=0.0,
                weather_code=1,
                weather_description="Mainly Clear",
            )
            source = "Open-Meteo (Demo Mode Fallback)"

        location = LocationInfo(
            name=resolved_name,
            lat=lat,
            lon=lon,
            state=nearest_city.state if dist_km < 35.0 else None,
            elevation_m=nearest_city.elevation_m if dist_km < 35.0 else None,
        )

        return WeatherResponse(
            location=location,
            current=current,
            source=source,
            retrieved_at=now_utc_iso(),
        )


weather_service = WeatherService()
