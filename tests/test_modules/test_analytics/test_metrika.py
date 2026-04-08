"""Tests for Yandex Metrika report and goals tools."""

import httpx
import pytest
import respx

from marketolog.modules.analytics.metrika import run_metrika_report, run_metrika_goals

METRIKA_BASE = "https://api-metrika.yandex.net"
STAT_URL = f"{METRIKA_BASE}/stat/v1/data"
GOALS_URL = f"{METRIKA_BASE}/management/v1/counter/12345678/goals"

SAMPLE_STAT_RESPONSE = {
    "total_rows": 3,
    "data": [
        {
            "dimensions": [{"name": "organic"}],
            "metrics": [1200, 800, 35.5, 2.1],
        },
        {
            "dimensions": [{"name": "direct"}],
            "metrics": [500, 400, 40.0, 1.8],
        },
        {
            "dimensions": [{"name": "social"}],
            "metrics": [300, 250, 28.0, 3.0],
        },
    ],
    "total_rows_rounded": False,
    "totals": [2000, 1450, 34.5, 2.3],
}

SAMPLE_GOALS_RESPONSE = {
    "goals": [
        {"id": 1, "name": "Регистрация", "type": "url", "conditions": []},
        {"id": 2, "name": "Покупка", "type": "action", "conditions": []},
    ]
}


@respx.mock
@pytest.mark.asyncio
async def test_metrika_report(config_with_keys, cache):
    """Full metrika report with mocked API."""
    respx.get(STAT_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_STAT_RESPONSE)
    )
    report = await run_metrika_report(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )
    assert isinstance(report, str)
    assert "organic" in report
    assert "2000" in report or "2,000" in report or "2000" in report.replace(",", "")


@respx.mock
@pytest.mark.asyncio
async def test_metrika_report_cached(config_with_keys, cache):
    """Cached result returns without HTTP calls."""
    cache.set("metrika_report", "12345678:7d:default", "cached report", ttl_seconds=3600)
    report = await run_metrika_report(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )
    assert report == "cached report"
    assert len(respx.calls) == 0


@respx.mock
@pytest.mark.asyncio
async def test_metrika_report_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    report = await run_metrika_report(
        counter_id="12345678", config=config_no_keys, cache=cache,
    )
    assert "YANDEX_OAUTH_TOKEN" in report


@respx.mock
@pytest.mark.asyncio
async def test_metrika_goals(config_with_keys, cache):
    """Fetch goals list."""
    respx.get(GOALS_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_GOALS_RESPONSE)
    )
    report = await run_metrika_goals(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )
    assert "Регистрация" in report
    assert "Покупка" in report


@respx.mock
@pytest.mark.asyncio
async def test_metrika_goals_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    report = await run_metrika_goals(
        counter_id="12345678", config=config_no_keys, cache=cache,
    )
    assert "YANDEX_OAUTH_TOKEN" in report
