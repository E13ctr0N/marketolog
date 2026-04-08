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

    # ── SEO Advanced (5) ──────────────────────────────────────────

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

    # ── Analytics (7) ─────────────────────────────────────────────

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

    # ── Content (7) ───────────────────────────────────────────────

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

    # ── SMM (10) ──────────────────────────────────────────────────

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

    # ── Strategy (7) ──────────────────────────────────────────────

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
