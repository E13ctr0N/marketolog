import asyncio
import pytest
from pathlib import Path

from marketolog.server import create_server


@pytest.fixture
def server(tmp_marketolog_dir: Path):
    return create_server(base_dir=tmp_marketolog_dir)


def test_server_has_core_tools(server):
    """Server must expose all 6 Core tools."""
    tools = asyncio.run(server._local_provider.list_tools())
    tool_names = {t.name for t in tools}
    expected = {
        "create_project", "switch_project", "list_projects",
        "update_project", "delete_project", "get_project_context",
    }
    assert expected.issubset(tool_names), f"Missing tools: {expected - tool_names}"


def test_server_has_strategist_resource(server):
    """Server must expose strategist prompt as a resource."""
    resources = asyncio.run(server._local_provider.list_resources())
    resource_uris = {str(r.uri) for r in resources}
    assert any("strategist" in uri for uri in resource_uris), (
        f"No strategist resource found. Resources: {resource_uris}"
    )
