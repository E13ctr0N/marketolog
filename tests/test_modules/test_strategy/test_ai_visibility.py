"""Tests for ai_visibility tool."""

import httpx
import pytest
import respx

from marketolog.modules.strategy.ai_visibility import run_ai_visibility

EXA_API = "https://api.exa.ai/search"


@respx.mock
@pytest.mark.asyncio
async def test_ai_visibility_with_exa(config_with_keys, cache, project_context):
    """AI visibility check via Exa API."""
    respx.post(EXA_API).mock(
        return_value=httpx.Response(200, json={
            "results": [
                {"title": "ChatGPT recommends my-saas", "url": "https://ai.com/1"},
                {"title": "Claude mentions my-saas", "url": "https://ai.com/2"},
            ]
        })
    )

    result = await run_ai_visibility(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "AI" in result or "ИИ" in result


@respx.mock
@pytest.mark.asyncio
async def test_ai_visibility_custom_brand(config_with_keys, cache, project_context):
    """Override brand_name parameter."""
    respx.post(EXA_API).mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    result = await run_ai_visibility(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
        brand_name="CustomBrand",
    )

    assert isinstance(result, str)
    assert "CustomBrand" in result


@respx.mock
@pytest.mark.asyncio
async def test_ai_visibility_no_exa(config_no_keys, cache, project_context):
    """Without Exa — returns setup guidance."""
    result = await run_ai_visibility(
        project_context=project_context,
        config=config_no_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "exa" in result.lower() or "настройте" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_ai_visibility_cached(config_with_keys, cache, project_context):
    """Cached result returned."""
    cache.set("ai_visibility", "test-saas", "cached ai viz", ttl_seconds=3600)

    result = await run_ai_visibility(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
    )

    assert result == "cached ai viz"
    assert len(respx.calls) == 0
