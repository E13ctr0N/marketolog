"""Integration tests — analytics tools registered in MCP server."""

import asyncio
import pytest
from pathlib import Path

from marketolog.server import create_server


@pytest.fixture
def server(tmp_marketolog_dir: Path):
    return create_server(base_dir=tmp_marketolog_dir)


def test_server_has_analytics_tools(server):
    """Server must expose all 8 analytics tools."""
    tools = asyncio.run(server._local_provider.list_tools())
    tool_names = {t.name for t in tools}
    expected_analytics = {
        "metrika_report", "metrika_goals", "search_console_report",
        "traffic_sources", "funnel_analysis", "weekly_digest",
        "ai_referral_report", "generate_utm_link",
    }
    assert expected_analytics.issubset(tool_names), f"Missing: {expected_analytics - tool_names}"


def test_server_has_analyst_resource(server):
    """Server must expose analyst prompt as a resource."""
    resources = asyncio.run(server._local_provider.list_resources())
    resource_uris = {str(r.uri) for r in resources}
    assert any("analyst" in uri for uri in resource_uris)


def test_analytics_tools_are_read_only(server):
    """All analytics tools should have readOnlyHint=True."""
    tools = asyncio.run(server._local_provider.list_tools())
    analytics_tools = {
        "metrika_report", "metrika_goals", "search_console_report",
        "traffic_sources", "funnel_analysis", "weekly_digest",
        "ai_referral_report", "generate_utm_link",
    }
    for tool in tools:
        if tool.name in analytics_tools:
            assert tool.annotations is not None, f"{tool.name} has no annotations"
            assert tool.annotations.readOnlyHint is True, f"{tool.name} should be readOnlyHint=True"


def test_total_tool_count(server):
    """Server should have exactly 46 tools (6 Core + 8 SEO + 8 Analytics + 7 Content + 10 SMM + 7 Strategy)."""
    tools = asyncio.run(server._local_provider.list_tools())
    assert len(tools) == 46, f"Expected 46 tools, got {len(tools)}: {[t.name for t in tools]}"
