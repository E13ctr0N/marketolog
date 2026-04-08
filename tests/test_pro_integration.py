"""Integration tests — free vs pro tool split."""

import asyncio
import sys
from pathlib import Path
from unittest import mock

import pytest

from marketolog.server import create_server


@pytest.fixture
def server(tmp_marketolog_dir: Path):
    return create_server(base_dir=tmp_marketolog_dir)


FREE_TOOLS = {
    "create_project", "switch_project", "list_projects",
    "update_project", "delete_project", "get_project_context",
    "seo_audit", "ai_seo_check", "keyword_research",
    "generate_utm_link",
}

PRO_TOOLS = {
    "keyword_cluster", "check_positions", "analyze_competitors",
    "content_gap", "webmaster_report",
    "metrika_report", "metrika_goals", "search_console_report",
    "traffic_sources", "funnel_analysis", "weekly_digest", "ai_referral_report",
    "content_plan", "generate_article", "generate_post",
    "optimize_text", "analyze_content", "generate_meta", "repurpose_content",
    "telegram_post", "telegram_stats", "vk_post", "vk_stats",
    "max_post", "max_stats", "dzen_publish",
    "trend_research", "smm_calendar", "best_time_to_post",
    "analyze_target_audience", "analyze_positioning",
    "competitor_intelligence", "marketing_plan",
    "channel_recommendation", "brand_health", "ai_visibility",
}


def test_with_pro_installed(server):
    """With Pro installed, server exposes all 46 tools."""
    tools = asyncio.run(server._local_provider.list_tools())
    tool_names = {t.name for t in tools}
    assert FREE_TOOLS.issubset(tool_names), f"Missing free: {FREE_TOOLS - tool_names}"
    assert PRO_TOOLS.issubset(tool_names), f"Missing pro: {PRO_TOOLS - tool_names}"
    assert len(tools) == 46


def test_without_pro_installed(tmp_marketolog_dir: Path):
    """Without Pro, server exposes only 10 free tools."""
    with mock.patch.dict(sys.modules, {"marketolog_pro": None, "marketolog_pro._register": None}):
        server = create_server(base_dir=tmp_marketolog_dir)
        tools = asyncio.run(server._local_provider.list_tools())
        tool_names = {t.name for t in tools}
        assert FREE_TOOLS.issubset(tool_names), f"Missing free: {FREE_TOOLS - tool_names}"
        assert len(tool_names & PRO_TOOLS) == 0, f"Pro tools present without pro: {tool_names & PRO_TOOLS}"
        assert len(tools) == 10, f"Expected 10 free tools, got {len(tools)}: {[t.name for t in tools]}"


def test_free_server_has_all_prompts(tmp_marketolog_dir: Path):
    """Prompts are available even without Pro."""
    with mock.patch.dict(sys.modules, {"marketolog_pro": None, "marketolog_pro._register": None}):
        server = create_server(base_dir=tmp_marketolog_dir)
        resources = asyncio.run(server._local_provider.list_resources())
        resource_uris = {str(r.uri) for r in resources}
        expected = {"strategist", "seo_expert", "analyst", "content_writer", "smm_manager"}
        for name in expected:
            assert any(name in uri for uri in resource_uris), f"Missing prompt: {name}"
