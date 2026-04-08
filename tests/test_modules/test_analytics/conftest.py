from pathlib import Path

import pytest

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache


@pytest.fixture
def config_with_keys() -> MarketologConfig:
    """Config with all Analytics-related API keys set."""
    return MarketologConfig(
        yandex_oauth_token="test-yandex-token",
        yandex_metrika_counter="12345678",
        google_sc_credentials="/tmp/fake-sa.json",
    )


@pytest.fixture
def config_no_keys() -> MarketologConfig:
    """Config with no API keys — for graceful degradation tests."""
    return MarketologConfig()


@pytest.fixture
def cache(tmp_path: Path) -> FileCache:
    return FileCache(base_dir=tmp_path / "cache")


@pytest.fixture
def project_context() -> dict:
    """Minimal project context for analytics tools."""
    return {
        "name": "test-project",
        "url": "https://example.ru",
        "niche": "тестирование",
        "seo": {
            "main_keywords": ["таск трекер", "управление задачами"],
            "yandex_metrika_id": "12345678",
            "search_console_url": "https://example.ru",
        },
        "competitors": [
            {"name": "Trello", "url": "https://trello.com"},
        ],
    }
