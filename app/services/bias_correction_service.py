"""Bias correction service."""

from typing import Optional
from app.ml.bias_correction import bias_corrector


class BiasCorrectionService:
    def correct(
        self,
        variable: str,
        value: float,
        elevation_m: float = 100.0,
        hour_of_day: Optional[int] = None,
        observed_reference: Optional[float] = None,
    ) -> float:
        return bias_corrector.correct_forecast_value(
            variable_name=variable,
            predicted_value=value,
            elevation_m=elevation_m,
            hour_of_day=hour_of_day,
            observed_reference=observed_reference,
        )


bias_correction_service = BiasCorrectionService()
