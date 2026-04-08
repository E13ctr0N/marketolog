"""Integration tests — Strategy tools registered in MCP server."""

import asyncio
import pytest
from pathlib import Path

from marketolog.server import create_server


@pytest.fixture
def server(tmp_marketolog_dir: Path):
    return create_server(base_dir=tmp_marketolog_dir)


def test_server_has_strategy_tools(server):
    """Server must expose all 7 Strategy tools."""
    tools = asyncio.run(server._local_provider.list_tools())
    tool_names = {t.name for t in tools}
    expected_strategy = {
        "analyze_target_audience",
        "analyze_positioning",
        "competitor_intelligence",
        "marketing_plan",
        "channel_recommendation",
        "brand_health",
        "ai_visibility",
    }
    assert expected_strategy.issubset(tool_names), f"Missing: {expected_strategy - tool_names}"


def test_strategy_readonly_tools(server):
    """Analysis tools should be readOnlyHint=True."""
    tools = asyncio.run(server._local_provider.list_tools())
    readonly_tools = {
        "analyze_target_audience",
        "analyze_positioning",
        "competitor_intelligence",
        "channel_recommendation",
        "brand_health",
        "ai_visibility",
    }
    for tool in tools:
        if tool.name in readonly_tools:
            assert tool.annotations is not None, f"{tool.name} has no annotations"
            assert tool.annotations.readOnlyHint is True, f"{tool.name} should be READ_ONLY"


def test_marketing_plan_is_mutating(server):
    """marketing_plan should have readOnlyHint=False (creates plan document)."""
    tools = asyncio.run(server._local_provider.list_tools())
    for tool in tools:
        if tool.name == "marketing_plan":
            assert tool.annotations is not None
            assert tool.annotations.readOnlyHint is False, "marketing_plan should be MUTATING"
            break
    else:
        pytest.fail("marketing_plan tool not found")


def test_total_tool_count(server):
    """Server should have exactly 46 tools (6 Core + 8 SEO + 8 Analytics + 7 Content + 10 SMM + 7 Strategy)."""
    tools = asyncio.run(server._local_provider.list_tools())
    assert len(tools) == 46, f"Expected 46 tools, got {len(tools)}: {[t.name for t in tools]}"
