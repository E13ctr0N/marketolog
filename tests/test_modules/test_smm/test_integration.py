"""Integration tests — SMM tools registered in MCP server."""

import asyncio
import pytest
from pathlib import Path

from marketolog.server import create_server


@pytest.fixture
def server(tmp_marketolog_dir: Path):
    return create_server(base_dir=tmp_marketolog_dir)


def test_server_has_smm_tools(server):
    """Server must expose all 10 SMM tools."""
    tools = asyncio.run(server._local_provider.list_tools())
    tool_names = {t.name for t in tools}
    expected_smm = {
        "telegram_post", "telegram_stats",
        "vk_post", "vk_stats",
        "max_post", "max_stats",
        "dzen_publish", "trend_research",
        "smm_calendar", "best_time_to_post",
    }
    assert expected_smm.issubset(tool_names), f"Missing: {expected_smm - tool_names}"


def test_server_has_smm_manager_resource(server):
    """Server must expose smm_manager prompt as a resource."""
    resources = asyncio.run(server._local_provider.list_resources())
    resource_uris = {str(r.uri) for r in resources}
    assert any("smm_manager" in uri for uri in resource_uris)


def test_smm_posting_tools_are_mutating(server):
    """Posting tools should have readOnlyHint=False."""
    tools = asyncio.run(server._local_provider.list_tools())
    mutating_tools = {"telegram_post", "vk_post", "max_post", "dzen_publish"}
    for tool in tools:
        if tool.name in mutating_tools:
            assert tool.annotations is not None, f"{tool.name} has no annotations"
            assert tool.annotations.readOnlyHint is False, f"{tool.name} should be MUTATING"


def test_smm_readonly_tools(server):
    """Stats/calendar/trends tools should be readOnlyHint=True."""
    tools = asyncio.run(server._local_provider.list_tools())
    readonly_tools = {
        "telegram_stats", "vk_stats", "max_stats",
        "trend_research", "smm_calendar", "best_time_to_post",
    }
    for tool in tools:
        if tool.name in readonly_tools:
            assert tool.annotations is not None, f"{tool.name} has no annotations"
            assert tool.annotations.readOnlyHint is True, f"{tool.name} should be READ_ONLY"


def test_total_tool_count(server):
    """Server should have exactly 39 tools (6 Core + 8 SEO + 8 Analytics + 7 Content + 10 SMM)."""
    tools = asyncio.run(server._local_provider.list_tools())
    assert len(tools) == 39, f"Expected 39 tools, got {len(tools)}: {[t.name for t in tools]}"
