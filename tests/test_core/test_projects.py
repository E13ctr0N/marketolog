from pathlib import Path

import pytest
import yaml

from marketolog.core.projects import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)


@pytest.fixture
def projects_dir(tmp_marketolog_dir: Path) -> Path:
    return tmp_marketolog_dir / "projects"


def test_create_project(projects_dir: Path):
    result = create_project(
        name="my-saas",
        url="https://my-saas.ru",
        niche="управление проектами",
        description="Таск-трекер для малых команд",
        projects_dir=projects_dir,
    )
    assert result["name"] == "my-saas"
    assert (projects_dir / "my-saas.yaml").exists()

    data = yaml.safe_load((projects_dir / "my-saas.yaml").read_text(encoding="utf-8"))
    assert data["url"] == "https://my-saas.ru"
    assert data["niche"] == "управление проектами"
    assert "target_audience" in data
    assert "social" in data
    assert "seo" in data


def test_create_duplicate_project(projects_dir: Path):
    create_project("dup", "https://dup.ru", "ниша", "описание", projects_dir=projects_dir)
    with pytest.raises(ValueError, match="уже существует"):
        create_project("dup", "https://dup.ru", "ниша", "описание", projects_dir=projects_dir)


def test_list_projects_empty(projects_dir: Path):
    result = list_projects(projects_dir=projects_dir)
    assert result == []


def test_list_projects(projects_dir: Path):
    create_project("alpha", "https://a.ru", "a", "a", projects_dir=projects_dir)
    create_project("beta", "https://b.ru", "b", "b", projects_dir=projects_dir)
    result = list_projects(projects_dir=projects_dir)
    names = [p["name"] for p in result]
    assert "alpha" in names
    assert "beta" in names


def test_get_project(projects_dir: Path):
    create_project("proj", "https://p.ru", "n", "d", projects_dir=projects_dir)
    result = get_project("proj", projects_dir=projects_dir)
    assert result["name"] == "proj"
    assert result["url"] == "https://p.ru"


def test_get_nonexistent_project(projects_dir: Path):
    with pytest.raises(FileNotFoundError, match="не найден"):
        get_project("ghost", projects_dir=projects_dir)


def test_update_project(projects_dir: Path):
    create_project("upd", "https://u.ru", "n", "d", projects_dir=projects_dir)
    result = update_project("upd", "tone_of_voice", "формальный, на вы", projects_dir=projects_dir)
    assert result["tone_of_voice"] == "формальный, на вы"

    reloaded = get_project("upd", projects_dir=projects_dir)
    assert reloaded["tone_of_voice"] == "формальный, на вы"


def test_update_nested_field(projects_dir: Path):
    create_project("nested", "https://n.ru", "n", "d", projects_dir=projects_dir)
    result = update_project(
        "nested", "social.telegram_channel", "@new_channel",
        projects_dir=projects_dir,
    )
    assert result["social"]["telegram_channel"] == "@new_channel"


def test_delete_project(projects_dir: Path):
    create_project("del-me", "https://d.ru", "n", "d", projects_dir=projects_dir)
    delete_project("del-me", projects_dir=projects_dir)
    assert not (projects_dir / "del-me.yaml").exists()


def test_delete_nonexistent_project(projects_dir: Path):
    with pytest.raises(FileNotFoundError, match="не найден"):
        delete_project("ghost", projects_dir=projects_dir)


@pytest.mark.parametrize("bad_name", [
    "../../etc/passwd",
    "../escape",
    "/absolute",
    "has spaces",
    "UPPERCASE",
    "",
    ".hidden",
    "a" * 64,
])
def test_reject_invalid_project_names(projects_dir: Path, bad_name: str):
    with pytest.raises(ValueError, match="Недопустимое имя"):
        create_project(bad_name, "https://x.ru", "n", "d", projects_dir=projects_dir)
