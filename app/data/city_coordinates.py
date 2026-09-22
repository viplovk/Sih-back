"""Central repository of Indian city coordinates and geographic metadata."""

import math
from typing import Dict, Optional, List, Tuple


class CityLocation:
    def __init__(
        self,
        name: str,
        lat: float,
        lon: float,
        state: str,
        elevation_m: float = 100.0,
    ):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.state = state
        self.elevation_m = elevation_m

    def to_dict(self) -> Dict[str, any]:
        return {
            "name": self.name,
            "lat": self.lat,
            "lon": self.lon,
            "state": self.state,
            "elevation_m": self.elevation_m,
        }


INDIAN_CITIES: Dict[str, CityLocation] = {
    "delhi": CityLocation("Delhi", 28.6139, 77.2090, "Delhi", 216.0),
    "mumbai": CityLocation("Mumbai", 19.0760, 72.8777, "Maharashtra", 14.0),
    "bengaluru": CityLocation("Bengaluru", 12.9716, 77.5946, "Karnataka", 920.0),
    "chennai": CityLocation("Chennai", 13.0827, 80.2707, "Tamil Nadu", 6.0),
    "kolkata": CityLocation("Kolkata", 22.5726, 88.3639, "West Bengal", 9.0),
    "hyderabad": CityLocation("Hyderabad", 17.3850, 78.4867, "Telangana", 542.0),
    "ahmedabad": CityLocation("Ahmedabad", 23.0225, 72.5714, "Gujarat", 53.0),
    "jaipur": CityLocation("Jaipur", 26.9124, 75.7873, "Rajasthan", 431.0),
    "lucknow": CityLocation("Lucknow", 26.8467, 80.9462, "Uttar Pradesh", 123.0),
    "pune": CityLocation("Pune", 18.5204, 73.8567, "Maharashtra", 560.0),
    "patna": CityLocation("Patna", 25.5941, 85.1376, "Bihar", 53.0),
    "bhopal": CityLocation("Bhopal", 23.2599, 77.4126, "Madhya Pradesh", 527.0),
    "chandigarh": CityLocation("Chandigarh", 30.7333, 76.7794, "Chandigarh", 321.0),
    "guwahati": CityLocation("Guwahati", 26.1445, 91.7362, "Assam", 55.0),
    "bhubaneswar": CityLocation("Bhubaneswar", 20.2961, 85.8245, "Odisha", 45.0),
    "kochi": CityLocation("Kochi", 9.9312, 76.2673, "Kerala", 5.0),
    "thiruvananthapuram": CityLocation("Thiruvananthapuram", 8.5241, 76.9366, "Kerala", 10.0),
    "srinagar": CityLocation("Srinagar", 34.0837, 74.7973, "Jammu & Kashmir", 1585.0),
    "dehradun": CityLocation("Dehradun", 30.3165, 78.0322, "Uttarakhand", 635.0),
    "shimla": CityLocation("Shimla", 31.1048, 77.1734, "Himachal Pradesh", 2276.0),
    "ranchi": CityLocation("Ranchi", 23.3441, 85.3096, "Jharkhand", 651.0),
    "raipur": CityLocation("Raipur", 21.2514, 81.6296, "Chhattisgarh", 298.0),
    "nagpur": CityLocation("Nagpur", 21.1458, 79.0882, "Maharashtra", 310.0),
    "indore": CityLocation("Indore", 22.7196, 75.8577, "Madhya Pradesh", 553.0),
    "surat": CityLocation("Surat", 21.1702, 72.8311, "Gujarat", 13.0),
    "vadodara": CityLocation("Vadodara", 22.3072, 73.1812, "Gujarat", 39.0),
    "visakhapatnam": CityLocation("Visakhapatnam", 17.6868, 83.2185, "Andhra Pradesh", 45.0),
    "varanasi": CityLocation("Varanasi", 25.3176, 82.9739, "Uttar Pradesh", 81.0),
    "agra": CityLocation("Agra", 27.1767, 78.0081, "Uttar Pradesh", 169.0),
    "amritsar": CityLocation("Amritsar", 31.6340, 74.8723, "Punjab", 234.0),
}


def get_city(name_or_query: str) -> Optional[CityLocation]:
    """Retrieve city by key or case-insensitive search."""
    cleaned = name_or_query.strip().lower()
    if cleaned in INDIAN_CITIES:
        return INDIAN_CITIES[cleaned]
    for key, city in INDIAN_CITIES.items():
        if cleaned in city.name.lower() or city.name.lower() in cleaned:
            return city
    return None


def get_all_cities() -> List[CityLocation]:
    """Return all defined Indian cities."""
    return list(INDIAN_CITIES.values())


def find_nearest_city(lat: float, lon: float) -> Tuple[CityLocation, float]:
    """Find nearest Indian city and its distance in kilometers using Haversine formula."""
    r = 6371.0  # Earth radius in km
    best_city = INDIAN_CITIES["delhi"]
    best_dist = float("inf")

    lat1 = math.radians(lat)
    lon1 = math.radians(lon)

    for city in INDIAN_CITIES.values():
        lat2 = math.radians(city.lat)
        lon2 = math.radians(city.lon)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        dist = r * c
        if dist < best_dist:
            best_dist = dist
            best_city = city

    return best_city, round(best_dist, 2)
