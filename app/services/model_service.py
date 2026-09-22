"""Model registry and contribution evaluation service."""

from typing import List, Dict, Any, Optional
from app.providers.base import ForecastModel
from app.providers.open_meteo_model import OpenMeteoModel
from app.providers.ai_models import DemoAIModel
from app.providers.nwp import DemoNWPModel
from app.schemas.models import ModelInfo, ModelsResponse, ModelContributionResponse, ModelWeightExplanation
from app.ml.meta_learner import meta_learner
from app.ml.feature_engineering import extract_atmospheric_features
from app.ml.regime_detector import regime_detector
from app.utils.time import now_utc_iso


class ModelService:
    """Manages active forecast model instances and contribution calculations."""

    def __init__(self):
        self.models: Dict[str, ForecastModel] = {
            "open-meteo": OpenMeteoModel(),
            "demo-ai": DemoAIModel(),
            "demo-nwp": DemoNWPModel(),
        }

    def get_models(self) -> ModelsResponse:
        """Return descriptors of all registered forecasting models."""
        info_list = [ModelInfo(**m.get_info()) for m in self.models.values()]
        return ModelsResponse(models=info_list)

    def calculate_contribution(
        self,
        location: str,
        lat: float,
        lon: float,
        time_iso: Optional[str] = None,
        forecast_horizon_hours: float = 24.0,
        temperature_c: float = 30.0,
        humidity: float = 60.0,
        wind_speed_kmh: float = 12.0,
        pressure_hpa: float = 1010.0,
        precipitation_mm: float = 0.0,
        weather_code: int = 1,
    ) -> ModelContributionResponse:
        """Compute the dynamic model weights and explanation for a specific time and location."""
        target_time = time_iso or now_utc_iso()

        # 1. Regime detection
        regime_info = regime_detector.detect_regime(
            temperature_c=temperature_c,
            humidity=humidity,
            wind_speed_kmh=wind_speed_kmh,
            pressure_hpa=pressure_hpa,
            precipitation_mm=precipitation_mm,
            weather_code=weather_code,
        )
        regime = regime_info["regime"]

        # 2. Extract atmospheric features
        features = extract_atmospheric_features(
            temperature_c=temperature_c,
            humidity=humidity,
            wind_speed_kmh=wind_speed_kmh,
            pressure_hpa=pressure_hpa,
            precipitation_mm=precipitation_mm,
            time_iso=target_time,
            lat=lat,
            lon=lon,
            forecast_horizon_hours=forecast_horizon_hours,
        )

        # 3. Dynamic weights calculation
        weights, explanations = meta_learner.compute_weights(features, regime)

        return ModelContributionResponse(
            location=location,
            time=target_time,
            regime=regime,
            weights=weights,
            reasoning=ModelWeightExplanation(
                regime=regime,
                horizon_hours=forecast_horizon_hours,
                primary_factors=explanations,
                confidence=regime_info.get("confidence", 0.85),
            ),
        )


model_service = ModelService()
