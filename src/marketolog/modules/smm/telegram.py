"""Telegram Bot API — post messages and get channel stats.

Uses direct httpx calls to Telegram Bot API.
Bot must be admin of the channel with posting rights.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

TG_API = "https://api.telegram.org"

SETUP_INSTRUCTIONS = """\
Telegram Bot не настроен.

Для публикации в Telegram задайте переменную окружения:

    TELEGRAM_BOT_TOKEN=<токен бота>

1. Создайте бота через @BotFather
2. Добавьте бота администратором канала с правом публикации
3. Укажите токен в переменной
"""


async def run_telegram_post(
    channel: str,
    text: str,
    *,
    config: MarketologConfig,
    image_url: str | None = None,
) -> str:
    """Send a message to a Telegram channel.

    Args:
        channel: Channel username (@channel) or numeric chat_id.
        text: Message text (Markdown supported).
        config: App configuration with bot token.
        image_url: Optional image URL to attach.

    Returns:
        Success message with message_id or error.
    """
    if not config.is_configured("telegram_bot_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.telegram_bot_token  # type: ignore[assignment]

    if image_url:
        endpoint = f"{TG_API}/bot{token}/sendPhoto"
        body = {
            "chat_id": channel,
            "photo": image_url,
            "caption": text,
            "parse_mode": "Markdown",
        }
    else:
        endpoint = f"{TG_API}/bot{token}/sendMessage"
        body = {
            "chat_id": channel,
            "text": text,
            "parse_mode": "Markdown",
        }

    resp = await fetch_with_retry(endpoint, method="POST", json=body)

    if resp.status_code != 200:
        return f"Ошибка Telegram API (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    if not data.get("ok"):
        return f"Ошибка Telegram: {data.get('description', 'unknown error')}"

    msg_id = data.get("result", {}).get("message_id", "?")
    return f"Пост отправлен в {channel} (message_id: {msg_id})"


async def run_telegram_stats(
    channel: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    """Get Telegram channel statistics.

    Args:
        channel: Channel username (@channel).
        config: App configuration with bot token.
        cache: File cache instance.

    Returns:
        Formatted channel stats.
    """
    if not config.is_configured("telegram_bot_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.telegram_bot_token  # type: ignore[assignment]

    cached = cache.get("telegram_stats", channel)
    if cached is not None:
        return cached  # type: ignore[return-value]

    # Get chat info
    chat_resp = await fetch_with_retry(
        f"{TG_API}/bot{token}/getChat",
        params={"chat_id": channel},
    )

    # Get member count
    count_resp = await fetch_with_retry(
        f"{TG_API}/bot{token}/getChatMemberCount",
        params={"chat_id": channel},
    )

    lines = [f"## Статистика Telegram: {channel}\n"]

    if chat_resp.status_code == 200:
        chat_data = chat_resp.json().get("result", {})
        lines.append(f"- **Название:** {chat_data.get('title', '—')}")
        lines.append(f"- **Тип:** {chat_data.get('type', '—')}")

    if count_resp.status_code == 200:
        count = count_resp.json().get("result", 0)
        lines.append(f"- **Подписчиков:** {count:,}")

    report = "\n".join(lines)
    cache.set("telegram_stats", channel, report, ttl_seconds=1800)
    return report
