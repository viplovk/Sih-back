"""Tests for meta-learner, blending logic, and scientific invariants."""

import pytest
from app.ml.meta_learner import meta_learner
from app.ml.regime_detector import regime_detector
from app.ml.bias_correction import bias_corrector
from app.ml.uncertainty_calibration import uncertainty_estimator
from app.ml.feature_engineering import extract_atmospheric_features


def test_meta_learner_weights_sum_to_one():
    features = extract_atmospheric_features(
        temperature_c=34.0,
        humidity=65.0,
        wind_speed_kmh=15.0,
        pressure_hpa=1005.0,
        precipitation_mm=5.0,
        time_iso="2026-09-22T14:00:00Z",
        lat=28.6139,
        lon=77.2090,
        forecast_horizon_hours=36.0,
    )

    weights, explanations = meta_learner.compute_weights(features, "HOT")
    total_w = sum(weights.values())
    assert abs(total_w - 1.0) < 0.005, f"Weights sum to {total_w}, expected 1.0"
    for m_name, w in weights.items():
        assert 0.0 <= w <= 1.0, f"Weight {m_name}={w} outside [0, 1]"
    assert len(explanations) > 0


def test_meta_learner_determinism():
    features = extract_atmospheric_features(
        temperature_c=25.0,
        humidity=50.0,
        wind_speed_kmh=10.0,
        pressure_hpa=1012.0,
        precipitation_mm=0.0,
        time_iso="2026-09-22T08:00:00Z",
        lat=13.0827,
        lon=80.2707,
        forecast_horizon_hours=12.0,
    )

    w1, _ = meta_learner.compute_weights(features, "NORMAL")
    w2, _ = meta_learner.compute_weights(features, "NORMAL")
    assert w1 == w2, "Meta-learner weights must be completely deterministic for identical inputs"


def test_regime_detector_thresholds():
    # Extreme heat test
    r_heat = regime_detector.detect_regime(
        temperature_c=43.5,
        humidity=40.0,
        wind_speed_kmh=12.0,
        pressure_hpa=1002.0,
        precipitation_mm=0.0,
        weather_code=0,
    )
    assert r_heat["regime"] == "EXTREME_HEAT"
    assert 0.0 <= r_heat["confidence"] <= 1.0

    # Heavy rain test
    r_rain = regime_detector.detect_regime(
        temperature_c=27.0,
        humidity=95.0,
        wind_speed_kmh=25.0,
        pressure_hpa=998.0,
        precipitation_mm=55.0,
        weather_code=65,
    )
    assert r_rain["regime"] == "EXTREME_RAIN"

    # Thunderstorm test
    r_ts = regime_detector.detect_regime(
        temperature_c=29.0,
        humidity=88.0,
        wind_speed_kmh=48.0,
        pressure_hpa=996.0,
        precipitation_mm=20.0,
        weather_code=95,
    )
    assert r_ts["regime"] == "THUNDERSTORM"


def test_bias_correction_lapse_rate():
    # High elevation station should adjust down for lapse rate
    val_sea_level = bias_corrector.correct_forecast_value("temperature_c", 30.0, elevation_m=50.0)
    val_mountain = bias_corrector.correct_forecast_value("temperature_c", 30.0, elevation_m=2000.0)
    assert val_mountain < val_sea_level, "Mountain station must adjust lower for lapse rate"


def test_uncertainty_estimator_bounds():
    res = uncertainty_estimator.estimate_uncertainty(
        model_predictions=[30.0, 31.5, 32.2],
        forecast_horizon_hours=48.0,
        regime="NORMAL",
    )
    assert res["lower_c"] < res["prediction_c"] < res["upper_c"]
    assert res["uncertainty_c"] == round(res["upper_c"] - res["lower_c"], 1)
