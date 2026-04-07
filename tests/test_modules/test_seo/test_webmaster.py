"""Tests for Yandex Webmaster report module.

TDD: write tests first, then implement.
"""

import httpx
import pytest
import respx

from marketolog.modules.seo.webmaster import run_webmaster_report

# ---------------------------------------------------------------------------
# Constants / mock data
# ---------------------------------------------------------------------------

HOST = "https://example.ru"
ENCODED_HOST_ID = "https:example.ru:443"

BASE_URL = "https://api.webmaster.yandex.net/v4"
USER_URL = f"{BASE_URL}/user"
HOSTS_URL = f"{BASE_URL}/user/12345/hosts"
POPULAR_QUERIES_URL = f"{BASE_URL}/user/12345/hosts/{ENCODED_HOST_ID}/search-queries/popular"
DIAGNOSTICS_URL = f"{BASE_URL}/user/12345/hosts/{ENCODED_HOST_ID}/diagnostics"
INDEXING_HISTORY_URL = f"{BASE_URL}/user/12345/hosts/{ENCODED_HOST_ID}/indexing/history"

USER_RESPONSE = {"user_id": "12345"}

HOSTS_RESPONSE = {
    "hosts": [
        {
            "host_id": ENCODED_HOST_ID,
            "unicode_host_url": "https://example.ru",
            "host_url": "https://example.ru",
        }
    ]
}

POPULAR_QUERIES_RESPONSE = {
    "queries": [
        {
            "query_text": "таск трекер",
            "position": 3,
            "clicks": 120,
            "impressions": 1500,
        },
        {
            "query_text": "управление задачами",
            "position": 7,
            "clicks": 80,
            "impressions": 900,
        },
    ]
}

DIAGNOSTICS_RESPONSE = {
    "indicators": [
        {
            "indicator": "SITE_ERROR",
            "severity": "ERROR",
            "message": "Критическая ошибка сервера",
        },
        {
            "indicator": "REDIRECT_LOOP",
            "severity": "WARNING",
            "message": "Обнаружен редирект-цикл",
        },
    ]
}

INDEXING_HISTORY_RESPONSE = {
    "history": [
        {"date": "2026-04-01", "pages_count": 450, "excluded_count": 10},
        {"date": "2026-04-02", "pages_count": 455, "excluded_count": 9},
        {"date": "2026-04-03", "pages_count": 460, "excluded_count": 8},
    ]
}


# ---------------------------------------------------------------------------
# Test 1: full report with all API endpoints mocked
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_webmaster_report(config_with_keys, cache):
    """Full Webmaster report: all API calls mocked, report contains key data."""
    # Mock all endpoints
    respx.get(USER_URL).mock(return_value=httpx.Response(200, json=USER_RESPONSE))
    respx.get(HOSTS_URL).mock(return_value=httpx.Response(200, json=HOSTS_RESPONSE))
    respx.get(POPULAR_QUERIES_URL).mock(
        return_value=httpx.Response(200, json=POPULAR_QUERIES_RESPONSE)
    )
    respx.get(DIAGNOSTICS_URL).mock(
        return_value=httpx.Response(200, json=DIAGNOSTICS_RESPONSE)
    )
    respx.get(INDEXING_HISTORY_URL).mock(
        return_value=httpx.Response(200, json=INDEXING_HISTORY_RESPONSE)
    )

    report = await run_webmaster_report(HOST, config=config_with_keys, cache=cache)

    assert isinstance(report, str)
    assert len(report) > 0

    # Popular queries section — must contain query text
    assert "таск трекер" in report

    # Indexing section
    lower = report.lower()
    assert "индексац" in lower

    # Result is cached
    cached = cache.get("webmaster", HOST)
    assert cached == report


# ---------------------------------------------------------------------------
# Test 2: no token → setup instructions with env var name
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_webmaster_report_no_token(config_no_keys, cache):
    """Without YANDEX_OAUTH_TOKEN config returns setup instructions."""
    report = await run_webmaster_report(HOST, config=config_no_keys, cache=cache)

    assert "YANDEX_OAUTH_TOKEN" in report
