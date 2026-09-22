"""Tests for uncertainty bounds endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_uncertainty_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/uncertainty?location=Mumbai&hours=24")
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "Mumbai"
    assert "prediction_c" in data
    assert "lower_c" in data
    assert "upper_c" in data
    assert "uncertainty_c" in data
    assert data["lower_c"] <= data["prediction_c"] <= data["upper_c"]
    assert "estimated uncertainty" in data["calibration_note"]
    assert "contributing_models" in data
    assert len(data["contributing_models"]) == 3
