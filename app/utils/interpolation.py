"""Spatial and temporal interpolation algorithms for meteorological fields."""

import math
from typing import List, Tuple, Dict


def inverse_distance_weighting(
    target_lat: float,
    target_lon: float,
    observations: List[Tuple[float, float, float]],
    power: float = 2.0,
) -> float:
    """
    Inverse Distance Weighting (IDW) interpolation.
    observations: List of (lat, lon, value).
    """
    if not observations:
        return 28.0  # sensible climatological fallback for India

    weights_sum = 0.0
    values_sum = 0.0

    for obs_lat, obs_lon, val in observations:
        # Euclidean degree approximation sufficient for regional IDW
        d = math.hypot(target_lat - obs_lat, target_lon - obs_lon)
        if d < 1e-4:
            return val
        w = 1.0 / (d ** power)
        weights_sum += w
        values_sum += w * val

    if weights_sum == 0.0:
        return observations[0][2]

    return round(values_sum / weights_sum, 1)


def linear_time_interpolate(val1: float, val2: float, fraction: float) -> float:
    """Simple linear interpolation between two time stamps."""
    return round(val1 + (val2 - val1) * fraction, 2)
