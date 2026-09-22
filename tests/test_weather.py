"""Tests for current weather retrieval, coordinates, freshness, and cache behavior."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.cache import weather_cache


@pytest.mark.asyncio
async def test_weather_with_named_location():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/weather?location=Delhi")
    assert response.status_code in (200, 503)
    data = response.json()
    if response.status_code == 200:
        assert data["location"]["name"] == "Delhi"
        assert data["source"] == "open-meteo"
        assert data["mode"] == "live"
        assert "temperature" in data
        assert "humidity" in data
        assert "wind_speed" in data
        assert "pressure" in data
        assert "fetched_at" in data
        assert "valid_time" in data
        assert "stale" in data
        assert "age_seconds" in data
        assert "current" in data
        assert "temperature_c" in data["current"]
    else:
        assert data["error"] == "weather_data_unavailable"
        assert data["source"] == "open-meteo"
        assert data["retryable"] is True


@pytest.mark.asyncio
async def test_weather_with_coordinates():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/weather?lat=19.076&lon=72.8777")
    assert response.status_code in (200, 503)
    data = response.json()
    if response.status_code == 200:
        assert "current" in data
        assert -50.0 <= data["temperature"] <= 60.0
        assert data["stale"] is False
    else:
        assert data["error"] == "weather_data_unavailable"


@pytest.mark.asyncio
async def test_weather_cache_and_stale_fallback():
    key = "weather:28.6139:77.209"
    cached_data = {
        "current": {
            "time": "2026-09-22T10:00",
            "temperature_2m": 32.5,
            "apparent_temperature": 34.0,
            "relative_humidity_2m": 65,
            "wind_speed_10m": 12.0,
            "wind_direction_10m": 180.0,
            "surface_pressure": 1010.0,
            "precipitation": 0.0,
            "weather_code": 1,
        }
    }
    # Pre-populate cache
    weather_cache.set(key, cached_data, source="open-meteo", valid_time="2026-09-22T10:00", ttl_seconds=60)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/weather?lat=28.6139&lon=77.2090")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "open-meteo"
    assert data["temperature"] == 32.5
    assert data["humidity"] == 65
    assert data["stale"] is False


@pytest.mark.asyncio
async def test_weather_invalid_latitude():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/weather?lat=95.0&lon=77.0")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_COORDINATES"


@pytest.mark.asyncio
async def test_weather_invalid_longitude():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/weather?lat=28.0&lon=200.0")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_COORDINATES"
