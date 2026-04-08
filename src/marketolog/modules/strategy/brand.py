"""Brand health — mentions, reviews, sentiment monitoring.

Uses Exa API to search for brand mentions across the web.
Falls back to a manual checklist when Exa is not configured.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

EXA_API = "https://api.exa.ai/search"
CACHE_NS = "brand_health"
CACHE_TTL = 3600  # 1 hour


async def run_brand_health(
    project_context: dict,
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    """Monitor brand health: mentions, reviews, dynamics.

    Args:
        project_context: Full project context.
        config: App configuration (Exa API key optional).
        cache: File cache.

    Returns:
        Brand health report.
    """
    project_name = project_context.get("name", "project")

    cached = cache.get(CACHE_NS, project_name)
    if cached is not None:
        return cached

    if config.is_configured("exa_api_key"):
        report = await _search_brand_mentions(project_context, config)
    else:
        report = _fallback_checklist(project_context)

    cache.set(CACHE_NS, project_name, report, ttl_seconds=CACHE_TTL)
    return report


async def _search_brand_mentions(project_context: dict, config: MarketologConfig) -> str:
    """Search Exa for brand mentions."""
    token: str = config.exa_api_key
    name = project_context.get("name", "")
    url = project_context.get("url", "")
    niche = project_context.get("niche", "")

    lines = [
        "## Здоровье бренда",
        f"**Бренд:** {name}",
        f"**URL:** {url}",
        "",
    ]

    queries = [
        f'"{name}" отзывы {niche}',
        f'"{name}" обзор',
    ]

    all_results = []
    for query in queries:
        body = {
            "query": query,
            "numResults": 5,
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

        if resp.status_code == 200:
            results = resp.json().get("results", [])
            all_results.extend(results)

    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique_results = []
    for item in all_results:
        item_url = item.get("url", "")
        if item_url not in seen_urls:
            seen_urls.add(item_url)
            unique_results.append(item)

    lines.append(f"### Упоминания ({len(unique_results)} найдено)")
    lines.append("")

    if unique_results:
        for i, item in enumerate(unique_results, 1):
            title = item.get("title", "Без заголовка")
            item_url = item.get("url", "")
            lines.append(f"{i}. **{title}**")
            if item_url:
                lines.append(f"   {item_url}")
    else:
        lines.append("Упоминаний не найдено. Это может означать:")
        lines.append("- Бренд ещё не набрал достаточно упоминаний")
        lines.append("- Название бренда слишком общее")
    lines.append("")

    lines.append("### Рекомендации")
    lines.append("- Используйте `ai_visibility` для проверки упоминаний в AI-поисковиках")
    lines.append("- Отслеживайте динамику: запускайте `brand_health` еженедельно")
    lines.append("- Работайте с отзывами: отвечайте на негатив, поощряйте позитив")

    return "\n".join(lines)


def _fallback_checklist(project_context: dict) -> str:
    """Brand health checklist without Exa."""
    name = project_context.get("name", "")

    lines = [
        "## Здоровье бренда",
        f"**Бренд:** {name}",
        "",
        "### Ручной чек-лист",
        "",
        "Для автоматического мониторинга настройте Exa API:",
        "    EXA_API_KEY=<ваш ключ>",
        "Получить: https://exa.ai",
        "",
        "Пока API не настроен, проверьте вручную:",
        "",
        f'1. Поищите "{name}" в Яндексе — что на первой странице?',
        f'2. Поищите "{name} отзывы" — есть ли отзывы? Какой тон?',
        f'3. Проверьте упоминания в соцсетях: VK, Telegram',
        f'4. Проверьте рейтинги на отзовиках (если применимо)',
        f'5. Поищите "{name}" в ChatGPT / Perplexity — что отвечают AI?',
        "",
        "### Инструменты",
        "- `ai_visibility` — автоматическая проверка AI-упоминаний",
        "- `trend_research` — тренды в вашей нише",
    ]

    return "\n".join(lines)
