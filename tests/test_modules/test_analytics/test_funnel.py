"""Tests for funnel analysis tool."""

import httpx
import pytest
import respx

from marketolog.modules.analytics.funnel import run_funnel_analysis

METRIKA_STAT_URL = "https://api-metrika.yandex.net/stat/v1/data"
METRIKA_GOALS_URL = "https://api-metrika.yandex.net/management/v1/counter/12345678/goals"

SAMPLE_GOALS = {
    "goals": [
        {"id": 1, "name": "Регистрация", "type": "url"},
        {"id": 2, "name": "Покупка", "type": "action"},
    ]
}

SAMPLE_FUNNEL_DATA = {
    "data": [
        {"dimensions": [{"name": "organic"}], "metrics": [1000, 50, 5.0, 10, 1.0]},
        {"dimensions": [{"name": "direct"}], "metrics": [500, 20, 4.0, 3, 0.6]},
    ],
    "totals": [1500, 70, 4.7, 13, 0.87],
}


@respx.mock
@pytest.mark.asyncio
async def test_funnel_analysis(config_with_keys, cache):
    """Funnel analysis with goals data."""
    respx.get(METRIKA_GOALS_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_GOALS)
    )
    respx.get(METRIKA_STAT_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_FUNNEL_DATA)
    )
    report = await run_funnel_analysis(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )
    assert isinstance(report, str)
    assert "Регистрация" in report or "воронк" in report.lower()
    assert "organic" in report


@respx.mock
@pytest.mark.asyncio
async def test_funnel_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    report = await run_funnel_analysis(
        counter_id="12345678", config=config_no_keys, cache=cache,
    )
    assert "YANDEX_OAUTH_TOKEN" in report


@respx.mock
@pytest.mark.asyncio
async def test_funnel_specific_goal(config_with_keys, cache):
    """Request analysis for a specific goal."""
    respx.get(METRIKA_GOALS_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_GOALS)
    )
    respx.get(METRIKA_STAT_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_FUNNEL_DATA)
    )
    report = await run_funnel_analysis(
        counter_id="12345678", config=config_with_keys, cache=cache,
        goal="Регистрация",
    )
    assert isinstance(report, str)
    assert "Регистрация" in report
