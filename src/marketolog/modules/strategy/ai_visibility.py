"""AI visibility — monitor brand mentions in AI search answers.

Checks how AI assistants (ChatGPT, Claude, Perplexity, Google AI)
reference the brand. Uses Exa API to find AI-generated content
mentioning the brand.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

EXA_API = "https://api.exa.ai/search"
CACHE_NS = "ai_visibility"
CACHE_TTL = 7200  # 2 hours

AI_PLATFORMS = [
    ("ChatGPT", "chatgpt.com"),
    ("Perplexity", "perplexity.ai"),
    ("Google AI", "google.com/search AI overview"),
    ("Claude", "claude.ai"),
]


async def run_ai_visibility(
    project_context: dict,
    *,
    config: MarketologConfig,
    cache: FileCache,
    brand_name: str | None = None,
) -> str:
    """Monitor brand mentions in AI search answers.

    Args:
        project_context: Full project context.
        config: App configuration (Exa API key required).
        cache: File cache.
        brand_name: Override brand name (default: project name).

    Returns:
        AI visibility report.
    """
    name = brand_name or project_context.get("name", "project")

    cached = cache.get(CACHE_NS, name)
    if cached is not None:
        return cached

    if not config.is_configured("exa_api_key"):
        return _setup_instructions(name)

    report = await _check_ai_mentions(name, project_context, config)

    cache.set(CACHE_NS, name, report, ttl_seconds=CACHE_TTL)
    return report


async def _check_ai_mentions(
    brand_name: str,
    project_context: dict,
    config: MarketologConfig,
) -> str:
    """Search Exa for AI-generated content mentioning the brand."""
    token: str = config.exa_api_key
    niche = project_context.get("niche", "")
    url = project_context.get("url", "")

    lines = [
        "## AI-видимость бренда",
        f"**Бренд:** {brand_name}",
        f"**URL:** {url}",
        "",
    ]

    queries = [
        f'"{brand_name}" AI рекомендация {niche}',
        f'"{brand_name}" лучшие инструменты {niche} 2026',
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

    # Deduplicate
    seen_urls: set[str] = set()
    unique_results = []
    for item in all_results:
        item_url = item.get("url", "")
        if item_url not in seen_urls:
            seen_urls.add(item_url)
            unique_results.append(item)

    lines.append(f"### Упоминания в AI-контексте ({len(unique_results)} найдено)")
    lines.append("")

    if unique_results:
        for i, item in enumerate(unique_results, 1):
            title = item.get("title", "Без заголовка")
            item_url = item.get("url", "")
            lines.append(f"{i}. **{title}**")
            if item_url:
                lines.append(f"   {item_url}")
    else:
        lines.append(f"Упоминаний «{brand_name}» в AI-контексте не найдено.")
    lines.append("")

    lines.append("### Проверка по AI-платформам")
    lines.append("")
    lines.append("Рекомендуем проверить вручную:")
    for platform_name, domain in AI_PLATFORMS:
        lines.append(f"- **{platform_name}** — спросите: «какие инструменты для {niche}?»")
    lines.append("")

    lines.append("### Как улучшить AI-видимость")
    lines.append("")
    lines.append("1. **llms.txt** — добавьте файл (проверьте через `ai_seo_check`)")
    lines.append("2. **Schema markup** — структурированные данные помогают AI понять контент")
    lines.append("3. **Экспертный контент** — AI цитирует авторитетные источники")
    lines.append("4. **Упоминания на авторитетных сайтах** — AI обучается на публичных данных")
    lines.append("5. **Уникальные данные** — исследования и отчёты повышают цитируемость")

    return "\n".join(lines)


def _setup_instructions(brand_name: str) -> str:
    """Return setup instructions when Exa is not configured."""
    return (
        f"## AI-видимость: {brand_name}\n\n"
        "Для мониторинга AI-упоминаний настройте Exa API:\n\n"
        "    EXA_API_KEY=<ваш ключ>\n"
        "Получить: https://exa.ai\n\n"
        "Пока API не настроен, проверьте вручную:\n"
        f'1. ChatGPT: "какие инструменты для [ваша ниша]?"\n'
        f'2. Perplexity: "{brand_name} обзор"\n'
        f'3. Claude: "порекомендуй [ваша ниша]"\n\n'
        "Используйте `ai_seo_check` для проверки технической готовности к AI-поиску."
    )
