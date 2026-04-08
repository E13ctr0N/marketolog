"""Traffic sources breakdown — Yandex Metrika source analysis."""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

METRIKA_BASE = "https://api-metrika.yandex.net"
CACHE_NS = "traffic_sources"
CACHE_TTL = 1800

SETUP_INSTRUCTIONS = """\
Яндекс.Метрика не настроена.

Для анализа источников трафика задайте переменные окружения:

    YANDEX_OAUTH_TOKEN=<ваш OAuth-токен>
    YANDEX_METRIKA_COUNTER=<ID счётчика>
"""


async def run_traffic_sources(
    counter_id: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
    period: str = "7d",
) -> str:
    if not config.is_configured("yandex_oauth_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.yandex_oauth_token

    cache_key = f"{counter_id}:{period}"
    cached = cache.get(CACHE_NS, cache_key)
    if cached is not None:
        return cached

    from marketolog.modules.analytics.metrika import _period_to_dates, _auth_headers

    date1, date2 = _period_to_dates(period)

    resp = await fetch_with_retry(
        f"{METRIKA_BASE}/stat/v1/data",
        headers=_auth_headers(token),
        params={
            "id": counter_id,
            "date1": date1,
            "date2": date2,
            "metrics": "ym:s:visits",
            "dimensions": "ym:s:lastTrafficSource",
            "sort": "-ym:s:visits",
            "limit": 20,
        },
    )

    if resp.status_code != 200:
        return f"Ошибка Метрики (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    report = _format_sources(counter_id, period, data)

    cache.set(CACHE_NS, cache_key, report, ttl_seconds=CACHE_TTL)
    return report


def _format_sources(counter_id: str, period: str, data: dict) -> str:
    lines = [f"## Источники трафика (счётчик {counter_id}, период: {period})\n"]

    rows = data.get("data", [])
    totals = data.get("totals", [0])
    total_visits = totals[0] if totals else 0

    if not rows:
        lines.append("Нет данных за выбранный период.")
        return "\n".join(lines)

    lines.append(f"**Всего визитов:** {int(total_visits):,}\n")

    source_names = {
        "organic": "Поисковые системы",
        "direct": "Прямые заходы",
        "social": "Социальные сети",
        "referral": "Ссылки с сайтов",
        "ad": "Реклама",
        "internal": "Внутренние переходы",
        "email": "Email-рассылки",
        "messenger": "Мессенджеры",
    }

    for row in rows:
        dims = row.get("dimensions", [])
        mets = row.get("metrics", [0])
        source_key = dims[0].get("name", "—") if dims else "—"
        visits = int(mets[0]) if mets else 0
        pct = (visits / total_visits * 100) if total_visits > 0 else 0
        label = source_names.get(source_key, source_key)
        bar = "█" * int(pct / 5) if pct >= 5 else "▏"
        lines.append(f"- **{label}** ({source_key}): {visits:,} ({pct:.1f}%) {bar}")

    return "\n".join(lines)
