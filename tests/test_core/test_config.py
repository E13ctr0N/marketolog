from pathlib import Path

import pytest
import yaml

from marketolog.core.config import MarketologConfig, load_config


def test_load_config_from_env(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("YANDEX_OAUTH_TOKEN", "env-token-123")
    monkeypatch.setenv("VK_API_TOKEN", "vk-token-456")
    config = load_config(config_dir=tmp_path)
    assert config.yandex_oauth_token == "env-token-123"
    assert config.vk_api_token == "vk-token-456"
    assert config.telegram_bot_token is None


def test_load_config_from_yaml(tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        yaml.dump({
            "yandex_oauth_token": "yaml-token-789",
            "exa_api_key": "exa-key-000",
        }),
        encoding="utf-8",
    )
    config = load_config(config_dir=tmp_path)
    assert config.yandex_oauth_token == "yaml-token-789"
    assert config.exa_api_key == "exa-key-000"


def test_env_overrides_yaml(monkeypatch, tmp_path: Path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        yaml.dump({"yandex_oauth_token": "yaml-token"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("YANDEX_OAUTH_TOKEN", "env-token")
    config = load_config(config_dir=tmp_path)
    assert config.yandex_oauth_token == "env-token"


def test_load_config_no_file_no_env(tmp_path: Path):
    config = load_config(config_dir=tmp_path)
    assert config.yandex_oauth_token is None
    assert config.vk_api_token is None


def test_config_has_all_fields():
    config = MarketologConfig()
    expected_fields = {
        "yandex_oauth_token", "yandex_wordstat_token",
        "yandex_search_api_key", "yandex_folder_id",
        "yandex_metrika_counter", "vk_api_token",
        "telegram_bot_token", "max_bot_token",
        "google_sc_credentials", "exa_api_key", "pagespeed_api_key",
    }
    assert set(config.__dataclass_fields__.keys()) == expected_fields


def test_config_is_configured(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("YANDEX_OAUTH_TOKEN", "token")
    config = load_config(config_dir=tmp_path)
    assert config.is_configured("yandex_oauth_token") is True
    assert config.is_configured("vk_api_token") is False
