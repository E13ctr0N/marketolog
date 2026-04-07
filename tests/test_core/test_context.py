from pathlib import Path

import pytest

from marketolog.core.context import ProjectContext
from marketolog.core.projects import create_project


@pytest.fixture
def ctx(tmp_marketolog_dir: Path) -> ProjectContext:
    projects_dir = tmp_marketolog_dir / "projects"
    create_project("alpha", "https://a.ru", "ниша A", "Проект A", projects_dir=projects_dir)
    create_project("beta", "https://b.ru", "ниша B", "Проект B", projects_dir=projects_dir)
    return ProjectContext(projects_dir=projects_dir)


def test_no_active_project(ctx: ProjectContext):
    assert ctx.active_project is None


def test_switch_project(ctx: ProjectContext):
    ctx.switch("alpha")
    assert ctx.active_project is not None
    assert ctx.active_project["name"] == "alpha"


def test_switch_to_nonexistent(ctx: ProjectContext):
    with pytest.raises(FileNotFoundError, match="не найден"):
        ctx.switch("ghost")


def test_get_context_no_active(ctx: ProjectContext):
    with pytest.raises(RuntimeError, match="Нет активного проекта"):
        ctx.get_context()


def test_get_context(ctx: ProjectContext):
    ctx.switch("alpha")
    context = ctx.get_context()
    assert context["name"] == "alpha"
    assert context["url"] == "https://a.ru"


def test_switch_reloads(ctx: ProjectContext):
    ctx.switch("alpha")
    assert ctx.active_project["niche"] == "ниша A"
    ctx.switch("beta")
    assert ctx.active_project["niche"] == "ниша B"


def test_refresh_reloads_from_disk(ctx: ProjectContext):
    ctx.switch("alpha")
    from marketolog.core.projects import update_project
    update_project("alpha", "niche", "обновлённая ниша", projects_dir=ctx.projects_dir)
    ctx.refresh()
    assert ctx.active_project["niche"] == "обновлённая ниша"
