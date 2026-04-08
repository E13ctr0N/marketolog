import asyncio
import pytest
from pathlib import Path

from marketolog.server import create_server


@pytest.fixture
def server(tmp_marketolog_dir: Path):
    return create_server(base_dir=tmp_marketolog_dir)


def test_server_has_seo_tools(server):
    """Server must expose all 8 SEO tools."""
    tools = asyncio.run(server._local_provider.list_tools())
    tool_names = {t.name for t in tools}
    expected_seo = {
        "seo_audit", "ai_seo_check", "keyword_research", "keyword_cluster",
        "check_positions", "analyze_competitors", "content_gap", "webmaster_report",
    }
    assert expected_seo.issubset(tool_names), f"Missing SEO tools: {expected_seo - tool_names}"


def test_server_has_seo_resource(server):
    """Server must expose seo_expert prompt as a resource."""
    resources = asyncio.run(server._local_provider.list_resources())
    resource_uris = {str(r.uri) for r in resources}
    assert any("seo_expert" in uri for uri in resource_uris)


def test_seo_tools_are_read_only(server):
    """All SEO tools should have readOnlyHint=True."""
    tools = asyncio.run(server._local_provider.list_tools())
    seo_tools = {
        "seo_audit", "ai_seo_check", "keyword_research", "keyword_cluster",
        "check_positions", "analyze_competitors", "content_gap", "webmaster_report",
    }
    for tool in tools:
        if tool.name in seo_tools:
            assert tool.annotations is not None, f"{tool.name} has no annotations"
            assert tool.annotations.readOnlyHint is True, f"{tool.name} should be readOnlyHint=True"


def test_total_tool_count(server):
    """Server should have exactly 29 tools (6 Core + 8 SEO + 8 Analytics + 7 Content)."""
    tools = asyncio.run(server._local_provider.list_tools())
    assert len(tools) == 29, f"Expected 29 tools, got {len(tools)}: {[t.name for t in tools]}"
