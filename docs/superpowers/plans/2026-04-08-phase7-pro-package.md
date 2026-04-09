# Phase 7: Pro-пакет и монетизация — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the Marketolog MCP server into a free open-source `marketolog` package (Core + basic SEO + UTM + prompts) and a paid `marketolog-pro` package (Content, SMM, Analytics-full, Strategy, SEO-advanced), write a comprehensive README, and prepare both for PyPI publishing.

**Architecture:** `server.py` is refactored to register only free tools. At the end of `create_server()`, it does `try: import marketolog_pro` which — if the package is installed — registers Pro tools into the same `mcp` instance. The `marketolog-pro` package lives in a `pro/` directory at repo root with its own `pyproject.toml`. Free tools: 10 (6 Core + 3 SEO-basic + 1 UTM). Pro tools: 36 (5 SEO-advanced + 7 Analytics + 7 Content + 10 SMM + 7 Strategy).

**Tech Stack:** Python 3.11+, hatchling, FastMCP, pytest

---

## Free vs Pro Split (from spec section 12)

**`marketolog` (free, 10 tools):**
- Core (6): `create_project`, `switch_project`, `list_projects`, `update_project`, `delete_project`, `get_project_context`
- SEO basic (3): `seo_audit`, `ai_seo_check`, `keyword_research`
- Analytics basic (1): `generate_utm_link`
- All 5 prompts (strategist, seo_expert, analyst, content_writer, smm_manager)

**`marketolog-pro` (paid, 36 tools):**
- SEO advanced (5): `keyword_cluster`, `check_positions`, `analyze_competitors`, `content_gap`, `webmaster_report`
- Analytics (7): `metrika_report`, `metrika_goals`, `search_console_report`, `traffic_sources`, `funnel_analysis`, `weekly_digest`, `ai_referral_report`
- Content (7): `content_plan`, `generate_article`, `generate_post`, `optimize_text`, `analyze_content`, `generate_meta`, `repurpose_content`
- SMM (10): `telegram_post`, `telegram_stats`, `vk_post`, `vk_stats`, `max_post`, `max_stats`, `dzen_publish`, `trend_research`, `smm_calendar`, `best_time_to_post`
- Strategy (7): `analyze_target_audience`, `analyze_positioning`, `competitor_intelligence`, `marketing_plan`, `channel_recommendation`, `brand_health`, `ai_visibility`

## File Structure

```
# Modified existing files
src/marketolog/server.py              — stripped to free tools only + pro plugin hook
pyproject.toml                        — updated with [project.scripts] entry point
README.md                             — full documentation

# New: Pro package
pro/
├── pyproject.toml                    — marketolog-pro package config
└── src/
    └── marketolog_pro/
        ├── __init__.py               — imports server, registers all pro tools
        └── _register.py              — all pro tool registrations (closures)

# Modified tests
tests/test_server.py                  — update tool count expectations
tests/test_modules/test_seo/test_integration.py
tests/test_modules/test_analytics/test_integration.py
tests/test_modules/test_content/test_integration.py
tests/test_modules/test_smm/test_integration.py
tests/test_modules/test_strategy/test_integration.py

# New tests
tests/test_pro_integration.py         — verify pro registration works
```

---

### Task 1: Refactor `server.py` to register only free tools

**Files:**
- Modify: `src/marketolog/server.py`

- [ ] **Step 1: Read the current server.py**

Read `src/marketolog/server.py` to understand all imports and tool registrations.

- [ ] **Step 2: Remove Pro imports from server.py**

Remove these imports (keep only free tool imports):

```python
# REMOVE these lines:
from marketolog.modules.seo.positions import run_check_positions
from marketolog.modules.seo.competitors import run_analyze_competitors, run_content_gap
from marketolog.modules.seo.webmaster import run_webmaster_report
from marketolog.modules.analytics.metrika import run_metrika_report, run_metrika_goals
from marketolog.modules.analytics.search_console import run_search_console_report
from marketolog.modules.analytics.traffic_sources import run_traffic_sources
from marketolog.modules.analytics.funnel import run_funnel_analysis
from marketolog.modules.analytics.ai_referral import run_ai_referral_report
from marketolog.modules.analytics.digest import run_weekly_digest
from marketolog.modules.content.planner import run_content_plan
from marketolog.modules.content.generator import run_generate_article, run_generate_post, run_repurpose_content
from marketolog.modules.content.optimizer import run_optimize_text
from marketolog.modules.content.analyzer import run_analyze_content
from marketolog.modules.content.meta import run_generate_meta
from marketolog.modules.smm.telegram import run_telegram_post, run_telegram_stats
from marketolog.modules.smm.vk import run_vk_post, run_vk_stats
from marketolog.modules.smm.max_api import run_max_post, run_max_stats
from marketolog.modules.smm.dzen import run_dzen_publish
from marketolog.modules.smm.trends import run_trend_research
from marketolog.modules.smm.calendar import run_smm_calendar, run_best_time_to_post
from marketolog.modules.strategy.audience import run_analyze_target_audience
from marketolog.modules.strategy.positioning import run_analyze_positioning
from marketolog.modules.strategy.intelligence import run_competitor_intelligence
from marketolog.modules.strategy.planning import run_marketing_plan
from marketolog.modules.strategy.channels import run_channel_recommendation
from marketolog.modules.strategy.brand import run_brand_health
from marketolog.modules.strategy.ai_visibility import run_ai_visibility
```

Keep ONLY these imports:

```python
from marketolog.modules.seo.audit import run_seo_audit
from marketolog.modules.seo.ai_seo import run_ai_seo_check
from marketolog.modules.seo.keywords import run_keyword_research
from marketolog.modules.analytics.utm import generate_utm as _generate_utm
```

Note: `run_keyword_cluster` was imported from `keywords` — remove it from the import.

- [ ] **Step 3: Remove Pro tool registrations from `create_server()`**

Remove ALL tool registrations in these sections:
- SEO tools: `keyword_cluster`, `check_positions`, `analyze_competitors`, `content_gap`, `webmaster_report`
- Analytics tools: `metrika_report`, `metrika_goals`, `search_console_report`, `traffic_sources`, `funnel_analysis`, `weekly_digest`, `ai_referral_report` (keep `generate_utm_link`)
- Content tools: ALL (entire section)
- SMM tools: ALL (entire section)
- Strategy tools: ALL (entire section)

Also remove the `_get_counter_id()` helper function since it's only used by pro analytics tools.

Keep:
- Core tools (6): `create_project`, `switch_project`, `list_projects`, `update_project`, `delete_project`, `get_project_context`
- SEO basic (3): `seo_audit`, `ai_seo_check`, `keyword_research`
- Analytics basic (1): `generate_utm_link`
- All prompt resources (5)
- Scheduled posts check

- [ ] **Step 4: Export `mcp`, `ctx`, `config`, `cache` for Pro plugin access**

At the end of `create_server()`, before `return mcp`, add the pro plugin hook:

```python
    # --- Pro Plugin Hook ---
    # If marketolog-pro is installed, it registers additional tools
    try:
        from marketolog_pro import register_pro_tools
        register_pro_tools(mcp=mcp, ctx=ctx, config=config, cache=cache)
    except ImportError:
        pass  # Pro not installed — free version only

    return mcp
```

- [ ] **Step 5: Verify free-only server starts**

Run: `pytest tests/test_server.py -v`
Expected: May need adjustment (will fix in Task 3)

- [ ] **Step 6: Commit**

```bash
git add src/marketolog/server.py
git commit -m "refactor(server): strip Pro tools, keep free-only (10 tools) + pro plugin hook"
```

---

### Task 2: Create `marketolog-pro` package

**Files:**
- Create: `pro/pyproject.toml`
- Create: `pro/src/marketolog_pro/__init__.py`
- Create: `pro/src/marketolog_pro/_register.py`

- [ ] **Step 1: Create pro package structure**

```bash
mkdir -p pro/src/marketolog_pro
```

- [ ] **Step 2: Create `pro/pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "marketolog-pro"
version = "0.1.0"
description = "Pro-расширение для Marketolog — Content, SMM, Analytics, Strategy"
readme = "README.md"
license = "Proprietary"
requires-python = ">=3.11"
dependencies = [
    "marketolog>=0.1.0",
]
```

- [ ] **Step 3: Create `pro/src/marketolog_pro/__init__.py`**

```python
"""Marketolog Pro — расширение с Content, SMM, Analytics, Strategy модулями."""

__version__ = "0.1.0"

from marketolog_pro._register import register_pro_tools

__all__ = ["register_pro_tools"]
```

- [ ] **Step 4: Create `pro/src/marketolog_pro/_register.py`**

This file contains the `register_pro_tools()` function that registers all 36 Pro tools into the MCP server instance. It receives `mcp`, `ctx`, `config`, `cache` from the free server.

```python
"""Register all Pro tools into the Marketolog MCP server."""

from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from marketolog.core.config import MarketologConfig
from marketolog.core.context import ProjectContext
from marketolog.utils.cache import FileCache

# --- Pro module imports ---
from marketolog.modules.seo.keywords import run_keyword_cluster
from marketolog.modules.seo.positions import run_check_positions
from marketolog.modules.seo.competitors import run_analyze_competitors, run_content_gap
from marketolog.modules.seo.webmaster import run_webmaster_report
from marketolog.modules.analytics.metrika import run_metrika_report, run_metrika_goals
from marketolog.modules.analytics.search_console import run_search_console_report
from marketolog.modules.analytics.traffic_sources import run_traffic_sources
from marketolog.modules.analytics.funnel import run_funnel_analysis
from marketolog.modules.analytics.ai_referral import run_ai_referral_report
from marketolog.modules.analytics.digest import run_weekly_digest
from marketolog.modules.content.planner import run_content_plan
from marketolog.modules.content.generator import (
    run_generate_article,
    run_generate_post,
    run_repurpose_content,
)
from marketolog.modules.content.optimizer import run_optimize_text
from marketolog.modules.content.analyzer import run_analyze_content
from marketolog.modules.content.meta import run_generate_meta
from marketolog.modules.smm.telegram import run_telegram_post, run_telegram_stats
from marketolog.modules.smm.vk import run_vk_post, run_vk_stats
from marketolog.modules.smm.max_api import run_max_post, run_max_stats
from marketolog.modules.smm.dzen import run_dzen_publish
from marketolog.modules.smm.trends import run_trend_research
from marketolog.modules.smm.calendar import run_smm_calendar, run_best_time_to_post
from marketolog.modules.strategy.audience import run_analyze_target_audience
from marketolog.modules.strategy.positioning import run_analyze_positioning
from marketolog.modules.strategy.intelligence import run_competitor_intelligence
from marketolog.modules.strategy.planning import run_marketing_plan
from marketolog.modules.strategy.channels import run_channel_recommendation
from marketolog.modules.strategy.brand import run_brand_health
from marketolog.modules.strategy.ai_visibility import run_ai_visibility

READ_ONLY = ToolAnnotations(readOnlyHint=True)
MUTATING = ToolAnnotations(readOnlyHint=False)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)


def register_pro_tools(
    *,
    mcp: FastMCP,
    ctx: ProjectContext,
    config: MarketologConfig,
    cache: FileCache,
) -> None:
    """Register all Pro tools into the MCP server instance."""

    def _get_counter_id() -> str:
        """Get Metrika counter ID from config or project context."""
        if config.yandex_metrika_counter:
            return config.yandex_metrika_counter
        project = ctx.get_context()
        return project.get("seo", {}).get("yandex_metrika_id", "")

    # --- SEO Advanced ---

    @mcp.tool(annotations=READ_ONLY)
    async def keyword_cluster(
        keywords: Annotated[list[dict], Field(description='Список: [{"text": "...", "count": N}, ...]')],
    ) -> str:
        """Кластеризация ключевых слов по интенту."""
        clusters = run_keyword_cluster(keywords)
        lines = []
        for c in clusters:
            lines.append(f"\n### {c['name']} (суммарный объём: {c['total_volume']})")
            for kw in c["keywords"]:
                lines.append(f"  - {kw['text']}: {kw.get('count', '?')}")
        return "\n".join(lines) if lines else "Не удалось кластеризовать."

    @mcp.tool(annotations=READ_ONLY)
    async def check_positions(
        keywords: Annotated[list[str] | None, Field(description="Ключевые слова. Если не указаны — из проекта", default=None)] = None,
    ) -> str:
        """Позиции сайта в Яндексе по ключевым словам."""
        project = ctx.get_context()
        site_url = project["url"]
        if keywords is None:
            keywords = project.get("seo", {}).get("main_keywords", [])
        if not keywords:
            return "Укажите keywords или добавьте main_keywords в проект."
        return await run_check_positions(keywords=keywords, site_url=site_url, config=config, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    async def analyze_competitors(
        competitor_urls: Annotated[list[str] | None, Field(description="URL конкурентов. Если не указаны — из проекта", default=None)] = None,
    ) -> str:
        """Анализ конкурентов: структура, контент, мета-теги, schema markup."""
        if competitor_urls is None:
            project = ctx.get_context()
            competitor_urls = [c["url"] for c in project.get("competitors", []) if c.get("url")]
        if not competitor_urls:
            return "Укажите competitor_urls или добавьте конкурентов в проект."
        return await run_analyze_competitors(competitor_urls=competitor_urls, config=config, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    async def content_gap(
        competitor_urls: Annotated[list[str] | None, Field(description="URL конкурентов", default=None)] = None,
    ) -> str:
        """Ключевые слова, по которым ранжируются конкуренты, но не вы."""
        project = ctx.get_context()
        site_url = project["url"]
        if competitor_urls is None:
            competitor_urls = [c["url"] for c in project.get("competitors", []) if c.get("url")]
        keywords = project.get("seo", {}).get("main_keywords", [])
        if not competitor_urls:
            return "Укажите competitor_urls или добавьте конкурентов в проект."
        return await run_content_gap(site_url=site_url, competitor_urls=competitor_urls, keywords=keywords, config=config, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    async def webmaster_report() -> str:
        """Отчёт Яндекс.Вебмастера: индексация, ошибки, популярные запросы."""
        project = ctx.get_context()
        host = project.get("seo", {}).get("webmaster_host", project["url"])
        return await run_webmaster_report(host=host, config=config, cache=cache)

    # --- Analytics Pro ---

    @mcp.tool(annotations=READ_ONLY)
    async def metrika_report(
        period: Annotated[str, Field(description="Период: 7d, 30d, 90d, today", default="7d")] = "7d",
        metrics: Annotated[str | None, Field(description="Метрики (через запятую)", default=None)] = None,
    ) -> str:
        """Отчёт Яндекс.Метрика: визиты, источники, поведение, конверсии."""
        counter_id = _get_counter_id()
        if not counter_id:
            return "Укажите YANDEX_METRIKA_COUNTER или добавьте yandex_metrika_id в проект."
        return await run_metrika_report(counter_id=counter_id, config=config, cache=cache, period=period, metrics=metrics)

    @mcp.tool(annotations=READ_ONLY)
    async def metrika_goals() -> str:
        """Список целей и конверсий в Яндекс.Метрике."""
        counter_id = _get_counter_id()
        if not counter_id:
            return "Укажите YANDEX_METRIKA_COUNTER или добавьте yandex_metrika_id в проект."
        return await run_metrika_goals(counter_id=counter_id, config=config, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    async def search_console_report(
        period: Annotated[str, Field(description="Период: 7d, 28d, 90d", default="7d")] = "7d",
    ) -> str:
        """Google Search Console: запросы, клики, позиции, CTR."""
        project = ctx.get_context()
        site_url = project.get("seo", {}).get("search_console_url", project["url"])
        return await run_search_console_report(site_url=site_url, config=config, cache=cache, period=period)

    @mcp.tool(annotations=READ_ONLY)
    async def traffic_sources(
        period: Annotated[str, Field(description="Период: 7d, 30d, 90d", default="7d")] = "7d",
    ) -> str:
        """Сводка по источникам трафика: поиск, соцсети, прямые, реферальные."""
        counter_id = _get_counter_id()
        if not counter_id:
            return "Укажите YANDEX_METRIKA_COUNTER или добавьте yandex_metrika_id в проект."
        return await run_traffic_sources(counter_id=counter_id, config=config, cache=cache, period=period)

    @mcp.tool(annotations=READ_ONLY)
    async def funnel_analysis(
        goal: Annotated[str | None, Field(description="Название цели (если не указана — первая цель)", default=None)] = None,
    ) -> str:
        """Анализ воронки конверсии: источник → визиты → цель → конверсия."""
        counter_id = _get_counter_id()
        if not counter_id:
            return "Укажите YANDEX_METRIKA_COUNTER или добавьте yandex_metrika_id в проект."
        return await run_funnel_analysis(counter_id=counter_id, config=config, cache=cache, goal=goal)

    @mcp.tool(annotations=READ_ONLY)
    async def weekly_digest() -> str:
        """Еженедельный дайджест: ключевые метрики, источники, тренды."""
        counter_id = _get_counter_id()
        if not counter_id:
            return "Укажите YANDEX_METRIKA_COUNTER или добавьте yandex_metrika_id в проект."
        project = ctx.get_context()
        project_name = project.get("name", "Проект")
        return await run_weekly_digest(counter_id=counter_id, project_name=project_name, config=config, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    async def ai_referral_report(
        period: Annotated[str, Field(description="Период: 7d, 30d, 90d", default="30d")] = "30d",
    ) -> str:
        """Трафик с AI-поисковиков: ChatGPT, Perplexity, Claude, Google AI Overviews."""
        counter_id = _get_counter_id()
        if not counter_id:
            return "Укажите YANDEX_METRIKA_COUNTER или добавьте yandex_metrika_id в проект."
        return await run_ai_referral_report(counter_id=counter_id, config=config, cache=cache, period=period)

    # --- Content ---

    @mcp.tool(annotations=READ_ONLY)
    def content_plan(
        period: Annotated[str, Field(description="Период планирования: '1 week', '2 weeks', '1 month'", default="2 weeks")] = "2 weeks",
        topics_count: Annotated[int, Field(description="Количество тем", default=10)] = 10,
    ) -> str:
        """Контент-план: темы, форматы, ключевые слова, календарь."""
        project = ctx.get_context()
        return run_content_plan(project_context=project, period=period, topics_count=topics_count)

    @mcp.tool(annotations=READ_ONLY)
    def generate_article(
        topic: Annotated[str, Field(description="Тема статьи")],
        keywords: Annotated[list[str] | None, Field(description="Целевые ключевые слова", default=None)] = None,
        length: Annotated[str, Field(description="Объём: short, medium, long", default="medium")] = "medium",
    ) -> str:
        """SEO-оптимизированная статья: собирает контекст (ключи, tone of voice, аудитория) для генерации."""
        project = ctx.get_context()
        return run_generate_article(topic=topic, project_context=project, keywords=keywords, length=length)

    @mcp.tool(annotations=READ_ONLY)
    def generate_post(
        platform: Annotated[str, Field(description="Площадка: telegram, vk, max, dzen")],
        topic: Annotated[str | None, Field(description="Тема поста (если не указана — предложит)", default=None)] = None,
    ) -> str:
        """Пост для площадки: собирает контекст + гайдлайны площадки для генерации."""
        project = ctx.get_context()
        return run_generate_post(platform=platform, project_context=project, topic=topic)

    @mcp.tool(annotations=READ_ONLY)
    def optimize_text(
        text: Annotated[str, Field(description="Текст для анализа (Markdown)")],
        target_keywords: Annotated[list[str], Field(description="Целевые ключевые слова")],
    ) -> str:
        """SEO-оптимизация текста: плотность ключей, структура, читаемость, рекомендации."""
        return run_optimize_text(text=text, target_keywords=target_keywords)

    @mcp.tool(annotations=READ_ONLY)
    async def analyze_content(
        url: Annotated[str | None, Field(description="URL страницы для анализа. Если не указан — URL проекта", default=None)] = None,
    ) -> str:
        """Анализ контента страницы: читаемость, SEO-оценка, заголовки, мета-теги."""
        if url is None:
            url = ctx.get_context()["url"]
        return await run_analyze_content(url=url, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    def generate_meta(
        text: Annotated[str, Field(description="Текст или содержимое страницы для генерации мета-тегов")],
        keywords: Annotated[list[str] | None, Field(description="Целевые ключевые слова", default=None)] = None,
    ) -> str:
        """Генерация title, description, H1 — собирает контекст и требования."""
        return run_generate_meta(text=text, keywords=keywords)

    @mcp.tool(annotations=READ_ONLY)
    def repurpose_content(
        text: Annotated[str, Field(description="Исходный текст для адаптации")],
        formats: Annotated[list[str] | None, Field(description="Целевые форматы: telegram, vk, max, dzen, carousel, video_script", default=None)] = None,
    ) -> str:
        """Репёрпосинг контента: адаптация текста под разные площадки и форматы."""
        project = ctx.get_context()
        return run_repurpose_content(text=text, project_context=project, formats=formats)

    # --- SMM ---

    @mcp.tool(annotations=MUTATING)
    async def telegram_post(
        text: Annotated[str, Field(description="Текст поста (Markdown)")],
        channel: Annotated[str | None, Field(description="Канал (@username). Если не указан — из проекта", default=None)] = None,
        image_url: Annotated[str | None, Field(description="URL изображения", default=None)] = None,
    ) -> str:
        """Публикация поста в Telegram-канал."""
        if channel is None:
            channel = ctx.get_context().get("social", {}).get("telegram_channel", "")
        if not channel:
            return "Укажите channel или добавьте telegram_channel в проект."
        return await run_telegram_post(channel=channel, text=text, config=config, image_url=image_url)

    @mcp.tool(annotations=READ_ONLY)
    async def telegram_stats(
        channel: Annotated[str | None, Field(description="Канал (@username). Если не указан — из проекта", default=None)] = None,
    ) -> str:
        """Статистика Telegram-канала: подписчики, информация."""
        if channel is None:
            channel = ctx.get_context().get("social", {}).get("telegram_channel", "")
        if not channel:
            return "Укажите channel или добавьте telegram_channel в проект."
        return await run_telegram_stats(channel=channel, config=config, cache=cache)

    @mcp.tool(annotations=MUTATING)
    async def vk_post(
        text: Annotated[str, Field(description="Текст поста")],
        group: Annotated[str | None, Field(description="VK-группа. Если не указана — из проекта", default=None)] = None,
    ) -> str:
        """Публикация поста в VK-сообщество."""
        if group is None:
            group = ctx.get_context().get("social", {}).get("vk_group", "")
        if not group:
            return "Укажите group или добавьте vk_group в проект."
        return await run_vk_post(group=group, text=text, config=config)

    @mcp.tool(annotations=READ_ONLY)
    async def vk_stats(
        group: Annotated[str | None, Field(description="VK-группа. Если не указана — из проекта", default=None)] = None,
        period: Annotated[str, Field(description="Период: 7d, 30d, 90d", default="7d")] = "7d",
    ) -> str:
        """Статистика VK-сообщества: просмотры, посетители, охват."""
        if group is None:
            group = ctx.get_context().get("social", {}).get("vk_group", "")
        if not group:
            return "Укажите group или добавьте vk_group в проект."
        return await run_vk_stats(group=group, config=config, cache=cache, period=period)

    @mcp.tool(annotations=MUTATING)
    async def max_post(
        text: Annotated[str, Field(description="Текст поста (Markdown, до 4000 символов)")],
        channel: Annotated[str | None, Field(description="MAX-канал. Если не указан — из проекта", default=None)] = None,
    ) -> str:
        """Публикация поста в MAX-канал."""
        if channel is None:
            channel = ctx.get_context().get("social", {}).get("max_channel", "")
        if not channel:
            return "Укажите channel или добавьте max_channel в проект."
        return await run_max_post(channel=channel, text=text, config=config)

    @mcp.tool(annotations=READ_ONLY)
    async def max_stats(
        channel: Annotated[str | None, Field(description="MAX-канал. Если не указан — из проекта", default=None)] = None,
    ) -> str:
        """Статистика MAX-канала: участники, информация."""
        if channel is None:
            channel = ctx.get_context().get("social", {}).get("max_channel", "")
        if not channel:
            return "Укажите channel или добавьте max_channel в проект."
        return await run_max_stats(channel=channel, config=config, cache=cache)

    @mcp.tool(annotations=MUTATING)
    async def dzen_publish(
        text: Annotated[str, Field(description="Текст для публикации в Дзен")],
        image_url: Annotated[str | None, Field(description="URL изображения", default=None)] = None,
    ) -> str:
        """Публикация в Дзен через Telegram-кросспостинг (@zen_sync_bot)."""
        project = ctx.get_context()
        return await run_dzen_publish(text=text, project_context=project, config=config, image_url=image_url)

    @mcp.tool(annotations=READ_ONLY)
    async def trend_research(
        topic: Annotated[str | None, Field(description="Тема для исследования. Если не указана — ниша проекта", default=None)] = None,
        platform: Annotated[str | None, Field(description="Площадка для фильтрации", default=None)] = None,
    ) -> str:
        """Исследование трендов: актуальные темы и контент в нише."""
        if topic is None:
            topic = ctx.get_context().get("niche", "маркетинг")
        return await run_trend_research(topic=topic, config=config, cache=cache, platform=platform)

    @mcp.tool(annotations=READ_ONLY)
    def smm_calendar(
        period: Annotated[str, Field(description="Период: '1 week', '2 weeks', '1 month'", default="1 week")] = "1 week",
    ) -> str:
        """Сводный календарь публикаций по всем площадкам."""
        project = ctx.get_context()
        return run_smm_calendar(project_context=project, period=period)

    @mcp.tool(annotations=READ_ONLY)
    def best_time_to_post(
        platform: Annotated[str | None, Field(description="Площадка: telegram, vk, max, dzen", default=None)] = None,
    ) -> str:
        """Рекомендация лучшего времени публикации (бенчмарки Рунета)."""
        project = ctx.get_context()
        return run_best_time_to_post(project_context=project, platform=platform)

    # --- Strategy ---

    @mcp.tool(annotations=READ_ONLY)
    def analyze_target_audience() -> str:
        """Портреты ЦА (ICP): кто, боли, мотивация, каналы."""
        project = ctx.get_context()
        return run_analyze_target_audience(project_context=project)

    @mcp.tool(annotations=READ_ONLY)
    def analyze_positioning() -> str:
        """Позиционирование: отличия от конкурентов, УТП, слабые стороны."""
        project = ctx.get_context()
        return run_analyze_positioning(project_context=project)

    @mcp.tool(annotations=READ_ONLY)
    async def competitor_intelligence(
        competitor_urls: Annotated[list[str] | None, Field(description="URL конкурентов. Если не указаны — из проекта", default=None)] = None,
    ) -> str:
        """Глубокий анализ конкурентов: продукт, цены, контент, соцсети, SEO, каналы."""
        project = ctx.get_context()
        return await run_competitor_intelligence(
            project_context=project, config=config, cache=cache, competitor_urls=competitor_urls,
        )

    @mcp.tool(annotations=MUTATING)
    def marketing_plan(
        period: Annotated[str, Field(description="Период: '1 month', '3 months', '6 months'", default="3 months")] = "3 months",
        budget: Annotated[str | None, Field(description="Месячный бюджет в рублях", default=None)] = None,
    ) -> str:
        """Маркетинговый план: цели, каналы, бюджет, метрики, календарь."""
        project = ctx.get_context()
        return run_marketing_plan(project_context=project, period=period, budget=budget)

    @mcp.tool(annotations=READ_ONLY)
    def channel_recommendation() -> str:
        """Рекомендация каналов продвижения с прогнозом ROI."""
        project = ctx.get_context()
        return run_channel_recommendation(project_context=project)

    @mcp.tool(annotations=READ_ONLY)
    async def brand_health() -> str:
        """Здоровье бренда: упоминания, отзывы, динамика."""
        project = ctx.get_context()
        return await run_brand_health(project_context=project, config=config, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    async def ai_visibility(
        brand_name: Annotated[str | None, Field(description="Название бренда. Если не указано — из проекта", default=None)] = None,
    ) -> str:
        """Мониторинг упоминаний бренда в AI-ответах (ChatGPT, Claude, Perplexity)."""
        project = ctx.get_context()
        return await run_ai_visibility(
            project_context=project, config=config, cache=cache, brand_name=brand_name,
        )
```

- [ ] **Step 5: Install pro package in development mode**

```bash
pip install -e pro/
```

- [ ] **Step 6: Commit**

```bash
git add pro/
git commit -m "feat(pro): create marketolog-pro package with 36 tool registrations"
```

---

### Task 3: Fix all integration tests for free/pro split

**Files:**
- Modify: `tests/test_server.py`
- Modify: `tests/test_modules/test_seo/test_integration.py`
- Modify: `tests/test_modules/test_analytics/test_integration.py`
- Modify: `tests/test_modules/test_content/test_integration.py`
- Modify: `tests/test_modules/test_smm/test_integration.py`
- Modify: `tests/test_modules/test_strategy/test_integration.py`
- Create: `tests/test_pro_integration.py`

- [ ] **Step 1: Update tool count in all module integration tests**

All existing integration tests check `len(tools) == 46`. With Pro installed in dev mode, this should still work — `register_pro_tools` is called automatically. But we need to ensure this is explicit.

In each integration test file, update the `test_total_tool_count` function comment:

`tests/test_modules/test_seo/test_integration.py`:
```python
def test_total_tool_count(server):
    """Server should have 46 tools when marketolog-pro is installed."""
    tools = asyncio.run(server._local_provider.list_tools())
    assert len(tools) == 46, f"Expected 46 tools, got {len(tools)}: {[t.name for t in tools]}"
```

(Same for analytics, content, smm, strategy integration tests — update docstring only.)

- [ ] **Step 2: Create `tests/test_pro_integration.py`**

```python
"""Integration tests — free vs pro tool split."""

import asyncio
import sys
from pathlib import Path
from unittest import mock

import pytest

from marketolog.server import create_server


@pytest.fixture
def server(tmp_marketolog_dir: Path):
    return create_server(base_dir=tmp_marketolog_dir)


FREE_TOOLS = {
    "create_project", "switch_project", "list_projects",
    "update_project", "delete_project", "get_project_context",
    "seo_audit", "ai_seo_check", "keyword_research",
    "generate_utm_link",
}

PRO_TOOLS = {
    "keyword_cluster", "check_positions", "analyze_competitors",
    "content_gap", "webmaster_report",
    "metrika_report", "metrika_goals", "search_console_report",
    "traffic_sources", "funnel_analysis", "weekly_digest", "ai_referral_report",
    "content_plan", "generate_article", "generate_post",
    "optimize_text", "analyze_content", "generate_meta", "repurpose_content",
    "telegram_post", "telegram_stats", "vk_post", "vk_stats",
    "max_post", "max_stats", "dzen_publish",
    "trend_research", "smm_calendar", "best_time_to_post",
    "analyze_target_audience", "analyze_positioning",
    "competitor_intelligence", "marketing_plan",
    "channel_recommendation", "brand_health", "ai_visibility",
}


def test_with_pro_installed(server):
    """With Pro installed, server exposes all 46 tools."""
    tools = asyncio.run(server._local_provider.list_tools())
    tool_names = {t.name for t in tools}
    assert FREE_TOOLS.issubset(tool_names), f"Missing free: {FREE_TOOLS - tool_names}"
    assert PRO_TOOLS.issubset(tool_names), f"Missing pro: {PRO_TOOLS - tool_names}"
    assert len(tools) == 46


def test_without_pro_installed(tmp_marketolog_dir: Path):
    """Without Pro, server exposes only 10 free tools."""
    # Block marketolog_pro from being imported
    with mock.patch.dict(sys.modules, {"marketolog_pro": None}):
        server = create_server(base_dir=tmp_marketolog_dir)
        tools = asyncio.run(server._local_provider.list_tools())
        tool_names = {t.name for t in tools}
        assert FREE_TOOLS.issubset(tool_names), f"Missing free: {FREE_TOOLS - tool_names}"
        assert len(tool_names & PRO_TOOLS) == 0, f"Pro tools present without pro: {tool_names & PRO_TOOLS}"
        assert len(tools) == 10, f"Expected 10 free tools, got {len(tools)}: {[t.name for t in tools]}"


def test_free_server_has_all_prompts(tmp_marketolog_dir: Path):
    """Prompts are available even without Pro."""
    with mock.patch.dict(sys.modules, {"marketolog_pro": None}):
        server = create_server(base_dir=tmp_marketolog_dir)
        resources = asyncio.run(server._local_provider.list_resources())
        resource_uris = {str(r.uri) for r in resources}
        expected = {"strategist", "seo_expert", "analyst", "content_writer", "smm_manager"}
        for name in expected:
            assert any(name in uri for uri in resource_uris), f"Missing prompt: {name}"
```

- [ ] **Step 3: Run all tests**

Run: `pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_pro_integration.py tests/test_server.py tests/test_modules/
git commit -m "test: add free/pro split integration tests"
```

---

### Task 4: Update pyproject.toml and add console_scripts entry point

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Update pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "marketolog"
version = "0.1.0"
description = "AI-маркетолог для бизнеса в Рунете — MCP-сервер для Claude"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
keywords = ["mcp", "marketing", "seo", "claude", "ai", "runet"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Internet :: WWW/HTTP",
]
dependencies = [
    "fastmcp>=3.0",
    "httpx>=0.27",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "beautifulsoup4>=4.12",
    "lxml>=5.0",
]

[project.scripts]
marketolog = "marketolog.__main__:main"

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "respx>=0.22",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Verify entry point works**

Run: `python -m marketolog auth status`
Expected: Prints credentials status

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "build: add console_scripts entry point and PyPI classifiers"
```

---

### Task 5: Write comprehensive README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write README.md**

```markdown
# Marketolog

AI-маркетолог для бизнеса в Рунете — MCP-сервер для Claude.

Подключается к Claude Desktop, Claude Code или claude.ai. Агент анализирует ваш проект, предлагает стратегию продвижения и выполняет задачи (SEO-аудит, контент-план, публикации в соцсети) после одобрения.

## Возможности

**Бесплатно (marketolog):**
- Управление проектами — создание, контекст, настройки
- SEO-аудит — Core Web Vitals, мета-теги, robots.txt, sitemap
- Проверка AI-готовности — GPTBot, ClaudeBot, llms.txt
- Подбор ключевых слов — Яндекс Wordstat API
- UTM-разметка ссылок
- Все промпты (маркетолог-стратег, SEO, аналитик, контент, SMM)

**Pro (marketolog-pro):**
- SEO расширенный — кластеризация, позиции, конкуренты, content gap
- Аналитика — Яндекс.Метрика, Google Search Console, воронки, AI-трафик
- Контент — план, генерация статей и постов, оптимизация, репёрпосинг
- SMM — публикация в Telegram, VK, MAX, Дзен + статистика
- Стратегия — ЦА, позиционирование, конкурентная разведка, маркетинг-план

## Быстрый старт

### Установка

```bash
pip install marketolog
```

### Подключение к Claude Desktop

Добавьте в `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "marketolog": {
      "command": "python",
      "args": ["-m", "marketolog"]
    }
  }
}
```

### Подключение к Claude Code

```bash
claude mcp add marketolog -- python -m marketolog
```

### Первый запуск

Скажите Claude:

> Создай проект my-saas с URL https://my-saas.ru в нише «управление проектами»

Claude создаст проект и предложит план действий.

## Настройка API-ключей

Ни один ключ не обязателен — подключайте сервисы по мере необходимости.

### Через CLI (рекомендуется)

```bash
python -m marketolog auth yandex      # OAuth для Метрики + Вебмастера
python -m marketolog auth wordstat    # OAuth для Wordstat
python -m marketolog auth vk          # Токен VK
python -m marketolog auth telegram    # Токен Telegram-бота
python -m marketolog auth max         # Токен MAX-бота
python -m marketolog auth status      # Статус подключений
```

### Через переменные окружения

| Переменная | Назначение |
|---|---|
| `YANDEX_OAUTH_TOKEN` | Яндекс.Метрика + Вебмастер |
| `YANDEX_WORDSTAT_TOKEN` | Яндекс Wordstat API |
| `YANDEX_SEARCH_API_KEY` | Яндекс Поиск API v2 |
| `YANDEX_FOLDER_ID` | Yandex Cloud Folder ID |
| `YANDEX_METRIKA_COUNTER` | ID счётчика Метрики |
| `VK_API_TOKEN` | Токен сообщества VK |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота |
| `MAX_BOT_TOKEN` | Токен MAX-бота |
| `GOOGLE_SC_CREDENTIALS` | Путь к service account JSON |
| `EXA_API_KEY` | Exa API (для трендов и AI-видимости) |
| `PAGESPEED_API_KEY` | PageSpeed (увеличивает квоту) |

## Инструменты

### Core (6)

| Инструмент | Описание |
|---|---|
| `create_project` | Создать проект |
| `switch_project` | Переключить активный проект |
| `list_projects` | Список проектов |
| `update_project` | Обновить поле проекта |
| `delete_project` | Удалить проект |
| `get_project_context` | Полный контекст проекта |

### SEO (8)

| Инструмент | Пакет | Описание |
|---|---|---|
| `seo_audit` | free | Технический SEO-аудит |
| `ai_seo_check` | free | Готовность к AI-поисковикам |
| `keyword_research` | free | Подбор ключевых слов |
| `keyword_cluster` | pro | Кластеризация по интенту |
| `check_positions` | pro | Позиции в Яндексе |
| `analyze_competitors` | pro | Анализ конкурентов |
| `content_gap` | pro | Контентные пробелы |
| `webmaster_report` | pro | Яндекс.Вебмастер |

### Analytics (8)

| Инструмент | Пакет | Описание |
|---|---|---|
| `generate_utm_link` | free | UTM-разметка |
| `metrika_report` | pro | Яндекс.Метрика |
| `metrika_goals` | pro | Цели Метрики |
| `search_console_report` | pro | Google Search Console |
| `traffic_sources` | pro | Источники трафика |
| `funnel_analysis` | pro | Воронка конверсии |
| `weekly_digest` | pro | Еженедельный дайджест |
| `ai_referral_report` | pro | AI-трафик |

### Content (7) — pro

| Инструмент | Описание |
|---|---|
| `content_plan` | Контент-план |
| `generate_article` | SEO-статья |
| `generate_post` | Пост для площадки |
| `optimize_text` | SEO-оптимизация текста |
| `analyze_content` | Анализ контента страницы |
| `generate_meta` | Title, description, H1 |
| `repurpose_content` | Адаптация под форматы |

### SMM (10) — pro

| Инструмент | Описание |
|---|---|
| `telegram_post` | Пост в Telegram |
| `telegram_stats` | Статистика Telegram |
| `vk_post` | Пост в VK |
| `vk_stats` | Статистика VK |
| `max_post` | Пост в MAX |
| `max_stats` | Статистика MAX |
| `dzen_publish` | Публикация в Дзен |
| `trend_research` | Тренды в нише |
| `smm_calendar` | Календарь публикаций |
| `best_time_to_post` | Лучшее время |

### Strategy (7) — pro

| Инструмент | Описание |
|---|---|
| `analyze_target_audience` | Портреты ЦА |
| `analyze_positioning` | УТП и позиционирование |
| `competitor_intelligence` | Конкурентная разведка |
| `marketing_plan` | Маркетинговый план |
| `channel_recommendation` | Рекомендация каналов |
| `brand_health` | Здоровье бренда |
| `ai_visibility` | AI-видимость |

## Хранилище данных

```
~/.marketolog/
├── config.yaml          # API-токены
├── projects/            # YAML-файлы проектов
├── cache/               # Кэш API-ответов
└── scheduled/           # Отложенные посты
```

## Лицензия

MIT
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: comprehensive README with tool reference and setup guide"
```

---

### Task 6: Run full test suite and verify

**Files:** None (verification only)

- [ ] **Step 1: Run all tests**

```bash
pytest tests/ -v
```

Expected: ALL PASS (187 existing + 3 new pro integration tests = 190)

- [ ] **Step 2: Verify free-only mode works**

```bash
python -c "
import sys
from unittest import mock
with mock.patch.dict(sys.modules, {'marketolog_pro': None}):
    from marketolog.server import create_server
    s = create_server()
    import asyncio
    tools = asyncio.run(s._local_provider.list_tools())
    print(f'Free tools: {len(tools)}')
    for t in tools:
        print(f'  - {t.name}')
    assert len(tools) == 10
print('OK: Free-only mode works')
"
```

- [ ] **Step 3: Verify full mode works**

```bash
python -c "
from marketolog.server import create_server
import asyncio
s = create_server()
tools = asyncio.run(s._local_provider.list_tools())
print(f'All tools: {len(tools)}')
assert len(tools) == 46
print('OK: Full mode (with Pro) works')
"
```

- [ ] **Step 4: Commit (if any fixes needed)**

---

### Summary

| Task | What | Files | Tests |
|------|------|-------|-------|
| 1 | Strip server.py to free-only + pro hook | 1 modified | — |
| 2 | Create marketolog-pro package | 3 created | — |
| 3 | Fix integration tests + add free/pro tests | 7 modified, 1 created | +3 |
| 4 | Update pyproject.toml | 1 modified | — |
| 5 | Write README | 1 modified | — |
| 6 | Full verification | — | — |

**Total: 6 tasks, ~190 tests expected**
