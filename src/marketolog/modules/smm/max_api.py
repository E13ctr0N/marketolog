"""MAX Bot API — post messages and get channel stats.

Uses direct httpx calls to MAX platform API.
Base URL: https://platform-api.max.ru
Auth: Authorization header with bot token.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

MAX_API = "https://platform-api.max.ru"

SETUP_INSTRUCTIONS = """\
MAX Bot не настроен.

Для публикации в MAX задайте переменную окружения:

    MAX_BOT_TOKEN=<токен бота>

1. Зайдите на dev.max.ru → Чат-боты → Интеграция
2. Получите токен бота
3. Добавьте бота администратором канала
"""


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": token}


async def run_max_post(
    channel: str,
    text: str,
    *,
    config: MarketologConfig,
    image_url: str | None = None,
) -> str:
    """Send a message to a MAX channel.

    Args:
        channel: Channel ID or @username.
        text: Message text (Markdown supported, up to 4000 chars).
        config: App configuration with MAX bot token.
        image_url: Optional image URL.

    Returns:
        Success message or error.
    """
    if not config.is_configured("max_bot_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.max_bot_token  # type: ignore[assignment]

    body: dict = {
        "chat_id": channel,
        "text": text,
        "format": "markdown",
    }

    resp = await fetch_with_retry(
        f"{MAX_API}/messages",
        method="POST",
        headers=_auth_headers(token),
        json=body,
    )

    if resp.status_code != 200:
        return f"Ошибка MAX API (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    msg_id = data.get("message", {}).get("body", {}).get("mid", "?")
    return f"Пост отправлен в MAX {channel} (mid: {msg_id})"


async def run_max_stats(
    channel: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    """Get MAX channel statistics.

    Args:
        channel: Channel ID or @username.
        config: App configuration.
        cache: File cache.

    Returns:
        Formatted channel stats.
    """
    if not config.is_configured("max_bot_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.max_bot_token  # type: ignore[assignment]

    cached = cache.get("max_stats", channel)
    if cached is not None:
        return cached  # type: ignore[return-value]

    resp = await fetch_with_retry(
        f"{MAX_API}/chats/{channel}",
        headers=_auth_headers(token),
    )

    if resp.status_code != 200:
        return f"Ошибка MAX API (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()

    lines = [f"## Статистика MAX: {channel}\n"]
    lines.append(f"- **Название:** {data.get('title', '—')}")
    lines.append(f"- **Тип:** {data.get('type', '—')}")
    lines.append(f"- **Участников:** {data.get('participants_count', 0):,}")

    report = "\n".join(lines)
    cache.set("max_stats", channel, report, ttl_seconds=1800)
    return report
