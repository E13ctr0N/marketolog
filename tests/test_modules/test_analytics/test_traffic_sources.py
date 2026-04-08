"""Tests for traffic_sources tool."""

import httpx
import pytest
import respx

from marketolog.modules.analytics.traffic_sources import run_traffic_sources

METRIKA_STAT_URL = "https://api-metrika.yandex.net/stat/v1/data"

SAMPLE_SOURCES = {
    "data": [
        {"dimensions": [{"name": "organic"}], "metrics": [1200]},
        {"dimensions": [{"name": "direct"}], "metrics": [500]},
        {"dimensions": [{"name": "social"}], "metrics": [300]},
        {"dimensions": [{"name": "referral"}], "metrics": [100]},
    ],
    "totals": [2100],
}


@respx.mock
@pytest.mark.asyncio
async def test_traffic_sources(config_with_keys, cache):
    """Traffic sources report from Metrika."""
    respx.get(METRIKA_STAT_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_SOURCES)
    )
    report = await run_traffic_sources(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )
    assert isinstance(report, str)
    assert "organic" in report
    assert "social" in report
    assert "%" in report


@respx.mock
@pytest.mark.asyncio
async def test_traffic_sources_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    report = await run_traffic_sources(
        counter_id="12345678", config=config_no_keys, cache=cache,
    )
    assert "YANDEX_OAUTH_TOKEN" in report


@respx.mock
@pytest.mark.asyncio
async def test_traffic_sources_cached(config_with_keys, cache):
    """Cached result returned."""
    cache.set("traffic_sources", "12345678:7d", "cached sources", ttl_seconds=3600)
    report = await run_traffic_sources(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )
    assert report == "cached sources"
    assert len(respx.calls) == 0
