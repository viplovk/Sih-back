"""Tests for geospatial map temperature endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_map_temperature_demo_resolution():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/map/temperature?resolution=demo")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "grid" in data
    assert len(data["grid"]) > 20
    first_pt = data["grid"][0]
    assert "lat" in first_pt
    assert "lon" in first_pt
    assert "temperature_c" in first_pt
    assert 5.0 <= first_pt["temperature_c"] <= 55.0


@pytest.mark.asyncio
async def test_map_temperature_forecast_hour():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/map/temperature?forecast_hour=12&resolution=demo")
    assert response.status_code == 200
    data = response.json()
    assert "grid" in data
    assert "min_temperature_c" in data
    assert "max_temperature_c" in data
