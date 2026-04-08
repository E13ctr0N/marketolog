from pathlib import Path

import pytest

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache


@pytest.fixture
def config_with_keys() -> MarketologConfig:
    """Config with Exa API key set."""
    return MarketologConfig(
        exa_api_key="test-exa-key",
        yandex_oauth_token="test-yandex-token",
        yandex_metrika_counter="12345678",
    )


@pytest.fixture
def config_no_keys() -> MarketologConfig:
    """Config with no API keys."""
    return MarketologConfig()


@pytest.fixture
def cache(tmp_path: Path) -> FileCache:
    return FileCache(base_dir=tmp_path / "cache")


@pytest.fixture
def project_context() -> dict:
    """Rich project context for strategy tools."""
    return {
        "name": "test-saas",
        "url": "https://my-saas.ru",
        "niche": "управление проектами",
        "description": "Таск-трекер для малых команд",
        "tone_of_voice": "дружелюбный, без канцелярита, на ты",
        "target_audience": [
            {
                "segment": "фрилансеры",
                "pain": "хаос в задачах, забытые дедлайны",
            },
            {
                "segment": "малые команды (3-10 человек)",
                "pain": "нет прозрачности, кто что делает",
            },
        ],
        "competitors": [
            {"name": "Trello", "url": "https://trello.com"},
            {"name": "Яндекс.Трекер", "url": "https://tracker.yandex.ru"},
        ],
        "social": {
            "telegram_channel": "@mysaas_channel",
            "vk_group": "mysaas",
            "max_channel": "",
            "telegram_dzen_channel": "",
        },
        "seo": {
            "main_keywords": ["таск-трекер", "управление задачами", "канбан"],
        },
    }
