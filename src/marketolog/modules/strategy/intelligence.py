"""Competitor intelligence — deep analysis via Exa API + project context.

Searches Exa for competitor mentions, reviews, pricing info.
Falls back to context-based analysis when Exa is not configured.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

EXA_API = "https://api.exa.ai/search"
CACHE_NS = "competitor_intel"
CACHE_TTL = 3600  # 1 hour


async def run_competitor_intelligence(
    project_context: dict,
    *,
    config: MarketologConfig,
    cache: FileCache,
    competitor_urls: list[str] | None = None,
) -> str:
    """Deep competitor analysis: product, pricing, content, channels.

    Args:
        project_context: Full project context.
        config: App configuration (Exa API key optional).
        cache: File cache.
        competitor_urls: Override competitor URLs (optional).

    Returns:
        Formatted competitor intelligence report.
    """
    project_name = project_context.get("name", "project")
    cache_key = f"{project_name}:competitors"

    cached = cache.get(CACHE_NS, cache_key)
    if cached is not None:
        return cached

    competitors = competitor_urls or [
        c.get("url", "") for c in project_context.get("competitors", []) if c.get("url")
    ]
    competitor_names = [
        c.get("name", c.get("url", "")) for c in project_context.get("competitors", [])
    ]

    niche = project_context.get("niche", "")

    if config.is_configured("exa_api_key") and competitors:
        report = await _search_exa_competitors(competitors, competitor_names, niche, config)
    else:
        report = _fallback_analysis(competitor_names, competitors, niche, project_context)

    cache.set(CACHE_NS, cache_key, report, ttl_seconds=CACHE_TTL)
    return report


async def _search_exa_competitors(
    urls: list[str],
    names: list[str],
    niche: str,
    config: MarketologConfig,
) -> str:
    """Search Exa for competitor intelligence."""
    token: str = config.exa_api_key

    lines = ["## Конкурентная разведка\n"]

    for i, url in enumerate(urls):
        name = names[i] if i < len(names) else url

        query = f"{name} {niche} обзор отзывы цены 2026"
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

        lines.append(f"### {name}")
        lines.append(f"URL: {url}")
        lines.append("")

        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                lines.append(f"Найдено {len(results)} источников:")
                for j, item in enumerate(results, 1):
                    title = item.get("title", "Без заголовка")
                    item_url = item.get("url", "")
                    lines.append(f"  {j}. {title}")
                    if item_url:
                        lines.append(f"     {item_url}")
            else:
                lines.append("Дополнительных данных не найдено.")
        else:
            lines.append("Не удалось получить данные из Exa.")

        lines.append("")

    lines.append("### Рекомендации")
    lines.append("- Используйте `analyze_competitors` (SEO) для технического сравнения сайтов")
    lines.append("- Используйте `analyze_positioning` для формулировки УТП на основе отличий")
    lines.append("- Используйте `content_gap` для поиска упущенных тем в контенте")

    return "\n".join(lines)


def _fallback_analysis(
    names: list[str],
    urls: list[str],
    niche: str,
    project_context: dict,
) -> str:
    """Context-based competitor analysis without Exa."""
    lines = ["## Конкурентная разведка\n"]

    if not names and not urls:
        lines.append("Конкуренты не указаны в проекте.")
        lines.append('Добавьте через `update_project("competitors", "[{name: ..., url: ...}]")`')
        lines.append("")
    else:
        for i, name in enumerate(names):
            url = urls[i] if i < len(urls) else ""
            lines.append(f"### {name}")
            if url:
                lines.append(f"URL: {url}")
            lines.append("")
            lines.append("**Что проанализировать:**")
            lines.append(f"- Продукт: какие задачи в нише «{niche}» решает?")
            lines.append("- Ценообразование: бесплатный тариф? Стоимость?")
            lines.append("- Контент: блог, соцсети, частота публикаций?")
            lines.append("- SEO: по каким запросам ранжируется?")
            lines.append("- Соцсети: какие площадки, активность?")
            lines.append("")

    lines.append("### Для глубокого анализа")
    lines.append("Настройте Exa API для автоматического сбора данных:")
    lines.append("    EXA_API_KEY=<ваш ключ>")
    lines.append("Получить: https://exa.ai")

    return "\n".join(lines)
