"""Common abstract interface for all meteorological forecast models."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.schemas.forecast import ForecastPoint


class ForecastModel(ABC):
    """Abstract base class for all forecasting models (NWP, AI, Operational Composite)."""

    def __init__(
        self,
        model_id: str,
        name: str,
        model_type: str,
        status: str,
        is_demo: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.model_id = model_id
        self.name = name
        self.model_type = model_type  # 'weather-provider', 'NWP', 'AI'
        self.status = status          # 'active' or 'SIMULATED'
        self.is_demo = is_demo
        self.metadata = metadata or {}

    @abstractmethod
    async def forecast(
        self,
        lat: float,
        lon: float,
        forecast_hours: int = 72,
        base_observations: Optional[Dict[str, Any]] = None,
    ) -> List[ForecastPoint]:
        """Generate time-series forecast points for given coordinates."""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Return model metadata descriptor."""
        return {
            "id": self.model_id,
            "name": self.name,
            "type": self.model_type,
            "status": self.status,
            "is_demo": self.is_demo,
            "description": self.metadata.get("description", ""),
        }
