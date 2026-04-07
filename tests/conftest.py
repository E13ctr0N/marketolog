from pathlib import Path
import pytest
import yaml


@pytest.fixture
def tmp_marketolog_dir(tmp_path: Path) -> Path:
    """Create a temporary ~/.marketolog/ structure."""
    base = tmp_path / ".marketolog"
    (base / "projects").mkdir(parents=True)
    (base / "cache").mkdir()
    (base / "scheduled").mkdir()
    return base


@pytest.fixture
def sample_project_data() -> dict:
    """Minimal valid project data."""
    return {
        "name": "test-project",
        "url": "https://example.ru",
        "niche": "тестирование",
        "description": "Тестовый проект",
        "target_audience": [
            {"segment": "разработчики", "pain": "баги"}
        ],
        "competitors": [],
        "tone_of_voice": "дружелюбный",
        "social": {
            "telegram_channel": "@test_channel",
            "telegram_dzen_channel": "",
            "vk_group": "",
            "max_channel": "",
        },
        "seo": {
            "main_keywords": ["тестирование"],
            "yandex_metrika_id": "",
            "webmaster_host": "",
            "search_console_url": "",
        },
    }


@pytest.fixture
def sample_project_file(tmp_marketolog_dir: Path, sample_project_data: dict) -> Path:
    """Write sample project YAML and return its path."""
    path = tmp_marketolog_dir / "projects" / "test-project.yaml"
    path.write_text(yaml.dump(sample_project_data, allow_unicode=True), encoding="utf-8")
    return path
