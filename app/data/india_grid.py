"""India geospatial boundary and meteorological grid definitions."""

from typing import List, Dict, Any, Tuple


# Simplified polygon boundary for continental India for bounding grid filtering
INDIA_BOUNDS = {
    "min_lat": 8.0,
    "max_lat": 37.2,
    "min_lon": 68.0,
    "max_lon": 97.4,
}


def is_in_india(lat: float, lon: float) -> bool:
    """Rough bounding box and geographic filter for Indian landmass."""
    if not (INDIA_BOUNDS["min_lat"] <= lat <= INDIA_BOUNDS["max_lat"] and
            INDIA_BOUNDS["min_lon"] <= lon <= INDIA_BOUNDS["max_lon"]):
        return False

    # Northern boundary checks (Kashmir / Ladakh)
    if lat > 32.0 and (lon < 73.0 or lon > 80.5):
        return False
    # North-East funnel
    if lat > 24.0 and lon > 88.0 and lat > 28.5 and lon > 97.5:
        return False
    # Southern triangle check
    if lat < 14.0 and (lon < 74.0 or lon > 81.0):
        return False
    if lat < 10.0 and (lon < 75.5 or lon > 79.8):
        return False

    return True


def generate_india_grid(step_deg: float = 2.0) -> List[Tuple[float, float]]:
    """Generate regularly spaced grid points inside Indian bounds."""
    points = []
    lat = INDIA_BOUNDS["min_lat"]
    while lat <= INDIA_BOUNDS["max_lat"]:
        lon = INDIA_BOUNDS["min_lon"]
        while lon <= INDIA_BOUNDS["max_lon"]:
            if is_in_india(lat, lon):
                points.append((round(lat, 2), round(lon, 2)))
            lon += step_deg
        lat += step_deg
    return points


# Pre-computed high-value representative anchor grid across India (demo resolution)
DEMO_INDIA_GRID_COORDINATES: List[Tuple[float, float, str]] = [
    # North
    (34.08, 74.80, "Srinagar"),
    (32.72, 74.86, "Jammu"),
    (31.63, 74.87, "Amritsar"),
    (31.10, 77.17, "Shimla"),
    (30.73, 76.78, "Chandigarh"),
    (30.32, 78.03, "Dehradun"),
    (28.61, 77.21, "Delhi"),
    (27.18, 78.01, "Agra"),
    (26.85, 80.95, "Lucknow"),
    (25.32, 82.97, "Varanasi"),
    (25.43, 81.84, "Prayagraj"),
    # West
    (26.91, 75.79, "Jaipur"),
    (26.24, 73.02, "Jodhpur"),
    (24.59, 73.71, "Udaipur"),
    (23.02, 72.57, "Ahmedabad"),
    (22.31, 73.18, "Vadodara"),
    (21.17, 72.83, "Surat"),
    (21.76, 72.15, "Bhavnagar"),
    (22.30, 70.80, "Rajkot"),
    # Central
    (23.26, 77.41, "Bhopal"),
    (22.72, 75.86, "Indore"),
    (23.18, 79.99, "Jabalpur"),
    (21.15, 79.09, "Nagpur"),
    (21.25, 81.63, "Raipur"),
    (23.34, 85.31, "Ranchi"),
    # East
    (25.59, 85.14, "Patna"),
    (24.80, 85.00, "Gaya"),
    (22.57, 88.36, "Kolkata"),
    (23.67, 86.95, "Asansol"),
    (20.30, 85.82, "Bhubaneswar"),
    (21.47, 83.98, "Sambalpur"),
    # North-East
    (26.14, 91.74, "Guwahati"),
    (25.58, 91.89, "Shillong"),
    (27.47, 94.91, "Dibrugarh"),
    (24.82, 92.80, "Silchar"),
    (23.83, 91.28, "Agartala"),
    # West Coast & Deccan
    (19.08, 72.88, "Mumbai"),
    (18.52, 73.86, "Pune"),
    (19.99, 73.79, "Nashik"),
    (16.70, 74.24, "Kolhapur"),
    (15.30, 74.12, "Goa"),
    (17.39, 78.49, "Hyderabad"),
    (17.69, 83.22, "Visakhapatnam"),
    (16.51, 80.64, "Vijayawada"),
    # South
    (12.97, 77.59, "Bengaluru"),
    (12.30, 76.65, "Mysuru"),
    (13.08, 80.27, "Chennai"),
    (11.02, 76.96, "Coimbatore"),
    (10.80, 78.69, "Tiruchirappalli"),
    (9.93, 78.12, "Madurai"),
    (9.93, 76.27, "Kochi"),
    (11.26, 75.78, "Kozhikode"),
    (8.52, 76.94, "Thiruvananthapuram"),
]
