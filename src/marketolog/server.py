"""FastMCP server — registers Core tools and prompt resources."""

import logging
import time as _time
from pathlib import Path
from typing import Annotated

import yaml
from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from marketolog.core.config import load_config
from marketolog.core.context import ProjectContext
from marketolog.core.projects import (
    create_project as _create_project,
    delete_project as _delete_project,
    get_project,
    list_projects as _list_projects,
    update_project as _update_project,
)
from marketolog.modules.seo.audit import run_seo_audit
from marketolog.modules.seo.ai_seo import run_ai_seo_check
from marketolog.modules.seo.keywords import run_keyword_research, run_keyword_cluster
from marketolog.modules.seo.positions import run_check_positions
from marketolog.modules.seo.competitors import run_analyze_competitors, run_content_gap
from marketolog.modules.seo.webmaster import run_webmaster_report
from marketolog.utils.cache import FileCache

READ_ONLY = ToolAnnotations(readOnlyHint=True)
MUTATING = ToolAnnotations(readOnlyHint=False)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)

DEFAULT_BASE_DIR = Path.home() / ".marketolog"


def create_server(base_dir: Path = DEFAULT_BASE_DIR) -> FastMCP:
    """Create and configure the Marketolog MCP server."""
    mcp = FastMCP(
        "Marketolog",
        instructions="AI-маркетолог для бизнеса в Рунете. Начни с get_project_context().",
    )

    projects_dir = base_dir / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(config_dir=base_dir)
    ctx = ProjectContext(projects_dir=projects_dir)

    # --- Core Tools ---

    @mcp.tool(annotations=MUTATING)
    def create_project(
        name: Annotated[str, Field(description="Уникальное имя проекта (латиница, без пробелов)", examples=["my-saas"])],
        url: Annotated[str, Field(description="URL сайта проекта", examples=["https://my-saas.ru"])],
        niche: Annotated[str, Field(description="Ниша / тематика проекта", examples=["управление проектами"])],
        description: Annotated[str, Field(description="Краткое описание проекта", examples=["Таск-трекер для малых команд"])],
    ) -> str:
        """Создаёт новый проект. После создания используйте switch_project для активации."""
        result = _create_project(name, url, niche, description, projects_dir=projects_dir)
        return f"Проект '{name}' создан. Используйте switch_project('{name}') для активации."

    @mcp.tool(annotations=MUTATING)
    def switch_project(
        name: Annotated[str, Field(description="Имя проекта для активации")],
    ) -> str:
        """Переключает активный проект. Все инструменты будут работать в контексте этого проекта."""
        data = ctx.switch(name)
        return f"Активный проект: {data['name']} ({data['url']}), ниша: {data['niche']}"

    @mcp.tool(annotations=READ_ONLY)
    def list_projects() -> str:
        """Список всех проектов."""
        projects = _list_projects(projects_dir=projects_dir)
        if not projects:
            return "Нет проектов. Создайте первый через create_project()."
        lines = [f"- {p['name']}: {p['url']} ({p['niche']})" for p in projects]
        return "\n".join(lines)

    @mcp.tool(annotations=MUTATING)
    def update_project(
        field: Annotated[str, Field(
            description="Поле для обновления (поддерживает точечную нотацию: 'social.telegram_channel')",
            examples=["tone_of_voice", "social.vk_group", "seo.main_keywords"],
        )],
        value: Annotated[str, Field(description="Новое значение поля")],
    ) -> str:
        """Обновляет поле активного проекта."""
        context = ctx.get_context()
        name = context["name"]
        _update_project(name, field, value, projects_dir=projects_dir)
        ctx.refresh()
        return f"Обновлено: {field} = {value}"

    @mcp.tool(annotations=DESTRUCTIVE)
    def delete_project(
        name: Annotated[str, Field(description="Имя проекта для удаления")],
    ) -> str:
        """Удаляет проект (YAML-файл). Это действие необратимо."""
        _delete_project(name, projects_dir=projects_dir)
        if ctx._active_name == name:
            ctx.active_project = None
            ctx._active_name = None
        return f"Проект '{name}' удалён."

    @mcp.tool(annotations=READ_ONLY)
    def get_project_context() -> str:
        """Полный контекст активного проекта: ниша, ЦА, конкуренты, tone of voice, соцсети, SEO."""
        context = ctx.get_context()
        return yaml.dump(context, allow_unicode=True, sort_keys=False)

    cache = FileCache(base_dir=base_dir / "cache")

    # --- SEO Tools ---

    @mcp.tool(annotations=READ_ONLY)
    async def seo_audit(
        url: Annotated[str | None, Field(description="URL для аудита. Если не указан — URL проекта", default=None)] = None,
    ) -> str:
        """Технический SEO-аудит: Core Web Vitals, мета-теги, заголовки, robots.txt, sitemap, schema markup."""
        if url is None:
            url = ctx.get_context()["url"]
        return await run_seo_audit(url=url, config=config, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    async def ai_seo_check(
        url: Annotated[str | None, Field(description="URL для проверки. Если не указан — URL проекта", default=None)] = None,
    ) -> str:
        """Проверка готовности к AI-поисковикам: GPTBot, ClaudeBot, PerplexityBot, llms.txt, schema markup."""
        if url is None:
            url = ctx.get_context()["url"]
        return await run_ai_seo_check(url=url, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    async def keyword_research(
        seed_keywords: Annotated[list[str] | None, Field(description="Начальные ключевые слова. Если не указаны — из проекта", default=None)] = None,
        count: Annotated[int, Field(description="Макс. количество результатов", default=50)] = 50,
    ) -> str:
        """Подбор ключевых слов через Яндекс Wordstat API: частотность, топ запросов."""
        if seed_keywords is None:
            project = ctx.get_context()
            seed_keywords = project.get("seo", {}).get("main_keywords", [])
        if not seed_keywords:
            return "Укажите seed_keywords или добавьте main_keywords в проект."
        return await run_keyword_research(seed_keywords=seed_keywords, config=config, cache=cache, count=count)

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

    # --- Prompt Resources ---

    prompts_dir = Path(__file__).parent / "prompts"

    @mcp.resource("marketolog://prompts/strategist")
    def strategist_prompt() -> str:
        """Основной промпт маркетолога-стратега."""
        return (prompts_dir / "strategist.md").read_text(encoding="utf-8")

    @mcp.resource("marketolog://prompts/seo_expert")
    def seo_expert_prompt() -> str:
        """Промпт SEO-эксперта."""
        return (prompts_dir / "seo_expert.md").read_text(encoding="utf-8")

    # --- Scheduled Posts Check ---

    logger = logging.getLogger("marketolog")
    scheduled_dir = base_dir / "scheduled"
    scheduled_dir.mkdir(parents=True, exist_ok=True)

    def _check_scheduled_posts() -> list[str]:
        """Check for pending scheduled posts at server startup."""
        notifications = []
        now = _time.time()
        one_hour = 3600

        for path in sorted(scheduled_dir.glob("*.yaml")):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                scheduled_at = data.get("scheduled_at", 0)

                if scheduled_at <= now:
                    overdue_seconds = now - scheduled_at
                    platform = data.get("platform", "unknown")
                    text_preview = data.get("text", "")[:50]

                    if overdue_seconds > one_hour:
                        notifications.append(
                            f"ПРОСРОЧЕН (>{int(overdue_seconds/60)} мин): "
                            f"{platform} — \"{text_preview}...\". Файл: {path.name}"
                        )
                    else:
                        notifications.append(
                            f"ГОТОВ к отправке: {platform} — \"{text_preview}...\". "
                            f"Файл: {path.name}"
                        )
            except Exception as e:
                logger.warning(f"Ошибка чтения {path}: {e}")

        return notifications

    pending = _check_scheduled_posts()
    if pending:
        logger.info("Отложенные посты:\n" + "\n".join(pending))

    return mcp
