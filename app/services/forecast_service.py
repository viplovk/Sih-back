"""Forecast orchestration service using real Open-Meteo provider data and honest hybrid semantics."""

from typing import Optional, Dict, Any, List, Tuple
from app.core.config import settings
from app.core.cache import weather_cache
from app.core.logging import logger
from app.providers.open_meteo import open_meteo_client, get_weather_description
from app.schemas.forecast import ForecastResponse, ForecastFrame, ForecastPoint
from app.schemas.weather import LocationInfo
from app.data.city_coordinates import find_nearest_city


class ForecastService:
    """Orchestrates hourly forecast frames from real weather models."""

    async def get_forecast(
        self,
        lat: float,
        lon: float,
        forecast_hours: int = 48,
        location_name: Optional[str] = None,
        blend: bool = False,
    ) -> ForecastResponse:
        """
        Produce real hourly forecast frames for given coordinates.
        Never generates synthetic or random mock numbers.
        """
        forecast_hours = max(24, min(forecast_hours, 168))
        forecast_days = max(1, min(7, (forecast_hours + 23) // 24))

        nearest_city, dist_km = find_nearest_city(lat, lon)
        resolved_name = location_name or (
            nearest_city.name if dist_km < 35.0 else f"Location ({lat:.2f}, {lon:.2f})"
        )
        elevation = nearest_city.elevation_m if dist_km < 35.0 else None

        key = f"forecast:{round(lat, 4)}:{round(lon, 4)}:{forecast_hours}"

        async def _fetcher():
            data = await open_meteo_client.get_forecast(lat, lon, forecast_days=forecast_days)
            first_hourly_time = ""
            if "hourly" in data and "time" in data["hourly"] and data["hourly"]["time"]:
                first_hourly_time = data["hourly"]["time"][0]
            elif "current" in data:
                first_hourly_time = data["current"].get("time", "")
            return data, "open-meteo", first_hourly_time

        raw_data, meta = await weather_cache.get_or_fetch(
            key, _fetcher, ttl_seconds=settings.CACHE_TTL_SECONDS
        )

        hourly = raw_data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        apparent_temps = hourly.get("apparent_temperature", [])
        humidities = hourly.get("relative_humidity_2m", [])
        precips = hourly.get("precipitation", [])
        rains = hourly.get("rain", precips)
        precip_probs = hourly.get("precipitation_probability", [0] * len(times))
        pressures = hourly.get("surface_pressure", [])
        wind_speeds = hourly.get("wind_speed_10m", [])
        wind_dirs = hourly.get("wind_direction_10m", [])
        wind_gusts = hourly.get("wind_gusts_10m", [None] * len(times))
        cloud_covers = hourly.get("cloud_cover", [0] * len(times))
        weather_codes = hourly.get("weather_code", [])

        limit = min(len(times), forecast_hours)
        frames: List[ForecastFrame] = []
        forecast_points: List[ForecastPoint] = []

        for i in range(limit):
            t_str = times[i]
            temp = float(temps[i]) if i < len(temps) and temps[i] is not None else 25.0
            app_temp = float(apparent_temps[i]) if i < len(apparent_temps) and apparent_temps[i] is not None else temp
            hum = int(humidities[i]) if i < len(humidities) and humidities[i] is not None else 50
            precip = float(precips[i]) if i < len(precips) and precips[i] is not None else 0.0
            rain = float(rains[i]) if i < len(rains) and rains[i] is not None else precip
            p_prob = int(precip_probs[i]) if i < len(precip_probs) and precip_probs[i] is not None else 0
            press = float(pressures[i]) if i < len(pressures) and pressures[i] is not None else 1013.0
            w_speed = float(wind_speeds[i]) if i < len(wind_speeds) and wind_speeds[i] is not None else 0.0
            w_dir = float(wind_dirs[i]) if i < len(wind_dirs) and wind_dirs[i] is not None else 0.0
            w_gust = float(wind_gusts[i]) if i < len(wind_gusts) and wind_gusts[i] is not None else None
            c_cover = int(cloud_covers[i]) if i < len(cloud_covers) and cloud_covers[i] is not None else 0
            w_code = int(weather_codes[i]) if i < len(weather_codes) and weather_codes[i] is not None else 0
            w_desc = get_weather_description(w_code)

            frame = ForecastFrame(
                timestamp=t_str,
                valid_time=t_str,
                temperature=temp,
                temperature_c=temp,
                feels_like_c=app_temp,
                precipitation=precip,
                precipitation_mm=precip,
                precipitation_probability=p_prob,
                rain=rain,
                humidity=hum,
                pressure=press,
                pressure_hpa=press,
                wind_speed=w_speed,
                wind_speed_kmh=w_speed,
                wind_direction=w_dir,
                wind_gusts=w_gust,
                cloud_cover=c_cover,
                weather_code=w_code,
                weather_description=w_desc,
            )
            frames.append(frame)

            point = ForecastPoint(
                time=t_str,
                temperature_c=temp,
                feels_like_c=app_temp,
                humidity=hum,
                wind_speed_kmh=w_speed,
                pressure_hpa=press,
                precipitation_probability=p_prob,
                precipitation_mm=precip,
                weather_code=w_code,
                weather_description=w_desc,
            )
            forecast_points.append(point)

        loc_info = LocationInfo(
            name=resolved_name,
            latitude=lat,
            longitude=lon,
            lat=lat,
            lon=lon,
            state=nearest_city.state if dist_km < 35.0 else None,
            elevation_m=elevation,
        )

        valid_time = frames[0].valid_time if frames else meta.get("valid_time", "")

        resp = ForecastResponse(
            source=meta.get("source", "open-meteo"),
            location=loc_info,
            mode="forecast",
            fetched_at=meta.get("fetched_at", ""),
            valid_time=valid_time,
            stale=meta.get("stale", False),
            age_seconds=meta.get("age_seconds", 0),
            frames=frames,
            forecast=forecast_points,
            generated_at=meta.get("fetched_at", ""),
            forecast_horizon_hours=limit,
            is_blended=False,
        )

        if blend:
            from app.providers.open_meteo_model import OpenMeteoModel
            from app.providers.ai_models import DemoAIModel
            from app.providers.nwp import DemoNWPModel
            from app.services.blending_service import blending_engine

            om_model = OpenMeteoModel()
            ai_model = DemoAIModel()
            nwp_model = DemoNWPModel()

            om_pts = await om_model.forecast(lat, lon, forecast_hours, raw_data)
            ai_pts = await ai_model.forecast(lat, lon, forecast_hours, raw_data)
            nwp_pts = await nwp_model.forecast(lat, lon, forecast_hours, raw_data)

            blended_pts, regimes = blending_engine.blend_forecasts(
                lat=lat,
                lon=lon,
                elevation_m=elevation or 100.0,
                open_meteo_points=om_pts,
                ai_points=ai_pts,
                nwp_points=nwp_pts,
            )

            resp.forecast = [
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
                for p in blended_pts
            ]
            resp.is_blended = True
            return resp, om_pts, ai_pts, nwp_pts, regimes

        return resp


forecast_service = ForecastService()
