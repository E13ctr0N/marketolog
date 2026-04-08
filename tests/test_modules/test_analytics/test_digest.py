"""Tests for weekly digest tool."""

import httpx
import pytest
import respx

from marketolog.modules.analytics.digest import run_weekly_digest

METRIKA_STAT_URL = "https://api-metrika.yandex.net/stat/v1/data"

SAMPLE_WEEKLY_DATA = {
    "data": [
        {"dimensions": [{"name": "organic"}], "metrics": [800, 600, 30.0, 120]},
        {"dimensions": [{"name": "direct"}], "metrics": [400, 300, 35.0, 90]},
        {"dimensions": [{"name": "social"}], "metrics": [200, 150, 25.0, 150]},
    ],
    "totals": [1400, 1050, 30.5, 115],
}


@respx.mock
@pytest.mark.asyncio
async def test_weekly_digest(config_with_keys, cache):
    """Weekly digest with Metrika data."""
    respx.get(METRIKA_STAT_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_WEEKLY_DATA)
    )
    report = await run_weekly_digest(
        counter_id="12345678",
        project_name="test-project",
        config=config_with_keys,
        cache=cache,
    )
    assert isinstance(report, str)
    assert "дайджест" in report.lower() or "Дайджест" in report
    assert "1,400" in report or "1400" in report
    assert "organic" in report or "Поиск" in report


@respx.mock
@pytest.mark.asyncio
async def test_weekly_digest_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    report = await run_weekly_digest(
        counter_id="12345678",
        project_name="test-project",
        config=config_no_keys,
        cache=cache,
    )
    assert "YANDEX_OAUTH_TOKEN" in report


@respx.mock
@pytest.mark.asyncio
async def test_weekly_digest_cached(config_with_keys, cache):
    """Cached result returned."""
    from datetime import date
    week_key = f"12345678:{date.today().isocalendar()[1]}"
    cache.set("weekly_digest", week_key, "cached digest", ttl_seconds=3600)
    report = await run_weekly_digest(
        counter_id="12345678",
        project_name="test-project",
        config=config_with_keys,
        cache=cache,
    )
    assert report == "cached digest"
    assert len(respx.calls) == 0
