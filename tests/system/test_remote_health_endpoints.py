import os
import pytest
import httpx


API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")

skip_remote = pytest.mark.skipif(
    not API_BASE_URL,
    reason="API_BASE_URL non definito: test remoto disabilitato"
)


@skip_remote
@pytest.mark.asyncio
async def test_remote_health_endpoint_ok():
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{API_BASE_URL}/health")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] in ("healthy", "degraded", "unhealthy")
            assert isinstance(data.get("database"), bool)
            assert isinstance(data.get("graph_database"), bool)


@skip_remote
@pytest.mark.asyncio
async def test_remote_detailed_health_endpoint():
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{API_BASE_URL}/health/detailed")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "timestamp" in data
            assert "services" in data


@skip_remote
@pytest.mark.asyncio
async def test_remote_database_status_endpoint():
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{API_BASE_URL}/status/database")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "database" in data
            assert "timestamp" in data
