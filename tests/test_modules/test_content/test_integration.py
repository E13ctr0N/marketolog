"""Integration tests — content tools registered in MCP server."""
import asyncio
import pytest
from pathlib import Path
from marketolog.server import create_server

@pytest.fixture
def server(tmp_marketolog_dir: Path):
    return create_server(base_dir=tmp_marketolog_dir)

def test_server_has_content_tools(server):
    tools = asyncio.run(server._local_provider.list_tools())
    tool_names = {t.name for t in tools}
    expected_content = {
        "content_plan", "generate_article", "generate_post",
        "optimize_text", "analyze_content", "generate_meta",
        "repurpose_content",
    }
    assert expected_content.issubset(tool_names), f"Missing: {expected_content - tool_names}"

def test_server_has_content_writer_resource(server):
    resources = asyncio.run(server._local_provider.list_resources())
    resource_uris = {str(r.uri) for r in resources}
    assert any("content_writer" in uri for uri in resource_uris)

def test_content_tools_are_read_only(server):
    tools = asyncio.run(server._local_provider.list_tools())
    content_tools = {
        "content_plan", "generate_article", "generate_post",
        "optimize_text", "analyze_content", "generate_meta",
        "repurpose_content",
    }
    for tool in tools:
        if tool.name in content_tools:
            assert tool.annotations is not None, f"{tool.name} has no annotations"
            assert tool.annotations.readOnlyHint is True, f"{tool.name} should be readOnlyHint=True"

def test_total_tool_count(server):
    """Server should have exactly 46 tools (6 Core + 8 SEO + 8 Analytics + 7 Content + 10 SMM + 7 Strategy)."""
    tools = asyncio.run(server._local_provider.list_tools())
    assert len(tools) == 46, f"Expected 46 tools, got {len(tools)}: {[t.name for t in tools]}"
