from pathlib import Path

import pytest

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache


@pytest.fixture
def config_with_keys() -> MarketologConfig:
    """Config with all SMM-related API keys set."""
    return MarketologConfig(
        telegram_bot_token="123456:ABC-DEF-test-token",
        vk_api_token="test-vk-token",
        max_bot_token="test-max-token",
        exa_api_key="test-exa-key",
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
    """Minimal project context for SMM tools."""
    return {
        "name": "test-project",
        "url": "https://example.ru",
        "niche": "управление проектами",
        "tone_of_voice": "дружелюбный, без канцелярита, на ты",
        "social": {
            "telegram_channel": "@mysaas_channel",
            "telegram_dzen_channel": "@mysaas_dzen",
            "vk_group": "mysaas",
            "max_channel": "@mysaas_max",
        },
    }
