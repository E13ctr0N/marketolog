"""Tests for brand_health tool."""

import httpx
import pytest
import respx

from marketolog.modules.strategy.brand import run_brand_health

EXA_API = "https://api.exa.ai/search"


@respx.mock
@pytest.mark.asyncio
async def test_brand_health_with_exa(config_with_keys, cache, project_context):
    """Brand monitoring via Exa API."""
    respx.post(EXA_API).mock(
        return_value=httpx.Response(200, json={
            "results": [
                {"title": "my-saas review", "url": "https://review.com/1"},
                {"title": "Отзывы my-saas", "url": "https://review.com/2"},
            ]
        })
    )

    result = await run_brand_health(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "бренд" in result.lower() or "упоминан" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_brand_health_no_exa(config_no_keys, cache, project_context):
    """Without Exa — returns guidance."""
    result = await run_brand_health(
        project_context=project_context,
        config=config_no_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "exa" in result.lower() or "настройте" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_brand_health_cached(config_with_keys, cache, project_context):
    """Cached result returned."""
    cache.set("brand_health", "test-saas", "cached brand", ttl_seconds=3600)

    result = await run_brand_health(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
    )

    assert result == "cached brand"
    assert len(respx.calls) == 0
