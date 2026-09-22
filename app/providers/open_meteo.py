"""Open-Meteo operational weather provider with HTTPX and TTL caching."""

import time
from typing import Dict, Any, Optional, List
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import WeatherProviderError


WMO_WEATHER_CODES: Dict[int, str] = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",
    77: "Snow Grains",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    85: "Slight Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail",
}


def get_weather_description(code: int) -> str:
    """Map WMO standard weather code to human-readable string."""
    return WMO_WEATHER_CODES.get(code, "Variable Weather")


class OpenMeteoClient:
    """Async HTTPX client for Open-Meteo with in-memory TTL caching."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.OPEN_METEO_BASE_URL
        self._client: Optional[httpx.AsyncClient] = None
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    async def _get_client(self) -> httpx.AsyncClient:
        import asyncio
        loop = asyncio.get_running_loop()
        current_client_loop = getattr(self, "_loop", None)
        if self._client is None or self._client.is_closed or current_client_loop is not loop:
            self._loop = loop
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(8.0, connect=3.0),
                headers={"User-Agent": "Algoriot-Backend/1.0 (SIH26081)"},
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{endpoint}?{param_str}"

    async def get_forecast(
        self,
        lat: float,
        lon: float,
        forecast_days: int = 4,
    ) -> Dict[str, Any]:
        """
        Fetch forecast data including hourly and current metrics.
        Cached according to CACHE_TTL_SECONDS.
        """
        endpoint = "/v1/forecast"
        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m"
            ),
            "hourly": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "precipitation_probability,precipitation,weather_code,surface_pressure,"
                "wind_speed_10m,wind_direction_10m"
            ),
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto",
            "forecast_days": min(max(1, forecast_days), 7),
        }

        key = self._cache_key(endpoint, params)
        now = time.time()
        if key in self._cache:
            cache_time, cached_val = self._cache[key]
            if now - cache_time < settings.CACHE_TTL_SECONDS:
                logger.debug(f"Open-Meteo cache hit for {lat}, {lon}")
                return cached_val

        client = await self._get_client()
        try:
            resp = await client.get(endpoint, params=params)
            resp.raise_for_status()
            data = resp.json()
            self._cache[key] = (now, data)
            logger.info(f"Open-Meteo fetched live weather for lat={lat}, lon={lon}")
            return data
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            logger.warning(
                f"Open-Meteo request failed: {exc}. Attempting cached or fallback data."
            )
            # If expired cache available, return that instead of hard fail
            if key in self._cache:
                logger.info(f"Serving stale cached data for {lat}, {lon}")
                return self._cache[key][1]
            raise WeatherProviderError(
                message=f"Weather provider error: {str(exc)}",
                details={"lat": lat, "lon": lon},
            )


open_meteo_client = OpenMeteoClient()
