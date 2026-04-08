"""Funnel analysis — goal conversion by traffic source via Yandex Metrika."""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.formatting import format_tabular
from marketolog.utils.http import fetch_with_retry

METRIKA_BASE = "https://api-metrika.yandex.net"
CACHE_NS = "funnel_analysis"
CACHE_TTL = 1800

SETUP_INSTRUCTIONS = """\
Яндекс.Метрика не настроена.

Для анализа воронки задайте переменные окружения:

    YANDEX_OAUTH_TOKEN=<ваш OAuth-токен>
    YANDEX_METRIKA_COUNTER=<ID счётчика>
"""


async def run_funnel_analysis(
    counter_id: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
    goal: str | None = None,
    period: str = "30d",
) -> str:
    if not config.is_configured("yandex_oauth_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.yandex_oauth_token

    cache_key = f"{counter_id}:{goal or 'first'}:{period}"
    cached = cache.get(CACHE_NS, cache_key)
    if cached is not None:
        return cached

    from marketolog.modules.analytics.metrika import _period_to_dates, _auth_headers

    # Step 1: get goals to find goal ID
    goals_resp = await fetch_with_retry(
        f"{METRIKA_BASE}/management/v1/counter/{counter_id}/goals",
        headers=_auth_headers(token),
    )
    if goals_resp.status_code != 200:
        return f"Ошибка при получении целей (HTTP {goals_resp.status_code})"

    goals = goals_resp.json().get("goals", [])
    if not goals:
        return "Цели не настроены в Метрике. Создайте хотя бы одну цель для анализа воронки."

    # Find target goal
    target_goal = goals[0]
    if goal:
        for g in goals:
            if g.get("name", "").lower() == goal.lower():
                target_goal = g
                break

    goal_id = target_goal["id"]
    goal_name = target_goal.get("name", f"Goal {goal_id}")

    # Step 2: fetch funnel data
    date1, date2 = _period_to_dates(period)

    metrics = (
        f"ym:s:visits,"
        f"ym:s:goal{goal_id}reaches,"
        f"ym:s:goal{goal_id}conversionRate,"
        f"ym:s:goal{goal_id}revenue,"
        f"ym:s:bounceRate"
    )

    resp = await fetch_with_retry(
        f"{METRIKA_BASE}/stat/v1/data",
        headers=_auth_headers(token),
        params={
            "id": counter_id,
            "date1": date1,
            "date2": date2,
            "metrics": metrics,
            "dimensions": "ym:s:lastTrafficSource",
            "sort": f"-ym:s:goal{goal_id}reaches",
            "limit": 20,
        },
    )

    if resp.status_code != 200:
        return f"Ошибка Метрики (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    report = _format_funnel(counter_id, goal_name, period, data)

    cache.set(CACHE_NS, cache_key, report, ttl_seconds=CACHE_TTL)
    return report


def _format_funnel(counter_id: str, goal_name: str, period: str, data: dict) -> str:
    lines = [f"## Анализ воронки: {goal_name} (период: {period})\n"]

    totals = data.get("totals", [])
    if totals and len(totals) >= 3:
        lines.append("### Сводка")
        lines.append(f"- **Визиты:** {int(totals[0]):,}")
        lines.append(f"- **Достижения цели:** {int(totals[1]):,}")
        lines.append(f"- **Конверсия:** {totals[2]:.1f}%")
        if len(totals) >= 5:
            lines.append(f"- **Отказы:** {totals[4]:.1f}%")
        lines.append("")

    rows = data.get("data", [])
    if rows:
        lines.append("### По источникам (откуда → конверсия)")
        table_data = []
        for row in rows:
            dims = row.get("dimensions", [])
            mets = row.get("metrics", [])
            source = dims[0].get("name", "—") if dims else "—"
            table_data.append({
                "Источник": source,
                "Визиты": int(mets[0]) if len(mets) > 0 else 0,
                "Достижения": int(mets[1]) if len(mets) > 1 else 0,
                "Конверсия (%)": round(mets[2], 1) if len(mets) > 2 else 0,
                "Отказы (%)": round(mets[4], 1) if len(mets) > 4 else 0,
            })
        lines.append(format_tabular(table_data))

    return "\n".join(lines)
