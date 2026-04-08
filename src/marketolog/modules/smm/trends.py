"""Trend research — discover trending topics via Exa API.

Uses Exa semantic search to find recent trending content.
Falls back to general topic suggestions when Exa is not configured.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

EXA_API = "https://api.exa.ai/search"
CACHE_NS = "trends"
CACHE_TTL = 7200  # 2 hours


async def run_trend_research(
    topic: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
    platform: str | None = None,
) -> str:
    """Research trending topics.

    Args:
        topic: Topic or niche to research.
        config: App configuration (Exa API key optional).
        cache: File cache.
        platform: Optional platform filter.

    Returns:
        Formatted list of trending topics/content.
    """
    cached = cache.get(CACHE_NS, topic)
    if cached is not None:
        return cached  # type: ignore[return-value]

    if config.is_configured("exa_api_key"):
        report = await _search_exa(topic, config, platform)
    else:
        report = _fallback_suggestions(topic, platform)

    cache.set(CACHE_NS, topic, report, ttl_seconds=CACHE_TTL)
    return report


async def _search_exa(topic: str, config: MarketologConfig, platform: str | None) -> str:
    """Search Exa for trending content."""
    token: str = config.exa_api_key  # type: ignore[assignment]

    query = f"тренды {topic} 2026"
    if platform:
        query += f" {platform}"

    body = {
        "query": query,
        "numResults": 10,
        "type": "auto",
    }

    resp = await fetch_with_retry(
        EXA_API,
        method="POST",
        headers={
            "x-api-key": token,
            "Content-Type": "application/json",
        },
        json=body,
    )

    if resp.status_code != 200:
        return _fallback_suggestions(topic, platform)

    data = resp.json()
    results = data.get("results", [])

    if not results:
        return _fallback_suggestions(topic, platform)

    lines = [f"## Тренды: {topic}\n"]
    lines.append(f"Найдено {len(results)} актуальных материалов:\n")

    for i, item in enumerate(results, 1):
        title = item.get("title", "Без заголовка")
        url = item.get("url", "")
        lines.append(f"{i}. **{title}**")
        if url:
            lines.append(f"   {url}")

    lines.append("\n### Рекомендации")
    lines.append("Используйте эти тренды как основу для контент-плана.")
    lines.append("Адаптируйте под tone of voice проекта и целевую аудиторию.")

    return "\n".join(lines)


def _fallback_suggestions(topic: str, platform: str | None) -> str:
    """Return basic content ideas when Exa is not available."""
    lines = [
        f"## Идеи контента: {topic}\n",
        "Exa API не настроен — предлагаю универсальные форматы:\n",
        f"1. **Обзор рынка {topic}** — что нового, тренды, прогнозы",
        f"2. **Кейс / история успеха** — как решали проблему в нише {topic}",
        f"3. **Чек-лист / гайд** — практические шаги для аудитории",
        f"4. **Сравнение инструментов** — помогает в принятии решений",
        f"5. **Ответы на частые вопросы** — FAQ формат, хорошо для SEO",
        f"6. **Экспертное мнение** — интервью или комментарий",
        f"7. **Разбор ошибок** — что не делать в {topic}",
        "",
        "Для более точных трендов настройте Exa API:",
        "    EXA_API_KEY=<ваш ключ>",
        "Получить: https://exa.ai",
    ]

    return "\n".join(lines)
