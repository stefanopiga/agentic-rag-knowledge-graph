import pytest
from typing import Generator
from unittest.mock import patch, AsyncMock

# Set test environment before other imports
import os
os.environ.setdefault("APP_ENV", "test")

from agent.graph_utils import GraphitiClient

@pytest.fixture(scope="session")
def graph_client() -> Generator[GraphitiClient, None, None]:
    """Provides a real GraphitiClient instance connected to Neo4j."""
    from dotenv import load_dotenv
    load_dotenv()

    try:
        client = GraphitiClient()
        yield client
    except Exception as e:
        pytest.fail(f"Failed to initialize GraphitiClient for Neo4j: {e}")
