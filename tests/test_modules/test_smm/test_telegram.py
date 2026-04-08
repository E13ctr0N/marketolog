"""Tests for Telegram posting and stats tools."""

import httpx
import pytest
import respx

from marketolog.modules.smm.telegram import run_telegram_post, run_telegram_stats

TG_API = "https://api.telegram.org"


@respx.mock
@pytest.mark.asyncio
async def test_telegram_post(config_with_keys):
    """Post a message to Telegram channel."""
    respx.post(f"{TG_API}/bot123456:ABC-DEF-test-token/sendMessage").mock(
        return_value=httpx.Response(200, json={
            "ok": True,
            "result": {"message_id": 42, "chat": {"id": -1001234, "title": "Test"}}
        })
    )

    result = await run_telegram_post(
        channel="@mysaas_channel",
        text="Тестовый пост",
        config=config_with_keys,
    )

    assert isinstance(result, str)
    assert "42" in result or "отправлен" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_telegram_post_no_token(config_no_keys):
    """Without token — returns setup instructions."""
    result = await run_telegram_post(
        channel="@test",
        text="test",
        config=config_no_keys,
    )

    assert "TELEGRAM_BOT_TOKEN" in result


@respx.mock
@pytest.mark.asyncio
async def test_telegram_stats(config_with_keys, cache):
    """Get Telegram channel stats."""
    respx.get(f"{TG_API}/bot123456:ABC-DEF-test-token/getChatMemberCount").mock(
        return_value=httpx.Response(200, json={"ok": True, "result": 1500})
    )
    respx.get(f"{TG_API}/bot123456:ABC-DEF-test-token/getChat").mock(
        return_value=httpx.Response(200, json={
            "ok": True,
            "result": {"id": -1001234, "title": "MySaaS", "type": "channel"}
        })
    )

    result = await run_telegram_stats(
        channel="@mysaas_channel",
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "1500" in result or "1,500" in result


@respx.mock
@pytest.mark.asyncio
async def test_telegram_stats_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    result = await run_telegram_stats(
        channel="@test",
        config=config_no_keys,
        cache=cache,
    )

    assert "TELEGRAM_BOT_TOKEN" in result
