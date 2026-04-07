from pathlib import Path

import pytest
import yaml

from marketolog.utils.auth import save_token, load_tokens, get_auth_status


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_save_token(config_dir: Path):
    save_token("yandex_oauth_token", "test-token-123", config_dir=config_dir)
    config_file = config_dir / "config.yaml"
    assert config_file.exists()
    data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    assert data["yandex_oauth_token"] == "test-token-123"


def test_save_multiple_tokens(config_dir: Path):
    save_token("yandex_oauth_token", "ya-token", config_dir=config_dir)
    save_token("vk_api_token", "vk-token", config_dir=config_dir)
    data = yaml.safe_load((config_dir / "config.yaml").read_text(encoding="utf-8"))
    assert data["yandex_oauth_token"] == "ya-token"
    assert data["vk_api_token"] == "vk-token"


def test_load_tokens_empty(config_dir: Path):
    tokens = load_tokens(config_dir=config_dir)
    assert tokens == {}


def test_load_tokens(config_dir: Path):
    save_token("exa_api_key", "exa-123", config_dir=config_dir)
    tokens = load_tokens(config_dir=config_dir)
    assert tokens["exa_api_key"] == "exa-123"


def test_get_auth_status(config_dir: Path, monkeypatch):
    monkeypatch.setenv("VK_API_TOKEN", "vk-from-env")
    save_token("yandex_oauth_token", "ya-token", config_dir=config_dir)

    status = get_auth_status(config_dir=config_dir)
    assert status["yandex_oauth_token"] == "config.yaml"
    assert status["vk_api_token"] == "env"
    assert status["telegram_bot_token"] == "не настроен"


def test_get_auth_url_yandex():
    from marketolog.utils.auth import get_oauth_url
    url = get_oauth_url("yandex", client_id="test-id")
    assert "oauth.yandex.ru" in url
    assert "test-id" in url
