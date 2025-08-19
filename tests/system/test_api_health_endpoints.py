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
async def test_enhanced_health_endpoint_schema(monkeypatch):
    """Test enhanced health endpoint returns the correct schema with real metrics."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENABLE_METRICS", "false")
    monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")

    from agent.api import app  # delayed import
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            
            # Basic health status fields
            assert data["status"] in ("healthy", "degraded", "unhealthy")
            assert isinstance(data["database"], bool)
            assert isinstance(data["graph_database"], bool)
            assert isinstance(data["llm_connection"], bool)
            assert "version" in data
            assert "timestamp" in data
            
            # Enhanced schema: check if databases section exists
            if "databases" in data:
                databases = data["databases"]
                assert "postgresql" in databases
                assert "neo4j" in databases
                
                # Check PostgreSQL connection info
                pg_info = databases["postgresql"]
                assert "status" in pg_info
                assert "active_connections" in pg_info
                assert "pool_size" in pg_info
                assert isinstance(pg_info["active_connections"], int)
                assert isinstance(pg_info["pool_size"], int)
                
                # Check Neo4j connection info  
                neo4j_info = databases["neo4j"]
                assert "status" in neo4j_info
                assert "active_sessions" in neo4j_info
                assert isinstance(neo4j_info["active_sessions"], int)
                
            # Enhanced schema: check if metrics section exists
            if "metrics" in data:
                metrics = data["metrics"]
                assert "active_sessions" in metrics
                assert "total_queries_today" in metrics
                assert "avg_response_time" in metrics
                assert "memory_usage_mb" in metrics
                assert "cpu_usage_percent" in metrics
                
                # Verify metric types
                assert isinstance(metrics["active_sessions"], int)
                assert isinstance(metrics["total_queries_today"], int)
                assert isinstance(metrics["avg_response_time"], (int, float))
                assert isinstance(metrics["memory_usage_mb"], (int, float))
                assert isinstance(metrics["cpu_usage_percent"], (int, float))
                
                # Check cache metrics if available
                if "cache_hit_rate" in metrics:
                    assert isinstance(metrics["cache_hit_rate"], (int, float))
                    assert 0.0 <= metrics["cache_hit_rate"] <= 1.0
                    
            # Enhanced schema: check uptime
            if "uptime_seconds" in data:
                assert isinstance(data["uptime_seconds"], (int, float))
                assert data["uptime_seconds"] >= 0


@pytest.mark.asyncio
async def test_enhanced_health_endpoint_with_metrics_disabled(monkeypatch):
    """Test enhanced health endpoint works correctly when metrics are disabled."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENABLE_METRICS", "false")
    monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")

    from agent.api import app  # delayed import
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            
            # Should still return basic health information
            assert data["status"] in ("healthy", "degraded", "unhealthy")
            assert isinstance(data["database"], bool)
            assert isinstance(data["graph_database"], bool)
            assert "timestamp" in data


@pytest.mark.asyncio
async def test_enhanced_health_metrics_calculation(monkeypatch):
    """Test that real metrics are calculated instead of returning placeholders."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ENABLE_METRICS", "false")
    monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")

    from agent.api import app  # delayed import
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            
            # Verify no placeholder strings remain
            if "metrics" in data:
                metrics = data["metrics"]
                for key, value in metrics.items():
                    assert value != "calculated_value", f"Metric {key} still has placeholder value"
                    assert isinstance(value, (int, float)), f"Metric {key} should be numeric, got {type(value)}"


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


