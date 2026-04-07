"""Configuration loading from env vars and ~/.marketolog/config.yaml.

Priority: env vars > config.yaml > None.
"""

import os
from dataclasses import dataclass, fields
from pathlib import Path

import yaml

DEFAULT_CONFIG_DIR = Path.home() / ".marketolog"

ENV_MAP = {
    "yandex_oauth_token": "YANDEX_OAUTH_TOKEN",
    "yandex_wordstat_token": "YANDEX_WORDSTAT_TOKEN",
    "yandex_search_api_key": "YANDEX_SEARCH_API_KEY",
    "yandex_folder_id": "YANDEX_FOLDER_ID",
    "yandex_metrika_counter": "YANDEX_METRIKA_COUNTER",
    "vk_api_token": "VK_API_TOKEN",
    "telegram_bot_token": "TELEGRAM_BOT_TOKEN",
    "max_bot_token": "MAX_BOT_TOKEN",
    "google_sc_credentials": "GOOGLE_SC_CREDENTIALS",
    "exa_api_key": "EXA_API_KEY",
    "pagespeed_api_key": "PAGESPEED_API_KEY",
}


@dataclass
class MarketologConfig:
    """All optional API credentials and settings."""

    yandex_oauth_token: str | None = None
    yandex_wordstat_token: str | None = None
    yandex_search_api_key: str | None = None
    yandex_folder_id: str | None = None
    yandex_metrika_counter: str | None = None
    vk_api_token: str | None = None
    telegram_bot_token: str | None = None
    max_bot_token: str | None = None
    google_sc_credentials: str | None = None
    exa_api_key: str | None = None
    pagespeed_api_key: str | None = None

    def is_configured(self, field_name: str) -> bool:
        """Check if a specific credential is set."""
        return getattr(self, field_name, None) is not None


def load_config(config_dir: Path = DEFAULT_CONFIG_DIR) -> MarketologConfig:
    """Load config: YAML first, then env vars override."""
    values: dict[str, str | None] = {}

    config_file = config_dir / "config.yaml"
    if config_file.exists():
        try:
            yaml_data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
            for field_name in ENV_MAP:
                if field_name in yaml_data and yaml_data[field_name]:
                    values[field_name] = str(yaml_data[field_name])
        except (yaml.YAMLError, OSError):
            pass

    for field_name, env_name in ENV_MAP.items():
        env_val = os.environ.get(env_name)
        if env_val:
            values[field_name] = env_val

    return MarketologConfig(**values)
