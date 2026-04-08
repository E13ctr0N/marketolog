"""VK API — post to community wall and get stats.

Uses direct httpx calls. VK API v5.199.
Changes since 27.08.2025: wall.post requires content (text/photo/video/link).
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

VK_API = "https://api.vk.com/method"
VK_VERSION = "5.199"

SETUP_INSTRUCTIONS = """\
VK API не настроен.

Для публикации в VK задайте переменную окружения:

    VK_API_TOKEN=<токен сообщества>

1. Откройте настройки сообщества → Работа с API → Создать ключ
2. Выберите права: управление стеной, статистика
3. Укажите токен в переменной
"""


async def run_vk_post(
    group: str,
    text: str,
    *,
    config: MarketologConfig,
    schedule_timestamp: int | None = None,
) -> str:
    """Post to VK community wall.

    Args:
        group: VK group short name or ID (without minus sign).
        text: Post text.
        config: App configuration with VK token.
        schedule_timestamp: Unix timestamp for scheduled post (VK native).

    Returns:
        Success message with post_id or error.
    """
    if not config.is_configured("vk_api_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.vk_api_token  # type: ignore[assignment]

    # Determine owner_id: if numeric, use -group_id; otherwise resolve
    if group.isdigit():
        owner_id = f"-{group}"
    else:
        owner_id = f"-{group}"  # VK accepts short name in some methods

    body: dict = {
        "access_token": token,
        "v": VK_VERSION,
        "owner_id": owner_id,
        "from_group": 1,
        "message": text,
    }

    if schedule_timestamp:
        body["publish_date"] = schedule_timestamp

    resp = await fetch_with_retry(f"{VK_API}/wall.post", method="POST", json=body)

    if resp.status_code != 200:
        return f"Ошибка VK API (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    if "error" in data:
        err = data["error"]
        return f"Ошибка VK: [{err.get('error_code')}] {err.get('error_msg', '')}"

    post_id = data.get("response", {}).get("post_id", "?")
    if schedule_timestamp:
        return f"Пост запланирован в VK (group: {group}, post_id: {post_id})"
    return f"Пост опубликован в VK (group: {group}, post_id: {post_id})"


async def run_vk_stats(
    group: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
    period: str = "7d",
) -> str:
    """Get VK community statistics.

    Args:
        group: VK group short name or ID.
        config: App configuration with VK token.
        cache: File cache.
        period: Period shorthand.

    Returns:
        Formatted stats report.
    """
    if not config.is_configured("vk_api_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.vk_api_token  # type: ignore[assignment]

    cached = cache.get("vk_stats", f"{group}:{period}")
    if cached is not None:
        return cached  # type: ignore[return-value]

    from datetime import date, timedelta
    today = date.today()
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 7)
    date_from = today - timedelta(days=days)

    body = {
        "access_token": token,
        "v": VK_VERSION,
        "group_id": group,
        "date_from": date_from.isoformat(),
        "date_to": today.isoformat(),
    }

    resp = await fetch_with_retry(f"{VK_API}/stats.get", method="POST", json=body)

    if resp.status_code != 200:
        return f"Ошибка VK API (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    if "error" in data:
        err = data["error"]
        return f"Ошибка VK: [{err.get('error_code')}] {err.get('error_msg', '')}"

    stats = data.get("response", [])
    report = _format_vk_stats(group, period, stats)

    cache.set("vk_stats", f"{group}:{period}", report, ttl_seconds=1800)
    return report


def _format_vk_stats(group: str, period: str, stats: list[dict]) -> str:
    lines = [f"## Статистика VK: {group} (период: {period})\n"]

    if not stats:
        lines.append("Нет данных за выбранный период.")
        return "\n".join(lines)

    total_views = 0
    total_visitors = 0
    total_reach = 0

    for entry in stats:
        visitors = entry.get("visitors", {})
        total_views += visitors.get("views", 0)
        total_visitors += visitors.get("visitors", 0)
        reach = entry.get("reach", {})
        total_reach += reach.get("reach", 0)

    lines.append(f"- **Просмотров:** {total_views:,}")
    lines.append(f"- **Уникальных посетителей:** {total_visitors:,}")
    lines.append(f"- **Охват:** {total_reach:,}")

    return "\n".join(lines)
