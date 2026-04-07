from pathlib import Path

import pytest

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache


@pytest.fixture
def config_with_keys() -> MarketologConfig:
    """Config with all SEO-related API keys set."""
    return MarketologConfig(
        yandex_oauth_token="test-yandex-token",
        yandex_wordstat_token="test-wordstat-token",
        yandex_search_api_key="test-search-key",
        yandex_folder_id="test-folder-id",
        pagespeed_api_key="test-pagespeed-key",
        exa_api_key="test-exa-key",
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
    """Minimal project context for SEO tools."""
    return {
        "name": "test-project",
        "url": "https://example.ru",
        "niche": "тестирование",
        "seo": {
            "main_keywords": ["таск трекер", "управление задачами"],
            "webmaster_host": "https://example.ru",
        },
        "competitors": [
            {"name": "Trello", "url": "https://trello.com"},
        ],
    }
