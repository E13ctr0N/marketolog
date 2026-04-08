"""Tests for MAX posting and stats tools."""

import httpx
import pytest
import respx

from marketolog.modules.smm.max_api import run_max_post, run_max_stats

MAX_API = "https://platform-api.max.ru"


@respx.mock
@pytest.mark.asyncio
async def test_max_post(config_with_keys):
    """Post to MAX channel."""
    respx.post(f"{MAX_API}/messages").mock(
        return_value=httpx.Response(200, json={
            "message": {"body": {"mid": "msg-123"}}
        })
    )

    result = await run_max_post(
        channel="@mysaas_max",
        text="Тестовый пост в MAX",
        config=config_with_keys,
    )

    assert isinstance(result, str)
    assert "отправлен" in result.lower() or "msg-123" in result


@respx.mock
@pytest.mark.asyncio
async def test_max_post_no_token(config_no_keys):
    """Without token — returns setup instructions."""
    result = await run_max_post(
        channel="@test",
        text="test",
        config=config_no_keys,
    )

    assert "MAX_BOT_TOKEN" in result


@respx.mock
@pytest.mark.asyncio
async def test_max_stats(config_with_keys, cache):
    """Get MAX channel info."""
    respx.get(f"{MAX_API}/chats/@mysaas_max").mock(
        return_value=httpx.Response(200, json={
            "title": "MySaaS MAX",
            "participants_count": 500,
            "type": "channel",
        })
    )

    result = await run_max_stats(
        channel="@mysaas_max",
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "500" in result


@respx.mock
@pytest.mark.asyncio
async def test_max_stats_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    result = await run_max_stats(
        channel="@test",
        config=config_no_keys,
        cache=cache,
    )

    assert "MAX_BOT_TOKEN" in result
