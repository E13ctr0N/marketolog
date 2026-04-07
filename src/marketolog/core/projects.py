"""CRUD operations for project YAML files.

Storage: ~/.marketolog/projects/<name>.yaml
"""

from pathlib import Path

import yaml

DEFAULT_PROJECTS_DIR = Path.home() / ".marketolog" / "projects"

PROJECT_TEMPLATE = {
    "target_audience": [],
    "competitors": [],
    "tone_of_voice": "дружелюбный, без канцелярита",
    "social": {
        "telegram_channel": "",
        "telegram_dzen_channel": "",
        "vk_group": "",
        "max_channel": "",
    },
    "seo": {
        "main_keywords": [],
        "yandex_metrika_id": "",
        "webmaster_host": "",
        "search_console_url": "",
    },
}


def _project_path(name: str, projects_dir: Path) -> Path:
    return projects_dir / f"{name}.yaml"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _save_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def create_project(
    name: str,
    url: str,
    niche: str,
    description: str,
    *,
    projects_dir: Path = DEFAULT_PROJECTS_DIR,
) -> dict:
    """Create a new project YAML file. Raises ValueError if exists."""
    path = _project_path(name, projects_dir)
    if path.exists():
        raise ValueError(f"Проект '{name}' уже существует")

    data = {
        "name": name,
        "url": url,
        "niche": niche,
        "description": description,
        **{k: (v.copy() if isinstance(v, (dict, list)) else v) for k, v in PROJECT_TEMPLATE.items()},
    }
    _save_yaml(path, data)
    return data


def list_projects(*, projects_dir: Path = DEFAULT_PROJECTS_DIR) -> list[dict]:
    """List all projects (name + url + niche)."""
    if not projects_dir.exists():
        return []
    results = []
    for path in sorted(projects_dir.glob("*.yaml")):
        data = _load_yaml(path)
        results.append({
            "name": data.get("name", path.stem),
            "url": data.get("url", ""),
            "niche": data.get("niche", ""),
        })
    return results


def get_project(name: str, *, projects_dir: Path = DEFAULT_PROJECTS_DIR) -> dict:
    """Get full project data. Raises FileNotFoundError if missing."""
    path = _project_path(name, projects_dir)
    if not path.exists():
        raise FileNotFoundError(f"Проект '{name}' не найден")
    return _load_yaml(path)


def update_project(
    name: str,
    field: str,
    value: str,
    *,
    projects_dir: Path = DEFAULT_PROJECTS_DIR,
) -> dict:
    """Update a project field (supports dot notation: 'social.telegram_channel')."""
    path = _project_path(name, projects_dir)
    if not path.exists():
        raise FileNotFoundError(f"Проект '{name}' не найден")

    data = _load_yaml(path)

    parts = field.split(".")
    target = data
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value

    _save_yaml(path, data)
    return data


def delete_project(name: str, *, projects_dir: Path = DEFAULT_PROJECTS_DIR) -> None:
    """Delete project YAML file. Raises FileNotFoundError if missing."""
    path = _project_path(name, projects_dir)
    if not path.exists():
        raise FileNotFoundError(f"Проект '{name}' не найден")
    path.unlink()
