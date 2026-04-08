"""Tests for Dzen publishing tool (via Telegram crosspost)."""

import httpx
import pytest
import respx

from marketolog.modules.smm.dzen import run_dzen_publish

TG_API = "https://api.telegram.org"


@respx.mock
@pytest.mark.asyncio
async def test_dzen_publish(config_with_keys, project_context):
    """Publish to Dzen via Telegram dzen channel."""
    respx.post(f"{TG_API}/bot123456:ABC-DEF-test-token/sendMessage").mock(
        return_value=httpx.Response(200, json={
            "ok": True,
            "result": {"message_id": 99, "chat": {"id": -1001234}}
        })
    )

    result = await run_dzen_publish(
        text="Как выбрать таск-трекер. Подробный обзор лучших решений для малых команд.",
        project_context=project_context,
        config=config_with_keys,
    )

    assert isinstance(result, str)
    assert "дзен" in result.lower() or "99" in result


@respx.mock
@pytest.mark.asyncio
async def test_dzen_publish_no_channel(config_with_keys):
    """No dzen channel configured — returns instructions."""
    context = {"social": {}}

    result = await run_dzen_publish(
        text="Test",
        project_context=context,
        config=config_with_keys,
    )

    assert "telegram_dzen_channel" in result.lower() or "дзен" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_dzen_publish_no_token(config_no_keys, project_context):
    """Without Telegram token — returns setup instructions."""
    result = await run_dzen_publish(
        text="Test",
        project_context=project_context,
        config=config_no_keys,
    )

    assert "TELEGRAM_BOT_TOKEN" in result
