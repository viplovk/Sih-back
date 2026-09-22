"""Map service handling spatial grids, wind vectors, and timeline from real Open-Meteo observations."""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy.interpolate import RectBivariateSpline

from app.core.config import settings
from app.core.cache import weather_cache
from app.core.logging import logger
from app.providers.open_meteo import open_meteo_client
from app.schemas.map import (
    TimelineResponse,
    TimelineFrame,
    WindGridResponse,
    TemperatureGridResponse,
    PrecipitationGridResponse,
    AirQualityGridResponse,
    MapBBox,
)


# Bounding Box for Indian subcontinent
NORTH = 37.0
SOUTH = 6.0
WEST = 68.0
EAST = 98.0
GRID_RES_LAT = 15
GRID_RES_LON = 15

ANCHOR_LATS = np.linspace(SOUTH, NORTH, GRID_RES_LAT)
ANCHOR_LONS = np.linspace(WEST, EAST, GRID_RES_LON)

ALL_ANCHOR_LATS: List[float] = [float(round(lat, 4)) for lat in ANCHOR_LATS for lon in ANCHOR_LONS]
ALL_ANCHOR_LONS: List[float] = [float(round(lon, 4)) for lat in ANCHOR_LATS for lon in ANCHOR_LONS]


def _parse_iso_ts(ts_str: str) -> Optional[datetime]:
    if not ts_str:
        return None
    cleaned = ts_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        try:
            return datetime.strptime(ts_str[:16], "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
        except Exception:
            return None


def _find_closest_time_index(requested_ts: str, time_list: List[str]) -> Tuple[int, str]:
    if not time_list:
        return 0, ""
    req_dt = _parse_iso_ts(requested_ts)
    if not req_dt:
        return 0, time_list[0]

    best_idx = 0
    best_diff = float("inf")
    for idx, t_str in enumerate(time_list):
        t_dt = _parse_iso_ts(t_str)
        if t_dt:
            diff = abs((t_dt - req_dt).total_seconds())
            if diff < best_diff:
                best_diff = diff
                best_idx = idx

    return best_idx, time_list[best_idx]


class MapService:
    """Provides spatial weather fields and synchronized temporal frames using real observations."""

    async def get_raw_weather_grid(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Fetch or retrieve cached 225-point weather grid across India."""
        key = "grid:india:weather:v2"

        async def _fetcher():
            data, source, valid_time = await open_meteo_client.get_multi_forecast(
                ALL_ANCHOR_LATS, ALL_ANCHOR_LONS, forecast_days=2
            )
            return data, source, valid_time

        data, meta = await weather_cache.get_or_fetch(
            key, _fetcher, ttl_seconds=settings.GRID_CACHE_TTL_SECONDS
        )
        return data, meta

    async def get_raw_aq_grid(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Fetch or retrieve cached 225-point air quality grid across India."""
        key = "grid:india:air_quality:v2"

        async def _fetcher():
            data, source, valid_time = await open_meteo_client.get_multi_air_quality(
                ALL_ANCHOR_LATS, ALL_ANCHOR_LONS, forecast_days=2
            )
            return data, source, valid_time

        data, meta = await weather_cache.get_or_fetch(
            key, _fetcher, ttl_seconds=settings.AIR_QUALITY_CACHE_TTL_SECONDS
        )
        return data, meta

    async def get_timeline(self) -> TimelineResponse:
        """Construct synchronized unified timeline of real provider timestamps."""
        grid_data, meta = await self.get_raw_weather_grid()
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        frames: List[TimelineFrame] = []
        if grid_data and len(grid_data) > 0:
            first_loc = grid_data[0]
            current_time = first_loc.get("current", {}).get("time", now_utc)
            frames.append(TimelineFrame(timestamp=current_time, mode="live"))

            hourly_times = first_loc.get("hourly", {}).get("time", [])
            # Filter hourly frames that are on or after current time
            curr_dt = _parse_iso_ts(current_time)
            for ht in hourly_times:
                h_dt = _parse_iso_ts(ht)
                if curr_dt and h_dt and h_dt > curr_dt:
                    frames.append(TimelineFrame(timestamp=ht, mode="forecast"))
        else:
            current_time = now_utc
            frames.append(TimelineFrame(timestamp=current_time, mode="live"))

        return TimelineResponse(
            source=meta.get("source", "open-meteo"),
            generated_at=now_utc,
            current_time=current_time,
            frames=frames,
            stale=meta.get("stale", False),
            fetched_at=meta.get("fetched_at", now_utc),
            age_seconds=meta.get("age_seconds", 0),
        )

    def _interpolate_matrix(
        self,
        values_flat: List[float],
        target_width: int,
        target_height: int,
    ) -> Tuple[np.ndarray, List[float], List[float]]:
        """
        Bivariate spline interpolation from 15x15 regular anchor grid to target resolution.
        """
        matrix = np.array(values_flat, dtype=np.float64).reshape((GRID_RES_LAT, GRID_RES_LON))
        spline = RectBivariateSpline(ANCHOR_LATS, ANCHOR_LONS, matrix, kx=2, ky=2)

        target_lats = np.linspace(SOUTH, NORTH, target_height)
        target_lons = np.linspace(WEST, EAST, target_width)
        grid = spline(target_lats, target_lons)
        return grid, [float(round(x, 4)) for x in target_lats], [float(round(x, 4)) for x in target_lons]

    async def get_wind_field(
        self,
        valid_time: Optional[str] = None,
        width: int = 80,
        height: int = 80,
    ) -> WindGridResponse:
        """Compute real wind vector field (u, v, speed, direction)."""
        width = max(10, min(width, 120))
        height = max(10, min(height, 120))
        grid_data, meta = await self.get_raw_weather_grid()

        # Determine mode and time frame
        is_live = not valid_time or valid_time.lower() in ("live", "current")
        first_loc = grid_data[0] if grid_data else {}
        hourly_times = first_loc.get("hourly", {}).get("time", [])

        u_anchors: List[float] = []
        v_anchors: List[float] = []
        actual_valid_time = ""
        mode = "live"

        if is_live:
            actual_valid_time = first_loc.get("current", {}).get("time", "")
            mode = "live"
            for loc in grid_data:
                curr = loc.get("current", {})
                speed = float(curr.get("wind_speed_10m", 0.0) or 0.0)
                direction = float(curr.get("wind_direction_10m", 0.0) or 0.0)
                rad = math.radians(direction)
                # Meteorological u (eastward) and v (northward) components
                u_anchors.append(-speed * math.sin(rad))
                v_anchors.append(-speed * math.cos(rad))
        else:
            time_idx, actual_valid_time = _find_closest_time_index(valid_time, hourly_times)
            mode = "forecast"
            for loc in grid_data:
                hourly = loc.get("hourly", {})
                speeds = hourly.get("wind_speed_10m", [])
                directions = hourly.get("wind_direction_10m", [])
                speed = float(speeds[time_idx]) if time_idx < len(speeds) and speeds[time_idx] is not None else 0.0
                direction = float(directions[time_idx]) if time_idx < len(directions) and directions[time_idx] is not None else 0.0
                rad = math.radians(direction)
                u_anchors.append(-speed * math.sin(rad))
                v_anchors.append(-speed * math.cos(rad))

        u_grid, out_lats, out_lons = self._interpolate_matrix(u_anchors, width, height)
        v_grid, _, _ = self._interpolate_matrix(v_anchors, width, height)

        speed_grid = np.sqrt(u_grid**2 + v_grid**2)
        # Direction in degrees (meteorological: from which wind blows)
        dir_grid = (np.degrees(np.arctan2(-u_grid, -v_grid)) + 360.0) % 360.0

        u_list = [[float(round(val, 2)) for val in row] for row in u_grid]
        v_list = [[float(round(val, 2)) for val in row] for row in v_grid]
        speed_list = [[float(round(val, 2)) for val in row] for row in speed_grid]
        dir_list = [[float(round(val, 1)) for val in row] for row in dir_grid]

        return WindGridResponse(
            source=meta.get("source", "open-meteo"),
            mode=mode,
            valid_time=actual_valid_time,
            requested_valid_time=valid_time,
            actual_valid_time=actual_valid_time,
            bbox=MapBBox(north=NORTH, south=SOUTH, west=WEST, east=EAST),
            width=width,
            height=height,
            latitudes=out_lats,
            longitudes=out_lons,
            u=u_list,
            v=v_list,
            speed=speed_list,
            direction=dir_list,
            unit="km/h",
            stale=meta.get("stale", False),
            fetched_at=meta.get("fetched_at", ""),
            age_seconds=meta.get("age_seconds", 0),
        )

    async def get_temperature_field(
        self,
        valid_time: Optional[str] = None,
        width: int = 80,
        height: int = 80,
        forecast_hour: Optional[int] = None,
    ) -> TemperatureGridResponse:
        """Compute real temperature field (°C) across the domain."""
        width = max(10, min(width, 120))
        height = max(10, min(height, 120))
        grid_data, meta = await self.get_raw_weather_grid()

        first_loc = grid_data[0] if grid_data else {}
        hourly_times = first_loc.get("hourly", {}).get("time", [])

        # If forecast_hour is provided (e.g. 12), resolve to matching hourly index
        if forecast_hour is not None and hourly_times:
            idx = min(max(0, forecast_hour), len(hourly_times) - 1)
            valid_time = hourly_times[idx]

        is_live = not valid_time or valid_time.lower() in ("live", "current")

        temp_anchors: List[float] = []
        actual_valid_time = ""
        mode = "live"

        if is_live:
            actual_valid_time = first_loc.get("current", {}).get("time", "")
            mode = "live"
            for loc in grid_data:
                curr = loc.get("current", {})
                t = float(curr.get("temperature_2m", 25.0) or 25.0)
                temp_anchors.append(t)
        else:
            time_idx, actual_valid_time = _find_closest_time_index(valid_time, hourly_times)
            mode = "forecast"
            for loc in grid_data:
                hourly = loc.get("hourly", {})
                temps = hourly.get("temperature_2m", [])
                t = float(temps[time_idx]) if time_idx < len(temps) and temps[time_idx] is not None else 25.0
                temp_anchors.append(t)

        temp_grid, out_lats, out_lons = self._interpolate_matrix(temp_anchors, width, height)
        values = [[float(round(val, 2)) for val in row] for row in temp_grid]
        min_val = float(round(float(np.min(temp_grid)), 2))
        max_val = float(round(float(np.max(temp_grid)), 2))

        # Sampled grid points for backward compatibility with earlier client expectations
        step_y = max(1, height // 8)
        step_x = max(1, width // 8)
        sampled_grid = []
        from app.schemas.map import TemperaturePoint
        for i in range(0, height, step_y):
            for j in range(0, width, step_x):
                sampled_grid.append(
                    TemperaturePoint(
                        lat=out_lats[i],
                        lon=out_lons[j],
                        temperature_c=values[i][j],
                    )
                )

        return TemperatureGridResponse(
            source=meta.get("source", "open-meteo"),
            mode=mode,
            valid_time=actual_valid_time,
            requested_valid_time=valid_time,
            actual_valid_time=actual_valid_time,
            bbox=MapBBox(north=NORTH, south=SOUTH, west=WEST, east=EAST),
            width=width,
            height=height,
            latitudes=out_lats,
            longitudes=out_lons,
            values=values,
            unit="°C",
            min=min_val,
            max=max_val,
            stale=meta.get("stale", False),
            fetched_at=meta.get("fetched_at", ""),
            age_seconds=meta.get("age_seconds", 0),
            timestamp=actual_valid_time,
            min_temperature_c=min_val,
            max_temperature_c=max_val,
            grid=sampled_grid,
        )

    async def get_precipitation_field(
        self,
        valid_time: Optional[str] = None,
        width: int = 80,
        height: int = 80,
    ) -> PrecipitationGridResponse:
        """Compute real precipitation field (mm) across the domain."""
        width = max(10, min(width, 120))
        height = max(10, min(height, 120))
        grid_data, meta = await self.get_raw_weather_grid()

        is_live = not valid_time or valid_time.lower() in ("live", "current")
        first_loc = grid_data[0] if grid_data else {}
        hourly_times = first_loc.get("hourly", {}).get("time", [])

        precip_anchors: List[float] = []
        actual_valid_time = ""
        mode = "live"

        if is_live:
            actual_valid_time = first_loc.get("current", {}).get("time", "")
            mode = "live"
            for loc in grid_data:
                curr = loc.get("current", {})
                p = float(curr.get("precipitation", 0.0) or 0.0)
                precip_anchors.append(p)
        else:
            time_idx, actual_valid_time = _find_closest_time_index(valid_time, hourly_times)
            mode = "forecast"
            for loc in grid_data:
                hourly = loc.get("hourly", {})
                precips = hourly.get("precipitation", [])
                p = float(precips[time_idx]) if time_idx < len(precips) and precips[time_idx] is not None else 0.0
                precip_anchors.append(p)

        precip_grid, out_lats, out_lons = self._interpolate_matrix(precip_anchors, width, height)
        # Precipitation cannot be negative
        precip_grid = np.maximum(0.0, precip_grid)
        values = [[float(round(val, 2)) for val in row] for row in precip_grid]

        return PrecipitationGridResponse(
            source=meta.get("source", "open-meteo"),
            mode=mode,
            valid_time=actual_valid_time,
            requested_valid_time=valid_time,
            actual_valid_time=actual_valid_time,
            bbox=MapBBox(north=NORTH, south=SOUTH, west=WEST, east=EAST),
            width=width,
            height=height,
            latitudes=out_lats,
            longitudes=out_lons,
            values=values,
            unit="mm",
            min=float(round(float(np.min(precip_grid)), 2)),
            max=float(round(float(np.max(precip_grid)), 2)),
            stale=meta.get("stale", False),
            fetched_at=meta.get("fetched_at", ""),
            age_seconds=meta.get("age_seconds", 0),
        )

    async def get_air_quality_field(
        self,
        valid_time: Optional[str] = None,
        width: int = 80,
        height: int = 80,
    ) -> AirQualityGridResponse:
        """Compute real air quality field (AQI, PM2.5, PM10, NO2, O3)."""
        width = max(10, min(width, 120))
        height = max(10, min(height, 120))
        grid_data, meta = await self.get_raw_aq_grid()

        is_live = not valid_time or valid_time.lower() in ("live", "current")
        first_loc = grid_data[0] if grid_data else {}
        hourly_times = first_loc.get("hourly", {}).get("time", [])

        aqi_anchors: List[float] = []
        pm25_anchors: List[float] = []
        pm10_anchors: List[float] = []
        no2_anchors: List[float] = []
        o3_anchors: List[float] = []
        actual_valid_time = ""
        mode = "live"

        if is_live:
            actual_valid_time = first_loc.get("current", {}).get("time", "")
            mode = "live"
            for loc in grid_data:
                curr = loc.get("current", {})
                aqi_anchors.append(float(curr.get("european_aqi", 50.0) or 50.0))
                pm25_anchors.append(float(curr.get("pm2_5", 25.0) or 25.0))
                pm10_anchors.append(float(curr.get("pm10", 45.0) or 45.0))
                no2_anchors.append(float(curr.get("nitrogen_dioxide", 20.0) or 20.0))
                o3_anchors.append(float(curr.get("ozone", 40.0) or 40.0))
        else:
            time_idx, actual_valid_time = _find_closest_time_index(valid_time, hourly_times)
            mode = "forecast"
            for loc in grid_data:
                hourly = loc.get("hourly", {})
                aqis = hourly.get("european_aqi", [])
                p25s = hourly.get("pm2_5", [])
                p10s = hourly.get("pm10", [])
                no2s = hourly.get("nitrogen_dioxide", [])
                o3s = hourly.get("ozone", [])

                aqi_anchors.append(float(aqis[time_idx]) if time_idx < len(aqis) and aqis[time_idx] is not None else 50.0)
                pm25_anchors.append(float(p25s[time_idx]) if time_idx < len(p25s) and p25s[time_idx] is not None else 25.0)
                pm10_anchors.append(float(p10s[time_idx]) if time_idx < len(p10s) and p10s[time_idx] is not None else 45.0)
                no2_anchors.append(float(no2s[time_idx]) if time_idx < len(no2s) and no2s[time_idx] is not None else 20.0)
                o3_anchors.append(float(o3s[time_idx]) if time_idx < len(o3s) and o3s[time_idx] is not None else 40.0)

        aqi_grid, out_lats, out_lons = self._interpolate_matrix(aqi_anchors, width, height)
        pm25_grid, _, _ = self._interpolate_matrix(pm25_anchors, width, height)
        pm10_grid, _, _ = self._interpolate_matrix(pm10_anchors, width, height)
        no2_grid, _, _ = self._interpolate_matrix(no2_anchors, width, height)
        o3_grid, _, _ = self._interpolate_matrix(o3_anchors, width, height)

        aqi_grid = np.maximum(0.0, aqi_grid)
        pm25_grid = np.maximum(0.0, pm25_grid)
        pm10_grid = np.maximum(0.0, pm10_grid)
        no2_grid = np.maximum(0.0, no2_grid)
        o3_grid = np.maximum(0.0, o3_grid)

        return AirQualityGridResponse(
            source=meta.get("source", "open-meteo-air-quality"),
            mode=mode,
            valid_time=actual_valid_time,
            requested_valid_time=valid_time,
            actual_valid_time=actual_valid_time,
            bbox=MapBBox(north=NORTH, south=SOUTH, west=WEST, east=EAST),
            width=width,
            height=height,
            latitudes=out_lats,
            longitudes=out_lons,
            aqi=[[float(round(val, 1)) for val in row] for row in aqi_grid],
            pm2_5=[[float(round(val, 1)) for val in row] for row in pm25_grid],
            pm10=[[float(round(val, 1)) for val in row] for row in pm10_grid],
            no2=[[float(round(val, 1)) for val in row] for row in no2_grid],
            o3=[[float(round(val, 1)) for val in row] for row in o3_grid],
            min=float(round(float(np.min(aqi_grid)), 1)),
            max=float(round(float(np.max(aqi_grid)), 1)),
            stale=meta.get("stale", False),
            fetched_at=meta.get("fetched_at", ""),
            age_seconds=meta.get("age_seconds", 0),
        )


map_service = MapService()
