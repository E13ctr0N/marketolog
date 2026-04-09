"""Tests for trend research tool."""

import httpx
import pytest
import respx

from marketolog.modules.smm.trends import run_trend_research

EXA_API = "https://api.exa.ai/search"


@respx.mock
@pytest.mark.asyncio
async def test_trend_research(config_with_keys, cache):
    """Trend research with Exa API."""
    respx.post(EXA_API).mock(
        return_value=httpx.Response(200, json={
            "results": [
                {"title": "AI в маркетинге 2026", "url": "https://example.com/1", "score": 0.95},
                {"title": "Тренды SMM весна 2026", "url": "https://example.com/2", "score": 0.88},
                {"title": "Автоматизация контента", "url": "https://example.com/3", "score": 0.82},
            ]
        })
    )

    result = await run_trend_research(
        topic="маркетинг",
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "AI в маркетинге" in result or "тренд" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_trend_research_no_key(config_no_keys, cache):
    """Without Exa key — returns basic suggestions."""
    result = await run_trend_research(
        topic="маркетинг",
        config=config_no_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    # Should still return something useful (niche-based)
    assert len(result) > 50


@respx.mock
@pytest.mark.asyncio
async def test_trend_research_cached(config_with_keys, cache):
    """Cached result returned."""
    cache.set("trends", "маркетинг:exa=True", "cached trends", ttl_seconds=3600)

    result = await run_trend_research(
        topic="маркетинг",
        config=config_with_keys,
        cache=cache,
    )

    assert result == "cached trends"
    assert len(respx.calls) == 0
