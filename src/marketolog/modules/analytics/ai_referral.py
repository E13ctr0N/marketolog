"""AI referral traffic analysis — identifies visits from AI search engines."""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

METRIKA_BASE = "https://api-metrika.yandex.net"
CACHE_NS = "ai_referral"
CACHE_TTL = 1800

SETUP_INSTRUCTIONS = """\
Яндекс.Метрика не настроена.

Для отчёта по AI-трафику задайте переменные окружения:

    YANDEX_OAUTH_TOKEN=<ваш OAuth-токен>
    YANDEX_METRIKA_COUNTER=<ID счётчика>
"""

AI_DOMAINS: dict[str, str] = {
    "chat.openai.com": "ChatGPT",
    "chatgpt.com": "ChatGPT",
    "perplexity.ai": "Perplexity",
    "claude.ai": "Claude",
    "copilot.microsoft.com": "Microsoft Copilot",
    "you.com": "You.com",
    "phind.com": "Phind",
    "bard.google.com": "Google Bard",
    "gemini.google.com": "Google Gemini",
    "labs.google.com": "Google AI (Labs)",
}


async def run_ai_referral_report(
    counter_id: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
    period: str = "30d",
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
            "metrics": "ym:s:visits,ym:s:users",
            "dimensions": "ym:s:refererDomain",
            "sort": "-ym:s:visits",
            "limit": 200,
        },
    )

    if resp.status_code != 200:
        return f"Ошибка Метрики (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    report = _format_ai_report(counter_id, period, data)

    cache.set(CACHE_NS, cache_key, report, ttl_seconds=CACHE_TTL)
    return report


def _format_ai_report(counter_id: str, period: str, data: dict) -> str:
    lines = [f"## AI-трафик (счётчик {counter_id}, период: {period})\n"]

    rows = data.get("data", [])
    totals = data.get("totals", [0, 0])
    total_visits = totals[0] if totals else 0

    ai_rows: list[dict] = []
    for row in rows:
        dims = row.get("dimensions", [])
        domain = dims[0].get("name", "") if dims else ""
        ai_name = _match_ai_domain(domain)
        if ai_name:
            mets = row.get("metrics", [0, 0])
            ai_rows.append({
                "domain": domain,
                "name": ai_name,
                "visits": int(mets[0]) if mets else 0,
                "users": int(mets[1]) if len(mets) > 1 else 0,
            })

    if not ai_rows:
        lines.append("AI-трафик не обнаружен за выбранный период.\n")
        lines.append("Это нормально — AI-поисковики пока дают мало прямого трафика.")
        lines.append("Рекомендации по улучшению видимости для AI:")
        lines.append("- Проверьте `ai_seo_check` для анализа готовности сайта")
        lines.append("- Добавьте файл `llms.txt` на сайт")
        lines.append("- Структурируйте контент с JSON-LD schema")
        return "\n".join(lines)

    total_ai = sum(r["visits"] for r in ai_rows)
    ai_share = (total_ai / total_visits * 100) if total_visits > 0 else 0

    lines.append("### Сводка")
    lines.append(f"- **AI-визиты:** {total_ai:,} из {int(total_visits):,} ({ai_share:.1f}%)")
    lines.append("")

    lines.append("### По источникам")
    for r in sorted(ai_rows, key=lambda x: x["visits"], reverse=True):
        pct = (r["visits"] / total_visits * 100) if total_visits > 0 else 0
        lines.append(f"- **{r['name']}** ({r['domain']}): {r['visits']:,} визитов, {r['users']:,} уник. ({pct:.2f}%)")

    return "\n".join(lines)


def _match_ai_domain(domain: str) -> str | None:
    domain_lower = domain.lower()
    for ai_domain, ai_name in AI_DOMAINS.items():
        if ai_domain in domain_lower:
            return ai_name
    return None
