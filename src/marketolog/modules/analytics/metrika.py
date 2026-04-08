"""Yandex Metrika API — reports and goals.

Uses Yandex Metrika Stat API v1 for traffic data and Management API for goals.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.formatting import format_tabular
from marketolog.utils.http import fetch_with_retry

BASE_URL = "https://api-metrika.yandex.net"
CACHE_TTL = 1800  # 30 min

SETUP_INSTRUCTIONS = """\
Яндекс.Метрика не настроена.

Для использования задайте переменные окружения:

    YANDEX_OAUTH_TOKEN=<ваш OAuth-токен>
    YANDEX_METRIKA_COUNTER=<ID счётчика>

Получить токен: https://oauth.yandex.ru/
ID счётчика: https://metrika.yandex.ru/ → Настройки → Код счётчика
"""


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"OAuth {token}"}


async def run_metrika_report(
    counter_id: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
    period: str = "7d",
    metrics: str | None = None,
) -> str:
    if not config.is_configured("yandex_oauth_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.yandex_oauth_token  # type: ignore[assignment]

    cache_key = f"{counter_id}:{period}:{metrics or 'default'}"
    cached = cache.get("metrika_report", cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    date1, date2 = _period_to_dates(period)
    default_metrics = "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:avgVisitDurationSeconds"

    params = {
        "id": counter_id,
        "date1": date1,
        "date2": date2,
        "metrics": metrics or default_metrics,
        "dimensions": "ym:s:lastTrafficSource",
        "sort": "-ym:s:visits",
        "limit": 20,
    }

    resp = await fetch_with_retry(
        f"{BASE_URL}/stat/v1/data",
        headers=_auth_headers(token),
        params=params,
    )

    if resp.status_code != 200:
        return f"Ошибка Метрики (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    report = _format_stat_report(counter_id, period, data)

    cache.set("metrika_report", cache_key, report, ttl_seconds=CACHE_TTL)
    return report


async def run_metrika_goals(
    counter_id: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    if not config.is_configured("yandex_oauth_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.yandex_oauth_token  # type: ignore[assignment]

    cached = cache.get("metrika_goals", counter_id)
    if cached is not None:
        return cached  # type: ignore[return-value]

    resp = await fetch_with_retry(
        f"{BASE_URL}/management/v1/counter/{counter_id}/goals",
        headers=_auth_headers(token),
    )

    if resp.status_code != 200:
        return f"Ошибка при получении целей (HTTP {resp.status_code}): {resp.text[:200]}"

    goals = resp.json().get("goals", [])
    report = _format_goals(counter_id, goals)

    cache.set("metrika_goals", counter_id, report, ttl_seconds=CACHE_TTL)
    return report


def _period_to_dates(period: str) -> tuple[str, str]:
    """Convert period shorthand to (date1, date2) for Metrika API."""
    from datetime import date, timedelta
    today = date.today()
    days_map = {"today": 0, "7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 7)
    start = today - timedelta(days=max(days, 1))
    return start.isoformat(), today.isoformat()


def _format_stat_report(counter_id: str, period: str, data: dict) -> str:
    lines = [f"## Отчёт Яндекс.Метрика (счётчик {counter_id}, период: {period})\n"]

    totals = data.get("totals", [])
    if totals:
        labels = ["Визиты", "Посетители", "Отказы (%)", "Ср. длительность (сек)"]
        lines.append("### Итого")
        for label, val in zip(labels, totals):
            formatted = f"{val:,.0f}" if isinstance(val, (int, float)) and label != "Отказы (%)" else str(val)
            lines.append(f"- **{label}:** {formatted}")
        lines.append("")

    rows = data.get("data", [])
    if rows:
        lines.append("### По источникам трафика")
        table_data = []
        for row in rows:
            dims = row.get("dimensions", [])
            mets = row.get("metrics", [])
            source_name = dims[0].get("name", "—") if dims else "—"
            table_data.append({
                "Источник": source_name,
                "Визиты": int(mets[0]) if len(mets) > 0 else 0,
                "Посетители": int(mets[1]) if len(mets) > 1 else 0,
                "Отказы (%)": round(mets[2], 1) if len(mets) > 2 else 0,
                "Ср. длит. (сек)": round(mets[3], 1) if len(mets) > 3 else 0,
            })
        lines.append(format_tabular(table_data))

    return "\n".join(lines)


def _format_goals(counter_id: str, goals: list[dict]) -> str:
    lines = [f"## Цели Яндекс.Метрика (счётчик {counter_id})\n"]

    if not goals:
        lines.append("Цели не настроены.")
        return "\n".join(lines)

    table_data = [
        {
            "ID": g.get("id", "—"),
            "Название": g.get("name", "—"),
            "Тип": g.get("type", "—"),
        }
        for g in goals
    ]
    lines.append(format_tabular(table_data))
    return "\n".join(lines)
