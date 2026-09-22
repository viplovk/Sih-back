"""Weather service handling live current weather observations and real provider data."""

from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.cache import weather_cache
from app.core.logging import logger
from app.providers.open_meteo import open_meteo_client, get_weather_description
from app.schemas.weather import WeatherResponse, CurrentWeather, LocationInfo
from app.data.city_coordinates import find_nearest_city


class WeatherService:
    """Orchestrates live weather observations, caching, and freshness validation."""

    async def get_current_weather(
        self,
        lat: float,
        lon: float,
        location_name: Optional[str] = None,
    ) -> WeatherResponse:
        """
        Fetch real current weather for given coordinates.
        Never generates mock or random data.
        Returns HTTP 503 via WeatherDataUnavailableError if provider fails with no cache.
        """
        nearest_city, dist_km = find_nearest_city(lat, lon)
        resolved_name = location_name or (
            nearest_city.name if dist_km < 35.0 else f"Location ({lat:.2f}, {lon:.2f})"
        )

        key = f"weather:{round(lat, 4)}:{round(lon, 4)}"

        async def _fetcher():
            data, source, valid_time = await open_meteo_client.get_live_weather(lat, lon)
            return data, source, valid_time

        raw_data, meta = await weather_cache.get_or_fetch(
            key, _fetcher, ttl_seconds=settings.LIVE_CACHE_TTL_SECONDS
        )

        current_raw = raw_data.get("current", {})
        observed_time = current_raw.get("time", meta.get("valid_time", ""))
        w_code = int(current_raw.get("weather_code", 0))
        w_desc = get_weather_description(w_code)

        temp_c = float(current_raw.get("temperature_2m", 0.0))
        apparent_temp_c = float(current_raw.get("apparent_temperature", temp_c))
        humidity = int(current_raw.get("relative_humidity_2m", 0))
        wind_speed = float(current_raw.get("wind_speed_10m", 0.0))
        wind_dir = float(current_raw.get("wind_direction_10m", 0.0))
        wind_gusts = (
            float(current_raw.get("wind_gusts_10m"))
            if current_raw.get("wind_gusts_10m") is not None
            else None
        )
        pressure = float(current_raw.get("surface_pressure", 1013.0))
        precipitation = float(current_raw.get("precipitation", 0.0))
        rain = float(current_raw.get("rain", precipitation))
        cloud_cover = int(current_raw.get("cloud_cover", 0))

        location = LocationInfo(
            name=resolved_name,
            latitude=lat,
            longitude=lon,
            lat=lat,
            lon=lon,
            state=nearest_city.state if dist_km < 35.0 else None,
            elevation_m=nearest_city.elevation_m if dist_km < 35.0 else None,
        )

        current_nested = CurrentWeather(
            time=observed_time,
            temperature_c=temp_c,
            feels_like_c=apparent_temp_c,
            humidity=humidity,
            wind_speed_kmh=wind_speed,
            wind_direction_deg=wind_dir,
            pressure_hpa=pressure,
            precipitation_mm=precipitation,
            weather_code=w_code,
            weather_description=w_desc,
        )

        return WeatherResponse(
            source=meta.get("source", "open-meteo"),
            location=location,
            mode="live",
            observed_at=observed_time,
            temperature=temp_c,
            temperature_c=temp_c,
            feels_like=apparent_temp_c,
            feels_like_c=apparent_temp_c,
            humidity=humidity,
            pressure=pressure,
            pressure_hpa=pressure,
            wind_speed=wind_speed,
            wind_speed_kmh=wind_speed,
            wind_direction=wind_dir,
            wind_direction_deg=wind_dir,
            wind_gusts=wind_gusts,
            precipitation=precipitation,
            precipitation_mm=precipitation,
            rain=rain,
            cloud_cover=cloud_cover,
            weather_code=w_code,
            weather_description=w_desc,
            fetched_at=meta.get("fetched_at", ""),
            valid_time=meta.get("valid_time", observed_time),
            stale=meta.get("stale", False),
            age_seconds=meta.get("age_seconds", 0),
            current=current_nested,
            retrieved_at=meta.get("fetched_at", ""),
        )


weather_service = WeatherService()
