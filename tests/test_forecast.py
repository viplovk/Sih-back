"""Tests for forecast and model endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.cache import weather_cache


@pytest.mark.asyncio
async def test_forecast_endpoint_schema():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/forecast?location=Delhi&forecast_hours=24")
    assert response.status_code in (200, 503)
    data = response.json()
    if response.status_code == 200:
        assert "location" in data
        assert data["location"]["name"] == "Delhi"
        assert data["source"] == "open-meteo"
        assert data["mode"] == "forecast"
        assert "fetched_at" in data
        assert "valid_time" in data
        assert "stale" in data
        assert "frames" in data
        assert len(data["frames"]) >= 24
        first_frame = data["frames"][0]
        assert "timestamp" in first_frame
        assert "valid_time" in first_frame
        assert "temperature" in first_frame
        assert "precipitation" in first_frame
        assert "wind_speed" in first_frame
        assert "wind_direction" in first_frame
        assert "humidity" in first_frame
    else:
        assert data["error"] == "weather_data_unavailable"


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


@pytest.mark.asyncio
async def test_model_contribution():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/models/contribution?location=Bengaluru&forecast_hour=24&mode=demo")
    assert response.status_code == 200
    data = response.json()
    if data.get("available") is False:
        assert data["source"] == "open-meteo"
    else:
        assert "weights" in data
        weights = data["weights"]
        assert "Open-Meteo" in weights
        total_w = sum(weights.values())
        assert abs(total_w - 1.0) < 0.005
