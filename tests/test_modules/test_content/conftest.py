from pathlib import Path

import pytest

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache


@pytest.fixture
def config_with_keys() -> MarketologConfig:
    return MarketologConfig(
        yandex_oauth_token="test-yandex-token",
        pagespeed_api_key="test-pagespeed-key",
        exa_api_key="test-exa-key",
    )


@pytest.fixture
def config_no_keys() -> MarketologConfig:
    return MarketologConfig()


@pytest.fixture
def cache(tmp_path: Path) -> FileCache:
    return FileCache(base_dir=tmp_path / "cache")


@pytest.fixture
def project_context() -> dict:
    return {
        "name": "test-project",
        "url": "https://example.ru",
        "niche": "управление проектами",
        "description": "Таск-трекер для малых команд",
        "tone_of_voice": "дружелюбный, без канцелярита, на ты",
        "target_audience": [
            {"segment": "фрилансеры", "pain": "хаос в задачах"},
            {"segment": "малые команды 3-10 чел", "pain": "нет единого места для задач"},
        ],
        "seo": {"main_keywords": ["таск трекер", "управление задачами"]},
        "competitors": [{"name": "Trello", "url": "https://trello.com"}],
        "social": {"telegram_channel": "@mysaas_channel", "vk_group": "mysaas"},
    }
