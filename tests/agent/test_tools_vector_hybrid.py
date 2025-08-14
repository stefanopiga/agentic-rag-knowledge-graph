import os
import pytest
from uuid import UUID

from agent.tools import vector_search_tool, hybrid_search_tool, VectorSearchInput, HybridSearchInput


@pytest.mark.asyncio
async def test_vector_search_tool_offline_cache_path(monkeypatch):
    monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
    tenant_id = UUID("00000000-0000-0000-0000-000000000001")

    inp = VectorSearchInput(query="test query", limit=3)
    results = await vector_search_tool(inp, tenant_id)

    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_hybrid_search_tool_offline_cache_path(monkeypatch):
    monkeypatch.setenv("EMBEDDINGS_OFFLINE", "1")
    tenant_id = UUID("00000000-0000-0000-0000-000000000001")

    inp = HybridSearchInput(query="test query", limit=3, text_weight=0.3)
    results = await hybrid_search_tool(inp, tenant_id)

    assert isinstance(results, list)


