"""Tests for competitor_intelligence tool."""

import httpx
import pytest
import respx

from marketolog.modules.strategy.intelligence import run_competitor_intelligence

EXA_API = "https://api.exa.ai/search"


@respx.mock
@pytest.mark.asyncio
async def test_intelligence_with_exa(config_with_keys, cache, project_context):
    """Deep competitor analysis using Exa API."""
    respx.post(EXA_API).mock(
        return_value=httpx.Response(200, json={
            "results": [
                {"title": "Trello pricing review", "url": "https://example.com/1", "text": "Trello offers free tier..."},
                {"title": "Trello vs alternatives", "url": "https://example.com/2", "text": "Comparison shows..."},
            ]
        })
    )

    result = await run_competitor_intelligence(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "Trello" in result
    assert "конкурент" in result.lower() or "анализ" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_intelligence_with_explicit_urls(config_with_keys, cache, project_context):
    """Analyze specific competitor URLs."""
    respx.post(EXA_API).mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    result = await run_competitor_intelligence(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
        competitor_urls=["https://competitor.ru"],
    )

    assert isinstance(result, str)
    assert len(result) > 50


@respx.mock
@pytest.mark.asyncio
async def test_intelligence_no_exa(config_no_keys, cache, project_context):
    """Without Exa — returns context-based analysis."""
    result = await run_competitor_intelligence(
        project_context=project_context,
        config=config_no_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "Trello" in result or "конкурент" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_intelligence_cached(config_with_keys, cache, project_context):
    """Cached result returned without API call."""
    cache_key = "test-saas:competitors:exa=True"
    cache.set("competitor_intel", cache_key, "cached intel", ttl_seconds=3600)

    result = await run_competitor_intelligence(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
    )

    assert result == "cached intel"
    assert len(respx.calls) == 0
