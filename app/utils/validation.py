"""Input parameter validation utilities."""

from typing import Tuple, Optional
from app.core.exceptions import InvalidCoordinatesError, ValidationError
from app.data.city_coordinates import get_city


def validate_coordinates(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    location_query: Optional[str] = None,
) -> Tuple[float, float, str]:
    """
    Validate coordinates or resolve named location to lat/lon.
    Returns (lat, lon, location_name).
    """
    # If location query provided, attempt resolving first
    if location_query:
        city = get_city(location_query)
        if city:
            return city.lat, city.lon, city.name

    # Check that lat and lon are present
    if lat is None or lon is None:
        # Default to Delhi if neither is given
        if location_query:
            return 28.6139, 77.2090, location_query.title()
        return 28.6139, 77.2090, "Delhi"

    if not (-90.0 <= lat <= 90.0):
        raise InvalidCoordinatesError(
            f"Latitude {lat} is out of bounds. Must be between -90.0 and 90.0."
        )

    if not (-180.0 <= lon <= 180.0):
        raise InvalidCoordinatesError(
            f"Longitude {lon} is out of bounds. Must be between -180.0 and 180.0."
        )

    # Determine location name if known city nearby
    from app.data.city_coordinates import find_nearest_city
    nearest_city, dist_km = find_nearest_city(lat, lon)
    location_name = nearest_city.name if dist_km < 35.0 else f"Location ({lat:.2f}, {lon:.2f})"

    return round(lat, 4), round(lon, 4), location_name


def validate_forecast_hours(hours: Optional[int] = None, forecast_hours: Optional[int] = None) -> int:
    """Validate requested forecast horizon in hours (between 1 and 168)."""
    h = forecast_hours if forecast_hours is not None else (hours if hours is not None else 72)
    if h < 1:
        return 1
    if h > 168:
        return 168
    return h


def validate_grid_resolution(resolution: str) -> str:
    """Validate grid resolution parameter."""
    res = resolution.lower().strip()
    if res in ("demo", "low", "medium", "high", "0.25", "0.5", "1.0", "2.0"):
        return res
    return "demo"
