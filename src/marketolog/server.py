"""FastMCP server — registers Core tools and prompt resources."""

from pathlib import Path
from typing import Annotated

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
        import yaml
        context = ctx.get_context()
        return yaml.dump(context, allow_unicode=True, sort_keys=False)

    # --- Prompt Resources ---

    prompts_dir = Path(__file__).parent / "prompts"

    @mcp.resource("marketolog://prompts/strategist")
    def strategist_prompt() -> str:
        """Основной промпт маркетолога-стратега."""
        return (prompts_dir / "strategist.md").read_text(encoding="utf-8")

    return mcp
