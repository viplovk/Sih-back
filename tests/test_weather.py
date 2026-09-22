"""Tests for current weather retrieval and coordinate handling."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_weather_with_named_location():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/weather?location=Delhi")
    assert response.status_code == 200
    data = response.json()
    assert data["location"]["name"] == "Delhi"
    assert "current" in data
    assert "temperature_c" in data["current"]
    assert "humidity" in data["current"]
    assert "wind_speed_kmh" in data["current"]
    assert "pressure_hpa" in data["current"]


@pytest.mark.asyncio
async def test_weather_with_coordinates():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/weather?lat=19.076&lon=72.8777")
    assert response.status_code == 200
    data = response.json()
    assert "current" in data
    assert -50.0 <= data["current"]["temperature_c"] <= 60.0


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
