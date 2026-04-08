"""Dzen publishing — via Telegram crosspost using @zen_sync_bot.

Dzen has no public API. Publishing works through a Telegram channel
connected to Dzen Studio via @zen_sync_bot. All posts from the
connected Telegram channel are automatically mirrored to Dzen.

The tool sends a message to the project's telegram_dzen_channel.
Title for Dzen = first sentence of the post (max 140 chars, Dzen requirement).
"""

from marketolog.core.config import MarketologConfig
from marketolog.modules.smm.telegram import run_telegram_post


async def run_dzen_publish(
    text: str,
    project_context: dict,
    *,
    config: MarketologConfig,
    image_url: str | None = None,
) -> str:
    """Publish to Dzen via Telegram crosspost channel.

    Args:
        text: Post text. First sentence becomes Dzen title (max 140 chars).
        project_context: Project context with social.telegram_dzen_channel.
        config: App configuration with Telegram bot token.
        image_url: Optional image URL.

    Returns:
        Success message or error/instructions.
    """
    dzen_channel = project_context.get("social", {}).get("telegram_dzen_channel", "")

    if not dzen_channel:
        return (
            "Канал Дзен не настроен.\n\n"
            "Для публикации в Дзен:\n"
            "1. Создайте Telegram-канал для кросспостинга\n"
            "2. Добавьте @zen_sync_bot администратором\n"
            "3. Настройте связку в Студии Дзен (Настройки → Кросспостинг → Telegram)\n"
            "4. Укажите канал в проекте: update_project('social.telegram_dzen_channel', '@your_dzen_channel')"
        )

    result = await run_telegram_post(
        channel=dzen_channel,
        text=text,
        config=config,
        image_url=image_url,
    )

    if "отправлен" in result.lower():
        return result.replace("Пост отправлен", "Пост отправлен в Дзен (через Telegram)")

    return result
