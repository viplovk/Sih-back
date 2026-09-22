"""Tests for extreme weather detection endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_extremes_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/extremes?location=Jaipur&hours=48")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert isinstance(data["events"], list)
    assert data["threshold_basis"] == "configured demonstration thresholds"
    for ev in data["events"]:
        assert "type" in ev
        assert "severity" in ev
        assert "start" in ev
        assert "end" in ev
        assert "peak_value" in ev
        assert ev["is_official_warning"] is False
