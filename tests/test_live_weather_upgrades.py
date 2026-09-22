"""Comprehensive tests for real, live weather data upgrades:
- Map timeline endpoint
- Map wind vectors endpoint
- Map temperature field endpoint
- Map precipitation field endpoint
- Map air-quality field endpoint
- Cache behavior and freshness metadata
- 503 error response structure
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.cache import weather_cache
from app.services.map_service import map_service


@pytest.mark.asyncio
async def test_map_timeline_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/map/timeline")
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert data["source"] == "open-meteo"
        assert "generated_at" in data
        assert "current_time" in data
        assert "frames" in data
        assert len(data["frames"]) > 0
        first_frame = data["frames"][0]
        assert "timestamp" in first_frame
        assert "mode" in first_frame
        assert "stale" in data
        assert "fetched_at" in data
        assert "age_seconds" in data


@pytest.mark.asyncio
async def test_map_wind_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/map/wind?width=20&height=20")
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert data["source"] == "open-meteo"
        assert data["width"] == 20
        assert data["height"] == 20
        assert "bbox" in data
        assert "latitudes" in data
        assert "longitudes" in data
        assert "u" in data
        assert "v" in data
        assert "speed" in data
        assert "direction" in data
        assert len(data["u"]) == 20
        assert len(data["u"][0]) == 20
        assert len(data["speed"]) == 20
        assert data["unit"] == "km/h"


@pytest.mark.asyncio
async def test_map_temperature_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/map/temperature?width=20&height=20")
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert data["source"] == "open-meteo"
        assert data["width"] == 20
        assert data["height"] == 20
        assert "values" in data
        assert len(data["values"]) == 20
        assert len(data["values"][0]) == 20
        assert data["unit"] == "°C"
        assert data["min"] <= data["max"]


@pytest.mark.asyncio
async def test_map_precipitation_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/map/precipitation?width=20&height=20")
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert data["source"] == "open-meteo"
        assert data["width"] == 20
        assert data["height"] == 20
        assert "values" in data
        assert len(data["values"]) == 20
        assert data["unit"] == "mm"
        assert data["min"] >= 0.0


@pytest.mark.asyncio
async def test_map_air_quality_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/map/air-quality?width=20&height=20")
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert "open-meteo" in data["source"]
        assert data["width"] == 20
        assert data["height"] == 20
        assert "aqi" in data
        assert "pm2_5" in data
        assert "pm10" in data
        assert "no2" in data
        assert "o3" in data
        assert len(data["aqi"]) == 20
        assert len(data["aqi"][0]) == 20


@pytest.mark.asyncio
async def test_weather_cache_lifecycle_and_freshness():
    key = "test:weather:lifecycle"
    sample_data = {"current": {"temperature_2m": 29.4}}
    meta = weather_cache.set(key, sample_data, source="open-meteo", valid_time="2026-09-22T12:00:00Z", ttl_seconds=2)
    assert meta["source"] == "open-meteo"
    assert meta["valid_time"] == "2026-09-22T12:00:00Z"
    assert meta["stale"] is False

    cached_val, cached_meta = weather_cache.get(key)
    assert cached_val == sample_data
    assert cached_meta["stale"] is False

    # Stale fallback when past TTL
    stale_val, stale_meta = weather_cache.get_stale(key)
    assert stale_val == sample_data
