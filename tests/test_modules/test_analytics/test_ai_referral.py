"""Tests for AI referral report tool."""

import httpx
import pytest
import respx

from marketolog.modules.analytics.ai_referral import run_ai_referral_report

METRIKA_STAT_URL = "https://api-metrika.yandex.net/stat/v1/data"

SAMPLE_REFERRER_DATA = {
    "data": [
        {"dimensions": [{"name": "chat.openai.com"}], "metrics": [45, 30]},
        {"dimensions": [{"name": "perplexity.ai"}], "metrics": [20, 15]},
        {"dimensions": [{"name": "claude.ai"}], "metrics": [10, 8]},
        {"dimensions": [{"name": "google.com"}], "metrics": [500, 350]},
        {"dimensions": [{"name": "yandex.ru"}], "metrics": [300, 200]},
    ],
    "totals": [875, 603],
}


@respx.mock
@pytest.mark.asyncio
async def test_ai_referral_report(config_with_keys, cache):
    """AI referral report identifies AI search traffic."""
    respx.get(METRIKA_STAT_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_REFERRER_DATA)
    )
    report = await run_ai_referral_report(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )
    assert isinstance(report, str)
    assert "ChatGPT" in report or "chat.openai.com" in report
    assert "Perplexity" in report or "perplexity.ai" in report
    assert "Claude" in report or "claude.ai" in report


@respx.mock
@pytest.mark.asyncio
async def test_ai_referral_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    report = await run_ai_referral_report(
        counter_id="12345678", config=config_no_keys, cache=cache,
    )
    assert "YANDEX_OAUTH_TOKEN" in report


@respx.mock
@pytest.mark.asyncio
async def test_ai_referral_no_ai_traffic(config_with_keys, cache):
    """When no AI referrer domains found — report says so."""
    no_ai_data = {
        "data": [
            {"dimensions": [{"name": "google.com"}], "metrics": [500, 350]},
            {"dimensions": [{"name": "yandex.ru"}], "metrics": [300, 200]},
        ],
        "totals": [800, 550],
    }
    respx.get(METRIKA_STAT_URL).mock(
        return_value=httpx.Response(200, json=no_ai_data)
    )
    report = await run_ai_referral_report(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )
    assert "не обнаружен" in report.lower() or "0" in report
