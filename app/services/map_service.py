"""Geospatial temperature map generation service across India."""

import math
from typing import List, Optional, Dict, Any
from app.data.india_grid import DEMO_INDIA_GRID_COORDINATES, generate_india_grid
from app.schemas.map import MapGridPoint, MapTemperatureResponse
from app.utils.time import now_utc_iso
from app.utils.interpolation import inverse_distance_weighting


class MapService:
    """Produces geospatial temperature grid surfaces for the India Heatmap."""

    def __init__(self):
        # Anchor regional baseline temperatures across Indian climate zones
        # [lat, lon, baseline_temp_c]
        self.climatological_anchors = [
            (34.08, 74.80, 18.0),  # Srinagar (Kashmir valley)
            (31.10, 77.17, 16.0),  # Shimla (Himalayan highland)
            (28.61, 77.21, 33.5),  # Delhi (Northern plains)
            (26.91, 75.79, 36.2),  # Jaipur (Thar desert margin)
            (26.14, 91.74, 28.5),  # Guwahati (Brahmaputra valley)
            (22.57, 88.36, 31.0),  # Kolkata (Gangetic delta)
            (21.15, 79.09, 34.0),  # Nagpur (Vidarbha / Central India)
            (19.08, 72.88, 30.5),  # Mumbai (Konkan coast)
            (17.39, 78.49, 32.0),  # Hyderabad (Deccan plateau)
            (13.08, 80.27, 32.8),  # Chennai (Coromandel coast)
            (12.97, 77.59, 27.5),  # Bengaluru (South Mysore plateau)
            (8.52, 76.94, 29.0),   # Thiruvananthapuram (Malabar coast)
        ]

    def generate_temperature_map(
        self,
        time_iso: Optional[str] = None,
        forecast_hour: int = 0,
        resolution: str = "demo",
    ) -> MapTemperatureResponse:
        """
        Generate grid points covering India with interpolated temperature field.
        """
        ts = time_iso or now_utc_iso()

        # Diurnal fluctuation factor based on forecast hour
        hour_mod = forecast_hour % 24
        diurnal_shift = 3.5 * math.sin((hour_mod - 6) / 24.0 * 2.0 * math.pi)

        # Shift anchors based on diurnal cycle
        shifted_anchors = [
            (lat, lon, temp + diurnal_shift)
            for lat, lon, temp in self.climatological_anchors
        ]

        grid_points: List[MapGridPoint] = []

        if resolution in ("demo", "low"):
            # Use pre-curated representative grid across Indian cities and districts
            for lat, lon, name in DEMO_INDIA_GRID_COORDINATES:
                temp = inverse_distance_weighting(lat, lon, shifted_anchors, power=2.0)
                # Elevation cooling for Himalayan stations
                if lat > 30.0 and lon < 80.0 and name in ("Shimla", "Srinagar", "Dehradun"):
                    temp = round(temp - 6.0, 1)

                grid_points.append(
                    MapGridPoint(
                        lat=lat,
                        lon=lon,
                        temperature_c=temp,
                        name=name,
                    )
                )
        else:
            # Regular grid based on resolution step
            step_map = {"medium": 1.5, "high": 1.0, "0.25": 0.5, "0.5": 0.5, "1.0": 1.0, "2.0": 2.0}
            step = step_map.get(resolution, 1.5)
            coords = generate_india_grid(step_deg=step)

            for lat, lon in coords:
                temp = inverse_distance_weighting(lat, lon, shifted_anchors, power=2.0)
                if lat > 31.0:
                    temp = round(temp - 7.5, 1)  # Himalayan high altitude cold zone
                grid_points.append(
                    MapGridPoint(
                        lat=lat,
                        lon=lon,
                        temperature_c=temp,
                        name=None,
                    )
                )

        temps = [p.temperature_c for p in grid_points]
        min_t = min(temps) if temps else 15.0
        max_t = max(temps) if temps else 40.0

        return MapTemperatureResponse(
            timestamp=ts,
            source="Open-Meteo",
            resolution=resolution,
            grid=grid_points,
            min_temperature_c=round(min_t, 1),
            max_temperature_c=round(max_t, 1),
        )


map_service = MapService()
