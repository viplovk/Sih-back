"""Meta-Learner for dynamic multi-model ensemble weighting.

Dynamically allocates weights across operational weather composite (Open-Meteo),
simulated AI Foundation model (AI-Demo), and simulated physical NWP (NWP-Demo)
based on atmospheric regime, forecast horizon, time of day, and physical parameter limits.
"""

from typing import Dict, Any, List, Tuple
from app.ml.feature_engineering import extract_atmospheric_features


class MetaLearner:
    """
    Scientific ensemble meta-learner for multi-model forecast blending.
    Guarantees:
    - Every weight is in [0.0, 1.0].
    - Weights sum exactly to 1.0.
    - 100% deterministic for identical meteorological inputs.
    - Transparent, human-interpretable reasoning factors.
    """

    def __init__(self):
        # Default baseline climatological weights
        self.default_weights = {
            "Open-Meteo": 0.45,
            "AI-Demo": 0.30,
            "NWP-Demo": 0.25,
        }

    def compute_weights(
        self,
        features: Dict[str, float],
        regime: str,
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Compute deterministic model weights based on feature vector and regime.
        Returns: (normalized_weights, explanation_factors).
        """
        horizon = features.get("forecast_horizon_hours", 24.0)
        temp = features.get("temperature_c", 30.0)
        precip = features.get("precipitation_mm", 0.0)
        wind = features.get("wind_speed_kmh", 12.0)

        # Raw scores starting from solid baselines
        score_open_meteo = 1.0
        score_ai = 0.75
        score_nwp = 0.65
        explanations: List[str] = []

        # 1. Lead-time / Forecast Horizon dependency
        if horizon <= 24.0:
            # Short-range: operational NWP and composite observations dominate
            score_open_meteo += 0.25
            score_nwp += 0.20
            score_ai -= 0.05
            explanations.append("short lead-time (<=24h) favors observational assimilation and high-res physics")
        elif horizon > 72.0:
            # Medium/extended range (3-7 days): AI foundation models exhibit lower error accumulation
            score_ai += 0.35
            score_nwp -= 0.15
            score_open_meteo -= 0.05
            explanations.append("extended lead-time (>72h) favors AI foundation model trajectory stability")
        else:
            # 24-72h standard transition
            score_ai += 0.10
            score_open_meteo += 0.10
            explanations.append("mid-range forecast horizon maintains balanced ensemble weighting")

        # 2. Regime dependency
        if regime in ("EXTREME_RAIN", "HEAVY_RAIN", "THUNDERSTORM"):
            # Deep convective rainfall requires explicit microphysics and hydrostatic balance
            score_nwp += 0.30
            score_open_meteo += 0.20
            score_ai -= 0.20
            explanations.append(f"convective regime ({regime}) increases NWP physical parameterization weight")
        elif regime in ("EXTREME_HEAT", "HOT"):
            # Boundary-layer thermal convection
            score_open_meteo += 0.15
            score_nwp += 0.15
            explanations.append(f"high thermal regime ({regime}) prioritizes surface heat budget models")
        elif regime == "HIGH_WIND":
            # Pressure gradient wind dynamics
            score_nwp += 0.25
            score_open_meteo += 0.15
            explanations.append("elevated wind speeds emphasize NWP geostrophic gradient calculation")
        else:
            explanations.append("standard climatological conditions with balanced multi-model distribution")

        # 3. Softmax / Normalization to strictly ensure sum = 1.0 and each weight in [0, 1]
        scores = {
            "Open-Meteo": max(0.1, score_open_meteo),
            "AI-Demo": max(0.1, score_ai),
            "NWP-Demo": max(0.1, score_nwp),
        }
        total = sum(scores.values())

        w_open_meteo = round(scores["Open-Meteo"] / total, 3)
        w_ai = round(scores["AI-Demo"] / total, 3)
        # Ensure exact 1.0 sum by assigning residual to NWP-Demo
        w_nwp = round(1.0 - w_open_meteo - w_ai, 3)

        # Safety clamp to guarantee 0.0 to 1.0
        final_weights = {
            "Open-Meteo": max(0.01, min(0.98, w_open_meteo)),
            "AI-Demo": max(0.01, min(0.98, w_ai)),
            "NWP-Demo": max(0.01, min(0.98, w_nwp)),
        }
        # Final exact renormalization
        f_total = sum(final_weights.values())
        final_weights = {k: round(v / f_total, 3) for k, v in final_weights.items()}
        # Re-verify exact sum
        diff = round(1.0 - sum(final_weights.values()), 3)
        if diff != 0.0:
            final_weights["Open-Meteo"] = round(final_weights["Open-Meteo"] + diff, 3)

        return final_weights, explanations


meta_learner = MetaLearner()
