"""Tests for VK posting and stats tools."""

import httpx
import pytest
import respx

from marketolog.modules.smm import vk as vk_module
from marketolog.modules.smm.vk import run_vk_post, run_vk_stats

VK_API = "https://api.vk.com/method"


@pytest.fixture(autouse=True)
def _clear_group_cache():
    """Clear module-level group ID cache between tests."""
    vk_module._group_id_cache.clear()


def _mock_groups_get_by_id(group_name: str = "mysaas", group_id: int = 12345):
    """Helper: mock groups.getById for short name resolution."""
    respx.get(f"{VK_API}/groups.getById").mock(
        return_value=httpx.Response(200, json={
            "response": {"groups": [{"id": group_id, "screen_name": group_name}]}
        })
    )


@respx.mock
@pytest.mark.asyncio
async def test_vk_post(config_with_keys):
    """Post to VK group wall."""
    _mock_groups_get_by_id()
    respx.get(f"{VK_API}/wall.post").mock(
        return_value=httpx.Response(200, json={"response": {"post_id": 123}})
    )

    result = await run_vk_post(
        group="mysaas",
        text="Тестовый пост в VK",
        config=config_with_keys,
    )

    assert isinstance(result, str)
    assert "123" in result or "опубликован" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_vk_post_numeric_group(config_with_keys):
    """Numeric group ID skips groups.getById resolution."""
    respx.get(f"{VK_API}/wall.post").mock(
        return_value=httpx.Response(200, json={"response": {"post_id": 456}})
    )

    result = await run_vk_post(
        group="12345",
        text="Тест",
        config=config_with_keys,
    )

    assert "456" in result


@respx.mock
@pytest.mark.asyncio
async def test_vk_post_no_token(config_no_keys):
    """Without token — returns setup instructions."""
    result = await run_vk_post(
        group="test",
        text="test",
        config=config_no_keys,
    )

    assert "VK_API_TOKEN" in result


@respx.mock
@pytest.mark.asyncio
async def test_vk_stats(config_with_keys, cache):
    """Get VK community stats."""
    respx.get(f"{VK_API}/stats.get").mock(
        return_value=httpx.Response(200, json={
            "response": [
                {
                    "period_from": "2026-04-01",
                    "period_to": "2026-04-07",
                    "visitors": {"views": 5000, "visitors": 2000},
                    "reach": {"reach": 3000},
                }
            ]
        })
    )

    result = await run_vk_stats(
        group="mysaas",
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "5000" in result or "5,000" in result or "просмотр" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_vk_stats_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    result = await run_vk_stats(
        group="test",
        config=config_no_keys,
        cache=cache,
    )

    assert "VK_API_TOKEN" in result
