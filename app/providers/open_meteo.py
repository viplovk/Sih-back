"""Open-Meteo operational weather and air quality provider with HTTPX."""

import asyncio
from typing import Dict, Any, Optional, List, Tuple
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import WeatherProviderError, WeatherDataUnavailableError


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
    """Async HTTPX client for Open-Meteo Weather and Air Quality APIs."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        aq_base_url: Optional[str] = None,
    ):
        self.base_url = base_url or settings.OPEN_METEO_BASE_URL
        self.aq_base_url = aq_base_url or settings.air_quality_url
        self._weather_client: Optional[httpx.AsyncClient] = None
        self._aq_client: Optional[httpx.AsyncClient] = None
        self._loop = None

    async def _get_weather_client(self) -> httpx.AsyncClient:
        loop = asyncio.get_running_loop()
        if (
            self._weather_client is None
            or self._weather_client.is_closed
            or self._loop is not loop
        ):
            self._loop = loop
            self._weather_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(20.0, connect=5.0),
                headers={"User-Agent": "Algoriot-Backend/2.0 (SIH26081-Production)"},
            )
        return self._weather_client

    async def _get_aq_client(self) -> httpx.AsyncClient:
        loop = asyncio.get_running_loop()
        if (
            self._aq_client is None
            or self._aq_client.is_closed
            or self._loop is not loop
        ):
            self._loop = loop
            self._aq_client = httpx.AsyncClient(
                base_url=self.aq_base_url,
                timeout=httpx.Timeout(20.0, connect=5.0),
                headers={"User-Agent": "Algoriot-Backend/2.0 (SIH26081-Production)"},
            )
        return self._aq_client

    async def close(self):
        if self._weather_client and not self._weather_client.is_closed:
            await self._weather_client.aclose()
        if self._aq_client and not self._aq_client.is_closed:
            await self._aq_client.aclose()

    async def _get_with_retry(
        self, client: httpx.AsyncClient, endpoint: str, params: Dict[str, Any], max_retries: int = 3
    ) -> httpx.Response:
        """Execute HTTP GET with automatic exponential backoff on 429 burst limits."""
        for attempt in range(max_retries):
            try:
                resp = await client.get(endpoint, params=params)
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and attempt < max_retries - 1:
                    sleep_time = 1.0 * (attempt + 1)
                    logger.warning(f"[OPEN-METEO] Rate limited (429), backing off {sleep_time}s before retry")
                    await asyncio.sleep(sleep_time)
                    continue
                raise

    async def get_live_weather(
        self,
        lat: float,
        lon: float,
    ) -> Tuple[Dict[str, Any], str, str]:
        """Fetch current weather conditions for specific coordinates."""
        client = await self._get_weather_client()
        endpoint = "/v1/forecast"
        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "current": (
                "temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,"
                "precipitation,rain,showers,snowfall,weather_code,cloud_cover,"
                "surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m"
            ),
            "timezone": "auto",
        }
        resp = await self._get_with_retry(client, endpoint, params)
        data = resp.json()
        current = data.get("current", {})
        valid_time = current.get("time", "")
        return data, "open-meteo", valid_time

    async def get_forecast(
        self,
        lat: float,
        lon: float,
        forecast_days: int = 2,
    ) -> Dict[str, Any]:
        """Fetch current and hourly forecast data."""
        client = await self._get_weather_client()
        endpoint = "/v1/forecast"
        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "current": (
                "temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,"
                "precipitation,rain,showers,snowfall,weather_code,cloud_cover,"
                "surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m"
            ),
            "hourly": (
                "temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,"
                "precipitation,rain,showers,snowfall,weather_code,cloud_cover,"
                "surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m"
            ),
            "timezone": "auto",
            "forecast_days": min(max(1, forecast_days), 7),
        }
        resp = await self._get_with_retry(client, endpoint, params)
        return resp.json()

    async def get_multi_forecast(
        self,
        lats: List[float],
        lons: List[float],
        forecast_days: int = 2,
    ) -> Tuple[List[Dict[str, Any]], str, str]:
        """
        Batch query multi-location forecasts in a single request.
        Used for populating spatial grids across India.
        """
        client = await self._get_weather_client()
        endpoint = "/v1/forecast"
        lat_str = ",".join(str(round(lat, 4)) for lat in lats)
        lon_str = ",".join(str(round(lon, 4)) for lon in lons)
        params = {
            "latitude": lat_str,
            "longitude": lon_str,
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "precipitation,rain,showers,snowfall,weather_code,cloud_cover,"
                "surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m"
            ),
            "hourly": (
                "temperature_2m,relative_humidity_2m,precipitation,"
                "surface_pressure,wind_speed_10m,wind_direction_10m,cloud_cover,weather_code"
            ),
            "timezone": "UTC",
            "forecast_days": min(max(1, forecast_days), 3),
        }
        resp = await client.get(endpoint, params=params)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            data = [data]

        valid_time = ""
        if data and "current" in data[0]:
            valid_time = data[0]["current"].get("time", "")

        return data, "open-meteo", valid_time

    async def get_air_quality(
        self,
        lat: float,
        lon: float,
        forecast_days: int = 2,
    ) -> Tuple[Dict[str, Any], str, str]:
        """Fetch real air quality from Open-Meteo Air Quality API."""
        client = await self._get_aq_client()
        endpoint = "/v1/air-quality"
        params = {
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "current": (
                "european_aqi,us_aqi,pm2_5,pm10,nitrogen_dioxide,"
                "ozone,sulphur_dioxide,carbon_monoxide"
            ),
            "hourly": "european_aqi,us_aqi,pm2_5,pm10,nitrogen_dioxide,ozone",
            "timezone": "auto",
            "forecast_days": min(max(1, forecast_days), 7),
        }
        resp = await client.get(endpoint, params=params)
        resp.raise_for_status()
        data = resp.json()
        valid_time = data.get("current", {}).get("time", "")
        return data, "open-meteo-air-quality", valid_time

    async def get_multi_air_quality(
        self,
        lats: List[float],
        lons: List[float],
        forecast_days: int = 2,
    ) -> Tuple[List[Dict[str, Any]], str, str]:
        """Batch query multi-location air quality across India grid."""
        client = await self._get_aq_client()
        endpoint = "/v1/air-quality"
        lat_str = ",".join(str(round(lat, 4)) for lat in lats)
        lon_str = ",".join(str(round(lon, 4)) for lon in lons)
        params = {
            "latitude": lat_str,
            "longitude": lon_str,
            "current": (
                "european_aqi,us_aqi,pm2_5,pm10,nitrogen_dioxide,"
                "ozone,sulphur_dioxide,carbon_monoxide"
            ),
            "hourly": "european_aqi,pm2_5,pm10,nitrogen_dioxide,ozone",
            "timezone": "UTC",
            "forecast_days": min(max(1, forecast_days), 3),
        }
        resp = await client.get(endpoint, params=params)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            data = [data]

        valid_time = ""
        if data and "current" in data[0]:
            valid_time = data[0]["current"].get("time", "")

        return data, "open-meteo-air-quality", valid_time


# Global singleton instance
open_meteo_client = OpenMeteoClient()
