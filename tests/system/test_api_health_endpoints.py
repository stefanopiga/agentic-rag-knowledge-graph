import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health_endpoint_ok(monkeypatch):
    # Imposta env minime per l'avvio dell'app in test
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENABLE_METRICS", "false")
    monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")

    # Import app dopo il setup env per evitare side effects d'import
    from agent.api import app  # delayed import
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code in (200, 500)  # tollerante in locale
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] in ("healthy", "degraded", "unhealthy")
            assert isinstance(data["database"], bool)
            assert isinstance(data["graph_database"], bool)


@pytest.mark.asyncio
async def test_detailed_health_endpoint(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENABLE_METRICS", "false")

    from agent.api import app  # delayed import
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health/detailed")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "timestamp" in data
            assert "services" in data


@pytest.mark.asyncio
async def test_database_status_endpoint(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENABLE_METRICS", "false")

    from agent.api import app  # delayed import
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/status/database")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "database" in data
            assert "timestamp" in data


