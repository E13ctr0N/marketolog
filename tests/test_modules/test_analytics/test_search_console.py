"""Tests for Google Search Console report tool."""

import httpx
import pytest
import respx

from marketolog.modules.analytics.search_console import run_search_console_report

SC_API_URL = "https://www.googleapis.com/webmasters/v3/sites/https%3A%2F%2Fexample.ru/searchAnalytics/query"

SAMPLE_SC_RESPONSE = {
    "rows": [
        {
            "keys": ["таск трекер"],
            "clicks": 120,
            "impressions": 3500,
            "ctr": 0.034,
            "position": 6.2,
        },
        {
            "keys": ["управление задачами"],
            "clicks": 85,
            "impressions": 2100,
            "ctr": 0.040,
            "position": 8.5,
        },
        {
            "keys": ["бесплатный таск трекер"],
            "clicks": 30,
            "impressions": 800,
            "ctr": 0.037,
            "position": 14.1,
        },
    ],
    "responseAggregationType": "byPage",
}


@respx.mock
@pytest.mark.asyncio
async def test_search_console_report(config_with_keys, cache, monkeypatch):
    """Full SC report with mocked API and mocked auth."""
    import marketolog.modules.analytics.search_console as sc_mod
    monkeypatch.setattr(sc_mod, "_get_access_token", lambda creds_path: "fake-token")

    respx.post(SC_API_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_SC_RESPONSE)
    )

    report = await run_search_console_report(
        site_url="https://example.ru",
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(report, str)
    assert "таск трекер" in report
    assert "120" in report


@respx.mock
@pytest.mark.asyncio
async def test_search_console_report_cached(config_with_keys, cache, monkeypatch):
    """Cached result returns without HTTP calls."""
    cache.set("search_console", "https://example.ru:7d", "cached SC report", ttl_seconds=3600)

    report = await run_search_console_report(
        site_url="https://example.ru",
        config=config_with_keys,
        cache=cache,
    )

    assert report == "cached SC report"
    assert len(respx.calls) == 0


@respx.mock
@pytest.mark.asyncio
async def test_search_console_no_credentials(config_no_keys, cache):
    """Without credentials — returns setup instructions."""
    report = await run_search_console_report(
        site_url="https://example.ru",
        config=config_no_keys,
        cache=cache,
    )

    assert "GOOGLE_SC_CREDENTIALS" in report
