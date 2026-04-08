"""Weekly digest — aggregated weekly performance report."""

from datetime import date, timedelta

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

METRIKA_BASE = "https://api-metrika.yandex.net"
CACHE_NS = "weekly_digest"
CACHE_TTL = 3600

SETUP_INSTRUCTIONS = """\
Яндекс.Метрика не настроена.

Для еженедельного дайджеста задайте переменные окружения:

    YANDEX_OAUTH_TOKEN=<ваш OAuth-токен>
    YANDEX_METRIKA_COUNTER=<ID счётчика>
"""


async def run_weekly_digest(
    counter_id: str,
    project_name: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    if not config.is_configured("yandex_oauth_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.yandex_oauth_token

    week_num = date.today().isocalendar()[1]
    cache_key = f"{counter_id}:{week_num}"
    cached = cache.get(CACHE_NS, cache_key)
    if cached is not None:
        return cached

    from marketolog.modules.analytics.metrika import _auth_headers

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = today

    resp = await fetch_with_retry(
        f"{METRIKA_BASE}/stat/v1/data",
        headers=_auth_headers(token),
        params={
            "id": counter_id,
            "date1": week_start.isoformat(),
            "date2": week_end.isoformat(),
            "metrics": "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:avgVisitDurationSeconds",
            "dimensions": "ym:s:lastTrafficSource",
            "sort": "-ym:s:visits",
            "limit": 10,
        },
    )

    if resp.status_code != 200:
        return f"Ошибка Метрики (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    report = _format_digest(project_name, week_start, week_end, data)

    cache.set(CACHE_NS, cache_key, report, ttl_seconds=CACHE_TTL)
    return report


def _format_digest(project_name: str, week_start: date, week_end: date, data: dict) -> str:
    lines = [
        f"## Недельный дайджест \"{project_name}\"",
        f"Период: {week_start.strftime('%d.%m')} — {week_end.strftime('%d.%m.%Y')}\n",
    ]

    totals = data.get("totals", [])
    if totals:
        visits = int(totals[0]) if len(totals) > 0 else 0
        users = int(totals[1]) if len(totals) > 1 else 0
        bounce = totals[2] if len(totals) > 2 else 0
        avg_dur = totals[3] if len(totals) > 3 else 0

        lines.append("### Ключевые метрики")
        lines.append(f"- **Визиты:** {visits:,}")
        lines.append(f"- **Посетители:** {users:,}")
        lines.append(f"- **Отказы:** {bounce:.1f}%")
        mins = int(avg_dur) // 60
        secs = int(avg_dur) % 60
        lines.append(f"- **Ср. время на сайте:** {mins}:{secs:02d}")
        lines.append("")

    rows = data.get("data", [])
    if rows:
        total_visits = int(totals[0]) if totals else 1
        lines.append("### Источники трафика")
        for row in rows:
            dims = row.get("dimensions", [])
            mets = row.get("metrics", [0])
            source = dims[0].get("name", "—") if dims else "—"
            visits = int(mets[0]) if mets else 0
            pct = (visits / total_visits * 100) if total_visits > 0 else 0
            lines.append(f"- {source}: {visits:,} ({pct:.0f}%)")

    return "\n".join(lines)
