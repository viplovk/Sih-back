"""Tests for forecast and model endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_forecast_default():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/forecast?location=Delhi&forecast_hours=24")
    assert response.status_code == 200
    data = response.json()
    assert "location" in data
    assert data["location"]["name"] == "Delhi"
    assert "forecast" in data
    assert len(data["forecast"]) == 24
    first_pt = data["forecast"][0]
    assert "temperature_c" in first_pt
    assert "feels_like_c" in first_pt
    assert "humidity" in first_pt
    assert "wind_speed_kmh" in first_pt
    assert "pressure_hpa" in first_pt
    assert "precipitation_probability" in first_pt
    assert "weather_code" in first_pt


@pytest.mark.asyncio
async def test_models_list():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    model_ids = [m["id"] for m in data["models"]]
    assert "open-meteo" in model_ids
    assert "demo-ai" in model_ids
    assert "demo-nwp" in model_ids
    for m in data["models"]:
        if m["id"] in ("demo-ai", "demo-nwp"):
            assert m["is_demo"] is True
            assert m["status"] == "SIMULATED"


@pytest.mark.asyncio
async def test_model_contribution():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/models/contribution?location=Bengaluru&forecast_hour=24")
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "Bengaluru"
    assert "regime" in data
    assert "weights" in data
    weights = data["weights"]
    assert "Open-Meteo" in weights
    assert "AI-Demo" in weights
    assert "NWP-Demo" in weights
    # Weights sum to 1.0 within floating point precision
    total_w = sum(weights.values())
    assert abs(total_w - 1.0) < 0.005
    for k, v in weights.items():
        assert 0.0 <= v <= 1.0
