"""Token management and OAuth flow helpers.

Tokens stored in ~/.marketolog/config.yaml as alternative to env vars.
"""

import os
from pathlib import Path

import yaml

from marketolog.core.config import ENV_MAP, DEFAULT_CONFIG_DIR


def save_token(field_name: str, token: str, *, config_dir: Path = DEFAULT_CONFIG_DIR) -> None:
    """Save a token to config.yaml (merges with existing)."""
    config_file = config_dir / "config.yaml"
    config_dir.mkdir(parents=True, exist_ok=True)

    existing: dict = {}
    if config_file.exists():
        existing = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}

    existing[field_name] = token
    config_file.write_text(yaml.dump(existing, allow_unicode=True), encoding="utf-8")


def load_tokens(*, config_dir: Path = DEFAULT_CONFIG_DIR) -> dict[str, str]:
    """Load all tokens from config.yaml."""
    config_file = config_dir / "config.yaml"
    if not config_file.exists():
        return {}
    data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
    return {k: v for k, v in data.items() if v}


def get_auth_status(*, config_dir: Path = DEFAULT_CONFIG_DIR) -> dict[str, str]:
    """Check status of all credentials: 'env', 'config.yaml', or 'не настроен'."""
    tokens = load_tokens(config_dir=config_dir)
    status: dict[str, str] = {}

    for field_name, env_name in ENV_MAP.items():
        if os.environ.get(env_name):
            status[field_name] = "env"
        elif field_name in tokens:
            status[field_name] = "config.yaml"
        else:
            status[field_name] = "не настроен"

    return status


def get_oauth_url(service: str, *, client_id: str) -> str:
    """Generate OAuth authorization URL for a service."""
    base = "https://oauth.yandex.ru/authorize"
    return f"{base}?response_type=token&client_id={client_id}"
