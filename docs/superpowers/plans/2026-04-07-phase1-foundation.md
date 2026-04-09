# Phase 1: Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the core infrastructure — project management, MCP server, utilities, prompts, CLI with OAuth — so that subsequent phases (SEO, Analytics, Content, SMM, Strategy) can register their tools into a working server.

**Architecture:** Single FastMCP 3.0+ server (`server.py`) registers tools from internal modules. Core module provides CRUD for YAML-based project files in `~/.marketolog/projects/`. Utils provide shared infrastructure: file-based TTL cache, HTTP retry, CSV formatting, auth. CLI entry point supports both MCP server mode and `auth` subcommands. Prompts are loaded as MCP resources.

**Tech Stack:** Python 3.11+, FastMCP 3.0+, httpx, pyyaml, pydantic, pytest, pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-04-07-marketolog-design.md`

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| Create | `pyproject.toml` | Package config, dependencies, extras (`[trends]`) |
| Create | `src/marketolog/__init__.py` | Package version |
| Create | `src/marketolog/__main__.py` | CLI entry: `python -m marketolog` (server or auth) |
| Create | `src/marketolog/server.py` | FastMCP server instance, Core tool registration |
| Create | `src/marketolog/core/__init__.py` | Core package |
| Create | `src/marketolog/core/config.py` | Load config from env vars + `~/.marketolog/config.yaml` |
| Create | `src/marketolog/core/projects.py` | CRUD for project YAML files |
| Create | `src/marketolog/core/context.py` | Active project state, context injection |
| Create | `src/marketolog/prompts/strategist.md` | Main strategist role prompt |
| Create | `src/marketolog/utils/__init__.py` | Utils package |
| Create | `src/marketolog/utils/formatting.py` | `format_tabular()` — list[dict] to CSV |
| Create | `src/marketolog/utils/http.py` | `fetch_with_retry()` — httpx + exponential backoff |
| Create | `src/marketolog/utils/cache.py` | File-based TTL cache |
| Create | `src/marketolog/utils/auth.py` | OAuth flow helpers, token storage |
| Create | `tests/conftest.py` | Shared fixtures (tmp dirs, mock projects) |
| Create | `tests/test_utils/test_formatting.py` | Tests for format_tabular |
| Create | `tests/test_utils/test_http.py` | Tests for fetch_with_retry |
| Create | `tests/test_utils/test_cache.py` | Tests for TTL cache |
| Create | `tests/test_core/test_config.py` | Tests for config loading |
| Create | `tests/test_core/test_projects.py` | Tests for project CRUD |
| Create | `tests/test_core/test_context.py` | Tests for active project context |
| Create | `tests/test_server.py` | Integration tests for MCP server + Core tools |
| Create | `.env.example` | Template for environment variables |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/marketolog/__init__.py`
- Create: `.env.example`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "marketolog"
version = "0.1.0"
description = "AI-маркетолог для бизнеса в Рунете — MCP-сервер для Claude"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=3.0",
    "httpx>=0.27",
    "pyyaml>=6.0",
    "pydantic>=2.0",
    "beautifulsoup4>=4.12",
    "lxml>=5.0",
]

[project.optional-dependencies]
trends = ["pytrends-modern>=0.2"]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "respx>=0.22",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create `src/marketolog/__init__.py`**

```python
"""Marketolog — AI-маркетолог для бизнеса в Рунете."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create `.env.example`**

```bash
# Яндекс API (OAuth-токены)
# YANDEX_OAUTH_TOKEN=        # Метрика + Вебмастер
# YANDEX_WORDSTAT_TOKEN=     # Wordstat API (отдельная заявка)
# YANDEX_SEARCH_API_KEY=     # Яндекс.Поиск API v2 (Yandex Cloud)
# YANDEX_FOLDER_ID=          # Folder ID (Yandex Cloud)
# YANDEX_METRIKA_COUNTER=    # ID счётчика Метрики

# Социальные сети
# VK_API_TOKEN=              # Токен сообщества VK
# TELEGRAM_BOT_TOKEN=        # Токен Telegram-бота
# MAX_BOT_TOKEN=             # Токен MAX-бота

# Google
# GOOGLE_SC_CREDENTIALS=     # Путь к service account JSON
# PAGESPEED_API_KEY=         # Увеличивает квоту (опционально)

# Другое
# EXA_API_KEY=               # Exa API (опционально)
```

- [ ] **Step 4: Create `tests/conftest.py`**

```python
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
```

- [ ] **Step 5: Create directory stubs**

```bash
mkdir -p src/marketolog/core
mkdir -p src/marketolog/modules
mkdir -p src/marketolog/prompts
mkdir -p src/marketolog/utils
mkdir -p tests/test_core
mkdir -p tests/test_utils
touch src/marketolog/core/__init__.py
touch src/marketolog/utils/__init__.py
touch src/marketolog/modules/__init__.py
```

- [ ] **Step 6: Install in dev mode and verify**

Run: `cd D:/AI/Marketolog && pip install -e ".[dev]"`
Expected: Successful install, `python -c "import marketolog; print(marketolog.__version__)"` prints `0.1.0`

- [ ] **Step 7: Commit**

```bash
git init
git add pyproject.toml src/ tests/conftest.py .env.example
git commit -m "feat: project scaffolding — pyproject.toml, package structure, test fixtures"
```

---

## Task 2: Utils — `format_tabular()`

**Files:**
- Create: `src/marketolog/utils/formatting.py`
- Create: `tests/test_utils/test_formatting.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_utils/test_formatting.py
from marketolog.utils.formatting import format_tabular


def test_format_tabular_basic():
    data = [
        {"keyword": "таск трекер", "volume": 1200, "position": 8},
        {"keyword": "управление задачами", "volume": 800, "position": 14},
    ]
    result = format_tabular(data)
    lines = result.strip().split("\n")
    assert lines[0] == "keyword,volume,position"
    assert lines[1] == "таск трекер,1200,8"
    assert lines[2] == "управление задачами,800,14"


def test_format_tabular_empty():
    assert format_tabular([]) == ""


def test_format_tabular_single_row():
    data = [{"name": "test", "value": 42}]
    result = format_tabular(data)
    assert result.strip() == "name,value\ntest,42"


def test_format_tabular_with_commas_in_values():
    data = [{"title": "Hello, world", "count": 1}]
    result = format_tabular(data)
    lines = result.strip().split("\n")
    assert lines[1] == '"Hello, world",1'


def test_format_tabular_with_none():
    data = [{"a": 1, "b": None}]
    result = format_tabular(data)
    lines = result.strip().split("\n")
    assert lines[1] == "1,"


def test_format_tabular_with_nested_dict():
    data = [{"name": "test", "meta": {"key": "val"}}]
    result = format_tabular(data)
    lines = result.strip().split("\n")
    # Nested dicts are JSON-serialized into cells
    assert '{"key": "val"}' in lines[1]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_utils/test_formatting.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'marketolog.utils.formatting'`

- [ ] **Step 3: Implement `format_tabular()`**

```python
# src/marketolog/utils/formatting.py
"""CSV formatting for tabular MCP tool responses.

Saves 40-60% of context tokens compared to JSON for tabular data.
"""

import csv
import io
import json


def format_tabular(data: list[dict]) -> str:
    """Convert list of dicts to CSV string.

    - Header from keys of first dict
    - None → empty string
    - Nested dicts/lists → JSON-serialized into cell
    - Strings with commas → quoted
    """
    if not data:
        return ""

    fieldnames = list(data[0].keys())
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(fieldnames)

    for row in data:
        cells = []
        for key in fieldnames:
            value = row.get(key)
            if value is None:
                cells.append("")
            elif isinstance(value, (dict, list)):
                cells.append(json.dumps(value, ensure_ascii=False))
            else:
                cells.append(value)
        writer.writerow(cells)

    return output.getvalue()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_utils/test_formatting.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/utils/formatting.py tests/test_utils/test_formatting.py
git commit -m "feat: add format_tabular() — CSV formatting for tool responses"
```

---

## Task 3: Utils — `fetch_with_retry()`

**Files:**
- Create: `src/marketolog/utils/http.py`
- Create: `tests/test_utils/test_http.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_utils/test_http.py
import httpx
import pytest
import respx

from marketolog.utils.http import fetch_with_retry


@respx.mock
@pytest.mark.asyncio
async def test_fetch_success():
    respx.get("https://api.example.com/data").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    response = await fetch_with_retry("https://api.example.com/data")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


@respx.mock
@pytest.mark.asyncio
async def test_fetch_retry_on_429():
    route = respx.get("https://api.example.com/data")
    route.side_effect = [
        httpx.Response(429, text="Rate limited"),
        httpx.Response(200, json={"ok": True}),
    ]
    response = await fetch_with_retry(
        "https://api.example.com/data", max_retries=3, base_delay=0.01
    )
    assert response.status_code == 200
    assert route.call_count == 2


@respx.mock
@pytest.mark.asyncio
async def test_fetch_retry_on_500():
    route = respx.get("https://api.example.com/data")
    route.side_effect = [
        httpx.Response(500, text="Server Error"),
        httpx.Response(500, text="Server Error"),
        httpx.Response(200, json={"ok": True}),
    ]
    response = await fetch_with_retry(
        "https://api.example.com/data", max_retries=3, base_delay=0.01
    )
    assert response.status_code == 200
    assert route.call_count == 3


@respx.mock
@pytest.mark.asyncio
async def test_fetch_exhausted_retries():
    respx.get("https://api.example.com/data").mock(
        return_value=httpx.Response(429, text="Rate limited")
    )
    response = await fetch_with_retry(
        "https://api.example.com/data", max_retries=2, base_delay=0.01
    )
    # After exhausting retries, returns the last response
    assert response.status_code == 429


@respx.mock
@pytest.mark.asyncio
async def test_fetch_no_retry_on_400():
    route = respx.get("https://api.example.com/data")
    route.mock(return_value=httpx.Response(400, text="Bad Request"))
    response = await fetch_with_retry(
        "https://api.example.com/data", max_retries=3, base_delay=0.01
    )
    assert response.status_code == 400
    assert route.call_count == 1  # No retry on 4xx (except 429)


@respx.mock
@pytest.mark.asyncio
async def test_fetch_post_with_headers():
    respx.post("https://api.example.com/data").mock(
        return_value=httpx.Response(200, json={"created": True})
    )
    response = await fetch_with_retry(
        "https://api.example.com/data",
        method="POST",
        headers={"Authorization": "Bearer token123"},
        json={"query": "test"},
    )
    assert response.status_code == 200
    assert response.json() == {"created": True}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_utils/test_http.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `fetch_with_retry()`**

```python
# src/marketolog/utils/http.py
"""HTTP client with automatic retry and exponential backoff."""

import asyncio
from typing import Any

import httpx

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


async def fetch_with_retry(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    json: Any = None,
    params: dict[str, Any] | None = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    timeout: float = 30.0,
) -> httpx.Response:
    """Make an HTTP request with exponential backoff retry on 429/5xx.

    Args:
        url: Request URL.
        method: HTTP method (GET, POST, etc.).
        headers: Optional request headers.
        json: Optional JSON body (for POST/PUT).
        params: Optional query parameters.
        max_retries: Maximum number of attempts (including first).
        base_delay: Initial delay in seconds (doubles each retry).
        timeout: Request timeout in seconds.

    Returns:
        httpx.Response — the last response (success or final failure).
    """
    last_response: httpx.Response | None = None

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(max_retries):
            last_response = await client.request(
                method,
                url,
                headers=headers,
                json=json,
                params=params,
            )

            if last_response.status_code not in RETRYABLE_STATUS_CODES:
                return last_response

            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)

    return last_response  # type: ignore[return-value]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_utils/test_http.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/utils/http.py tests/test_utils/test_http.py
git commit -m "feat: add fetch_with_retry() — HTTP with exponential backoff"
```

---

## Task 4: Utils — File-Based TTL Cache

**Files:**
- Create: `src/marketolog/utils/cache.py`
- Create: `tests/test_utils/test_cache.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_utils/test_cache.py
import json
import time
from pathlib import Path

import pytest

from marketolog.utils.cache import FileCache


@pytest.fixture
def cache(tmp_path: Path) -> FileCache:
    return FileCache(base_dir=tmp_path / "cache")


def test_cache_set_and_get(cache: FileCache):
    cache.set("seo", "audit_example.ru", {"score": 85}, ttl_seconds=3600)
    result = cache.get("seo", "audit_example.ru")
    assert result == {"score": 85}


def test_cache_miss(cache: FileCache):
    result = cache.get("seo", "nonexistent")
    assert result is None


def test_cache_expired(cache: FileCache):
    cache.set("seo", "audit_example.ru", {"score": 85}, ttl_seconds=0)
    time.sleep(0.05)
    result = cache.get("seo", "audit_example.ru")
    assert result is None


def test_cache_different_namespaces(cache: FileCache):
    cache.set("seo", "key1", {"a": 1}, ttl_seconds=3600)
    cache.set("metrika", "key1", {"b": 2}, ttl_seconds=3600)
    assert cache.get("seo", "key1") == {"a": 1}
    assert cache.get("metrika", "key1") == {"b": 2}


def test_cache_overwrite(cache: FileCache):
    cache.set("seo", "key1", {"old": True}, ttl_seconds=3600)
    cache.set("seo", "key1", {"new": True}, ttl_seconds=3600)
    assert cache.get("seo", "key1") == {"new": True}


def test_cache_clear_namespace(cache: FileCache):
    cache.set("seo", "key1", {"a": 1}, ttl_seconds=3600)
    cache.set("seo", "key2", {"b": 2}, ttl_seconds=3600)
    cache.set("metrika", "key1", {"c": 3}, ttl_seconds=3600)
    cache.clear("seo")
    assert cache.get("seo", "key1") is None
    assert cache.get("seo", "key2") is None
    assert cache.get("metrika", "key1") == {"c": 3}


def test_cache_creates_dirs(tmp_path: Path):
    cache = FileCache(base_dir=tmp_path / "deep" / "nested" / "cache")
    cache.set("ns", "key", {"x": 1}, ttl_seconds=3600)
    assert cache.get("ns", "key") == {"x": 1}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_utils/test_cache.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `FileCache`**

```python
# src/marketolog/utils/cache.py
"""File-based TTL cache.

Storage: ~/.marketolog/cache/<namespace>/<key_hash>.json
Each file contains: {"data": ..., "expires_at": <unix_timestamp>}
No external dependencies.
"""

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any


class FileCache:
    """Simple file-based cache with TTL per entry."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)

    def _key_path(self, namespace: str, key: str) -> Path:
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.base_dir / namespace / f"{key_hash}.json"

    def get(self, namespace: str, key: str) -> Any | None:
        """Return cached value or None if missing/expired."""
        path = self._key_path(namespace, key)
        if not path.exists():
            return None

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        if time.time() > raw.get("expires_at", 0):
            path.unlink(missing_ok=True)
            return None

        return raw.get("data")

    def set(self, namespace: str, key: str, data: Any, *, ttl_seconds: int) -> None:
        """Store value with TTL."""
        path = self._key_path(namespace, key)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "data": data,
            "expires_at": time.time() + ttl_seconds,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def clear(self, namespace: str) -> None:
        """Remove all entries in a namespace."""
        ns_dir = self.base_dir / namespace
        if ns_dir.exists():
            shutil.rmtree(ns_dir)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_utils/test_cache.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/utils/cache.py tests/test_utils/test_cache.py
git commit -m "feat: add FileCache — file-based TTL cache"
```

---

## Task 5: Core — Config

**Files:**
- Create: `src/marketolog/core/config.py`
- Create: `tests/test_core/test_config.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_core/test_config.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_core/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement config**

```python
# src/marketolog/core/config.py
"""Configuration loading from env vars and ~/.marketolog/config.yaml.

Priority: env vars > config.yaml > None.
"""

import os
from dataclasses import dataclass, fields
from pathlib import Path

import yaml

DEFAULT_CONFIG_DIR = Path.home() / ".marketolog"

# Maps dataclass field names to env var names
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

    # Layer 1: YAML file
    config_file = config_dir / "config.yaml"
    if config_file.exists():
        try:
            yaml_data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
            for field_name in ENV_MAP:
                if field_name in yaml_data and yaml_data[field_name]:
                    values[field_name] = str(yaml_data[field_name])
        except (yaml.YAMLError, OSError):
            pass

    # Layer 2: Env vars override YAML
    for field_name, env_name in ENV_MAP.items():
        env_val = os.environ.get(env_name)
        if env_val:
            values[field_name] = env_val

    return MarketologConfig(**values)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_core/test_config.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/core/config.py tests/test_core/test_config.py
git commit -m "feat: add config loading — env vars + YAML with priority"
```

---

## Task 6: Core — Projects CRUD

**Files:**
- Create: `src/marketolog/core/projects.py`
- Create: `tests/test_core/test_projects.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_core/test_projects.py
from pathlib import Path

import pytest
import yaml

from marketolog.core.projects import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)


@pytest.fixture
def projects_dir(tmp_marketolog_dir: Path) -> Path:
    return tmp_marketolog_dir / "projects"


def test_create_project(projects_dir: Path):
    result = create_project(
        name="my-saas",
        url="https://my-saas.ru",
        niche="управление проектами",
        description="Таск-трекер для малых команд",
        projects_dir=projects_dir,
    )
    assert result["name"] == "my-saas"
    assert (projects_dir / "my-saas.yaml").exists()

    data = yaml.safe_load((projects_dir / "my-saas.yaml").read_text(encoding="utf-8"))
    assert data["url"] == "https://my-saas.ru"
    assert data["niche"] == "управление проектами"
    assert "target_audience" in data
    assert "social" in data
    assert "seo" in data


def test_create_duplicate_project(projects_dir: Path):
    create_project("dup", "https://dup.ru", "ниша", "описание", projects_dir=projects_dir)
    with pytest.raises(ValueError, match="уже существует"):
        create_project("dup", "https://dup.ru", "ниша", "описание", projects_dir=projects_dir)


def test_list_projects_empty(projects_dir: Path):
    result = list_projects(projects_dir=projects_dir)
    assert result == []


def test_list_projects(projects_dir: Path):
    create_project("alpha", "https://a.ru", "a", "a", projects_dir=projects_dir)
    create_project("beta", "https://b.ru", "b", "b", projects_dir=projects_dir)
    result = list_projects(projects_dir=projects_dir)
    names = [p["name"] for p in result]
    assert "alpha" in names
    assert "beta" in names


def test_get_project(projects_dir: Path):
    create_project("proj", "https://p.ru", "n", "d", projects_dir=projects_dir)
    result = get_project("proj", projects_dir=projects_dir)
    assert result["name"] == "proj"
    assert result["url"] == "https://p.ru"


def test_get_nonexistent_project(projects_dir: Path):
    with pytest.raises(FileNotFoundError, match="не найден"):
        get_project("ghost", projects_dir=projects_dir)


def test_update_project(projects_dir: Path):
    create_project("upd", "https://u.ru", "n", "d", projects_dir=projects_dir)
    result = update_project("upd", "tone_of_voice", "формальный, на вы", projects_dir=projects_dir)
    assert result["tone_of_voice"] == "формальный, на вы"

    reloaded = get_project("upd", projects_dir=projects_dir)
    assert reloaded["tone_of_voice"] == "формальный, на вы"


def test_update_nested_field(projects_dir: Path):
    create_project("nested", "https://n.ru", "n", "d", projects_dir=projects_dir)
    result = update_project(
        "nested", "social.telegram_channel", "@new_channel",
        projects_dir=projects_dir,
    )
    assert result["social"]["telegram_channel"] == "@new_channel"


def test_delete_project(projects_dir: Path):
    create_project("del-me", "https://d.ru", "n", "d", projects_dir=projects_dir)
    delete_project("del-me", projects_dir=projects_dir)
    assert not (projects_dir / "del-me.yaml").exists()


def test_delete_nonexistent_project(projects_dir: Path):
    with pytest.raises(FileNotFoundError, match="не найден"):
        delete_project("ghost", projects_dir=projects_dir)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_core/test_projects.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement projects CRUD**

```python
# src/marketolog/core/projects.py
"""CRUD operations for project YAML files.

Storage: ~/.marketolog/projects/<name>.yaml
"""

from pathlib import Path

import yaml

DEFAULT_PROJECTS_DIR = Path.home() / ".marketolog" / "projects"

PROJECT_TEMPLATE = {
    "target_audience": [],
    "competitors": [],
    "tone_of_voice": "дружелюбный, без канцелярита",
    "social": {
        "telegram_channel": "",
        "telegram_dzen_channel": "",
        "vk_group": "",
        "max_channel": "",
    },
    "seo": {
        "main_keywords": [],
        "yandex_metrika_id": "",
        "webmaster_host": "",
        "search_console_url": "",
    },
}


def _project_path(name: str, projects_dir: Path) -> Path:
    return projects_dir / f"{name}.yaml"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _save_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def create_project(
    name: str,
    url: str,
    niche: str,
    description: str,
    *,
    projects_dir: Path = DEFAULT_PROJECTS_DIR,
) -> dict:
    """Create a new project YAML file. Raises ValueError if exists."""
    path = _project_path(name, projects_dir)
    if path.exists():
        raise ValueError(f"Проект '{name}' уже существует")

    data = {
        "name": name,
        "url": url,
        "niche": niche,
        "description": description,
        **{k: (v.copy() if isinstance(v, (dict, list)) else v) for k, v in PROJECT_TEMPLATE.items()},
    }
    _save_yaml(path, data)
    return data


def list_projects(*, projects_dir: Path = DEFAULT_PROJECTS_DIR) -> list[dict]:
    """List all projects (name + url + niche)."""
    if not projects_dir.exists():
        return []
    results = []
    for path in sorted(projects_dir.glob("*.yaml")):
        data = _load_yaml(path)
        results.append({
            "name": data.get("name", path.stem),
            "url": data.get("url", ""),
            "niche": data.get("niche", ""),
        })
    return results


def get_project(name: str, *, projects_dir: Path = DEFAULT_PROJECTS_DIR) -> dict:
    """Get full project data. Raises FileNotFoundError if missing."""
    path = _project_path(name, projects_dir)
    if not path.exists():
        raise FileNotFoundError(f"Проект '{name}' не найден")
    return _load_yaml(path)


def update_project(
    name: str,
    field: str,
    value: str,
    *,
    projects_dir: Path = DEFAULT_PROJECTS_DIR,
) -> dict:
    """Update a project field (supports dot notation: 'social.telegram_channel')."""
    path = _project_path(name, projects_dir)
    if not path.exists():
        raise FileNotFoundError(f"Проект '{name}' не найден")

    data = _load_yaml(path)

    parts = field.split(".")
    target = data
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value

    _save_yaml(path, data)
    return data


def delete_project(name: str, *, projects_dir: Path = DEFAULT_PROJECTS_DIR) -> None:
    """Delete project YAML file. Raises FileNotFoundError if missing."""
    path = _project_path(name, projects_dir)
    if not path.exists():
        raise FileNotFoundError(f"Проект '{name}' не найден")
    path.unlink()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_core/test_projects.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/core/projects.py tests/test_core/test_projects.py
git commit -m "feat: add project CRUD — create, list, get, update, delete"
```

---

## Task 7: Core — Active Project Context

**Files:**
- Create: `src/marketolog/core/context.py`
- Create: `tests/test_core/test_context.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_core/test_context.py
from pathlib import Path

import pytest

from marketolog.core.context import ProjectContext
from marketolog.core.projects import create_project


@pytest.fixture
def ctx(tmp_marketolog_dir: Path) -> ProjectContext:
    projects_dir = tmp_marketolog_dir / "projects"
    create_project("alpha", "https://a.ru", "ниша A", "Проект A", projects_dir=projects_dir)
    create_project("beta", "https://b.ru", "ниша B", "Проект B", projects_dir=projects_dir)
    return ProjectContext(projects_dir=projects_dir)


def test_no_active_project(ctx: ProjectContext):
    assert ctx.active_project is None


def test_switch_project(ctx: ProjectContext):
    ctx.switch("alpha")
    assert ctx.active_project is not None
    assert ctx.active_project["name"] == "alpha"


def test_switch_to_nonexistent(ctx: ProjectContext):
    with pytest.raises(FileNotFoundError, match="не найден"):
        ctx.switch("ghost")


def test_get_context_no_active(ctx: ProjectContext):
    with pytest.raises(RuntimeError, match="Нет активного проекта"):
        ctx.get_context()


def test_get_context(ctx: ProjectContext):
    ctx.switch("alpha")
    context = ctx.get_context()
    assert context["name"] == "alpha"
    assert context["url"] == "https://a.ru"


def test_switch_reloads(ctx: ProjectContext):
    ctx.switch("alpha")
    assert ctx.active_project["niche"] == "ниша A"
    ctx.switch("beta")
    assert ctx.active_project["niche"] == "ниша B"


def test_refresh_reloads_from_disk(ctx: ProjectContext):
    ctx.switch("alpha")
    # Simulate external update
    from marketolog.core.projects import update_project
    update_project("alpha", "niche", "обновлённая ниша", projects_dir=ctx.projects_dir)
    ctx.refresh()
    assert ctx.active_project["niche"] == "обновлённая ниша"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_core/test_context.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement ProjectContext**

```python
# src/marketolog/core/context.py
"""Active project state management."""

from pathlib import Path

from marketolog.core.projects import DEFAULT_PROJECTS_DIR, get_project


class ProjectContext:
    """Tracks the currently active project and provides its context to tools."""

    def __init__(self, *, projects_dir: Path = DEFAULT_PROJECTS_DIR) -> None:
        self.projects_dir = projects_dir
        self.active_project: dict | None = None
        self._active_name: str | None = None

    def switch(self, name: str) -> dict:
        """Switch active project. Raises FileNotFoundError if missing."""
        data = get_project(name, projects_dir=self.projects_dir)
        self.active_project = data
        self._active_name = name
        return data

    def get_context(self) -> dict:
        """Return full context of active project. Raises RuntimeError if none."""
        if self.active_project is None:
            raise RuntimeError("Нет активного проекта. Используйте switch_project.")
        return self.active_project

    def refresh(self) -> None:
        """Reload active project data from disk."""
        if self._active_name is not None:
            self.active_project = get_project(
                self._active_name, projects_dir=self.projects_dir
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_core/test_context.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/core/context.py tests/test_core/test_context.py
git commit -m "feat: add ProjectContext — active project state management"
```

---

## Task 8: Strategist Prompt

**Files:**
- Create: `src/marketolog/prompts/strategist.md`

- [ ] **Step 1: Create the strategist prompt**

```markdown
# Маркетолог-стратег

Ты — опытный маркетолог для бизнеса в Рунете. Твоя задача — анализировать проекты, предлагать стратегию продвижения и выполнять задачи после одобрения пользователя.

## Принципы работы

1. **Всегда начинай с контекста** — вызови `get_project_context()`, чтобы понять проект
2. **Предлагай, не делай** — сначала план действий, потом ждёшь одобрения
3. **Данные, а не догадки** — каждая рекомендация подкреплена данными из инструментов
4. **Простой язык** — говори понятно, без маркетингового жаргона
5. **Максимум результата при минимуме затрат** — приоритизируй действия по ROI

## Алгоритм работы

1. Получи контекст проекта (`get_project_context()`)
2. Определи текущую ситуацию (что уже сделано, где проблемы)
3. Предложи 2-3 приоритетных действия с обоснованием
4. Дождись одобрения пользователя
5. Выполни через инструменты
6. Отчитайся о результатах

## Адаптация под масштаб

Подстраивай рекомендации под проект:
- **Стартап без бюджета** — бесплатные каналы, органика, контент-маркетинг
- **Растущий бизнес** — SEO + контент + соцсети, тестирование каналов
- **Зрелый бизнес** — оптимизация воронки, аналитика, масштабирование каналов

## Платформы Рунета

- **Яндекс** — основная поисковая система (~65% поискового трафика в РФ)
- **VK** — основная социальная сеть
- **Telegram** — каналы и боты, растущий канал
- **MAX** — новый мессенджер, ранний доступ = преимущество
- **Дзен** — контент-платформа, хорошо для SEO и охвата

## Если нет данных

Когда инструмент недоступен (API-ключ не настроен), не останавливайся — предложи альтернативу или объясни, как настроить.
```

- [ ] **Step 2: Commit**

```bash
git add src/marketolog/prompts/strategist.md
git commit -m "feat: add strategist prompt — main role definition"
```

---

## Task 9: MCP Server + Core Tools Registration

**Files:**
- Create: `src/marketolog/server.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Write the failing integration tests**

```python
# tests/test_server.py
import pytest
from pathlib import Path

from marketolog.server import create_server


@pytest.fixture
def server(tmp_marketolog_dir: Path):
    return create_server(base_dir=tmp_marketolog_dir)


def test_server_has_core_tools(server):
    """Server must expose all 6 Core tools."""
    tool_names = {t.name for t in server._tool_manager.list_tools()}
    expected = {
        "create_project", "switch_project", "list_projects",
        "update_project", "delete_project", "get_project_context",
    }
    assert expected.issubset(tool_names), f"Missing tools: {expected - tool_names}"


def test_server_has_strategist_resource(server):
    """Server must expose strategist prompt as a resource."""
    resources = server._resource_manager.list_resources()
    resource_uris = {str(r.uri) for r in resources}
    assert any("strategist" in uri for uri in resource_uris), (
        f"No strategist resource found. Resources: {resource_uris}"
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_server.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `server.py`**

```python
# src/marketolog/server.py
"""FastMCP server — registers Core tools and prompt resources."""

from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from marketolog.core.config import load_config, MarketologConfig
from marketolog.core.context import ProjectContext
from marketolog.core.projects import (
    create_project as _create_project,
    delete_project as _delete_project,
    get_project,
    list_projects as _list_projects,
    update_project as _update_project,
)

READ_ONLY = ToolAnnotations(readOnlyHint=True)
MUTATING = ToolAnnotations(readOnlyHint=False)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True)

DEFAULT_BASE_DIR = Path.home() / ".marketolog"


def create_server(base_dir: Path = DEFAULT_BASE_DIR) -> FastMCP:
    """Create and configure the Marketolog MCP server."""
    mcp = FastMCP(
        "Marketolog",
        instructions="AI-маркетолог для бизнеса в Рунете. Начни с get_project_context().",
    )

    projects_dir = base_dir / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(config_dir=base_dir)
    ctx = ProjectContext(projects_dir=projects_dir)

    # --- Core Tools ---

    @mcp.tool(annotations=MUTATING)
    def create_project(
        name: Annotated[str, Field(description="Уникальное имя проекта (латиница, без пробелов)", examples=["my-saas"])],
        url: Annotated[str, Field(description="URL сайта проекта", examples=["https://my-saas.ru"])],
        niche: Annotated[str, Field(description="Ниша / тематика проекта", examples=["управление проектами"])],
        description: Annotated[str, Field(description="Краткое описание проекта", examples=["Таск-трекер для малых команд"])],
    ) -> str:
        """Создаёт новый проект. После создания используйте switch_project для активации."""
        result = _create_project(name, url, niche, description, projects_dir=projects_dir)
        return f"Проект '{name}' создан. Используйте switch_project('{name}') для активации."

    @mcp.tool(annotations=MUTATING)
    def switch_project(
        name: Annotated[str, Field(description="Имя проекта для активации")],
    ) -> str:
        """Переключает активный проект. Все инструменты будут работать в контексте этого проекта."""
        data = ctx.switch(name)
        return f"Активный проект: {data['name']} ({data['url']}), ниша: {data['niche']}"

    @mcp.tool(annotations=READ_ONLY)
    def list_projects() -> str:
        """Список всех проектов."""
        projects = _list_projects(projects_dir=projects_dir)
        if not projects:
            return "Нет проектов. Создайте первый через create_project()."
        lines = [f"- {p['name']}: {p['url']} ({p['niche']})" for p in projects]
        return "\n".join(lines)

    @mcp.tool(annotations=MUTATING)
    def update_project(
        field: Annotated[str, Field(
            description="Поле для обновления (поддерживает точечную нотацию: 'social.telegram_channel')",
            examples=["tone_of_voice", "social.vk_group", "seo.main_keywords"],
        )],
        value: Annotated[str, Field(description="Новое значение поля")],
    ) -> str:
        """Обновляет поле активного проекта."""
        context = ctx.get_context()
        name = context["name"]
        _update_project(name, field, value, projects_dir=projects_dir)
        ctx.refresh()
        return f"Обновлено: {field} = {value}"

    @mcp.tool(annotations=DESTRUCTIVE)
    def delete_project(
        name: Annotated[str, Field(description="Имя проекта для удаления")],
    ) -> str:
        """Удаляет проект (YAML-файл). Это действие необратимо."""
        _delete_project(name, projects_dir=projects_dir)
        if ctx._active_name == name:
            ctx.active_project = None
            ctx._active_name = None
        return f"Проект '{name}' удалён."

    @mcp.tool(annotations=READ_ONLY)
    def get_project_context() -> str:
        """Полный контекст активного проекта: ниша, ЦА, конкуренты, tone of voice, соцсети, SEO."""
        import yaml
        context = ctx.get_context()
        return yaml.dump(context, allow_unicode=True, sort_keys=False)

    # --- Prompt Resources ---

    prompts_dir = Path(__file__).parent / "prompts"

    @mcp.resource("marketolog://prompts/strategist")
    def strategist_prompt() -> str:
        """Основной промпт маркетолога-стратега."""
        return (prompts_dir / "strategist.md").read_text(encoding="utf-8")

    return mcp
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_server.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/server.py tests/test_server.py
git commit -m "feat: add MCP server with Core tools and strategist resource"
```

---

## Task 10: Utils — Auth (OAuth Flow Helpers)

**Files:**
- Create: `src/marketolog/utils/auth.py`
- Create: `tests/test_utils/test_auth.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_utils/test_auth.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_utils/test_auth.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement auth helpers**

```python
# src/marketolog/utils/auth.py
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
    """Generate OAuth authorization URL for a service.

    Args:
        service: 'yandex' or 'wordstat'
        client_id: Yandex OAuth application client ID
    """
    base = "https://oauth.yandex.ru/authorize"
    return f"{base}?response_type=token&client_id={client_id}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_utils/test_auth.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/utils/auth.py tests/test_utils/test_auth.py
git commit -m "feat: add auth helpers — token storage, status check, OAuth URL"
```

---

## Task 11: CLI Entry Point

**Files:**
- Create: `src/marketolog/__main__.py`

- [ ] **Step 1: Implement `__main__.py`**

```python
# src/marketolog/__main__.py
"""CLI entry point: python -m marketolog

Usage:
    python -m marketolog              — start MCP server
    python -m marketolog auth status  — show credentials status
    python -m marketolog auth yandex  — start OAuth flow for Yandex
"""

import sys


def run_auth(args: list[str]) -> None:
    """Handle `python -m marketolog auth <subcommand>`."""
    from marketolog.utils.auth import get_auth_status, get_oauth_url, save_token

    if not args:
        print("Использование: python -m marketolog auth <status|yandex|wordstat|vk|telegram|max>")
        sys.exit(1)

    subcommand = args[0]

    if subcommand == "status":
        status = get_auth_status()
        print("Статус подключений:\n")
        labels = {
            "yandex_oauth_token": "Яндекс (Метрика + Вебмастер)",
            "yandex_wordstat_token": "Яндекс Wordstat API",
            "yandex_search_api_key": "Яндекс Поиск API",
            "yandex_folder_id": "Yandex Cloud Folder ID",
            "yandex_metrika_counter": "Яндекс Метрика (счётчик)",
            "vk_api_token": "VK API",
            "telegram_bot_token": "Telegram Bot",
            "max_bot_token": "MAX Bot",
            "google_sc_credentials": "Google Search Console",
            "exa_api_key": "Exa API",
            "pagespeed_api_key": "PageSpeed API",
        }
        for field, label in labels.items():
            state = status.get(field, "не настроен")
            icon = "+" if state != "не настроен" else "-"
            print(f"  [{icon}] {label}: {state}")

    elif subcommand in ("yandex", "wordstat"):
        client_id = input("Введите Client ID приложения Яндекс OAuth: ").strip()
        if not client_id:
            print("Client ID не может быть пустым.")
            sys.exit(1)
        url = get_oauth_url(subcommand, client_id=client_id)
        print(f"\nОткройте в браузере:\n{url}\n")
        token = input("Вставьте полученный токен: ").strip()
        if not token:
            print("Токен не может быть пустым.")
            sys.exit(1)
        field = "yandex_oauth_token" if subcommand == "yandex" else "yandex_wordstat_token"
        save_token(field, token)
        print(f"Токен сохранён в ~/.marketolog/config.yaml ({field})")

    elif subcommand in ("vk", "telegram", "max"):
        field_map = {
            "vk": "vk_api_token",
            "telegram": "telegram_bot_token",
            "max": "max_bot_token",
        }
        token = input(f"Введите токен для {subcommand.upper()}: ").strip()
        if not token:
            print("Токен не может быть пустым.")
            sys.exit(1)
        save_token(field_map[subcommand], token)
        print(f"Токен сохранён в ~/.marketolog/config.yaml")

    else:
        print(f"Неизвестная команда: {subcommand}")
        print("Доступные: status, yandex, wordstat, vk, telegram, max")
        sys.exit(1)


def main() -> None:
    args = sys.argv[1:]

    if args and args[0] == "auth":
        run_auth(args[1:])
        return

    # Default: start MCP server
    from marketolog.server import create_server
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify server starts**

Run: `python -m marketolog auth status`
Expected: Prints credentials status table with all `[-]` (none configured)

- [ ] **Step 3: Commit**

```bash
git add src/marketolog/__main__.py
git commit -m "feat: add CLI entry point — MCP server + auth subcommands"
```

---

## Task 12: Scheduled Posts Queue (Startup Check)

**Files:**
- Modify: `src/marketolog/server.py`

- [ ] **Step 1: Add scheduled posts check on server start**

Add to `create_server()` in `server.py`, after tool registration:

```python
    # --- Scheduled Posts Check ---
    import logging
    import time

    logger = logging.getLogger("marketolog")
    scheduled_dir = base_dir / "scheduled"
    scheduled_dir.mkdir(parents=True, exist_ok=True)

    def _check_scheduled_posts() -> list[str]:
        """Check for pending scheduled posts at server startup."""
        notifications = []
        now = time.time()
        one_hour = 3600

        for path in sorted(scheduled_dir.glob("*.yaml")):
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                scheduled_at = data.get("scheduled_at", 0)

                if scheduled_at <= now:
                    overdue_seconds = now - scheduled_at
                    platform = data.get("platform", "unknown")
                    text_preview = data.get("text", "")[:50]

                    if overdue_seconds > one_hour:
                        notifications.append(
                            f"ПРОСРОЧЕН (>{int(overdue_seconds/60)} мин): "
                            f"{platform} — \"{text_preview}...\". Файл: {path.name}"
                        )
                    else:
                        notifications.append(
                            f"ГОТОВ к отправке: {platform} — \"{text_preview}...\". "
                            f"Файл: {path.name}"
                        )
            except Exception as e:
                logger.warning(f"Ошибка чтения {path}: {e}")

        return notifications

    # Run check at import time (server startup)
    pending = _check_scheduled_posts()
    if pending:
        logger.info("Отложенные посты:\n" + "\n".join(pending))
```

- [ ] **Step 2: Commit**

```bash
git add src/marketolog/server.py
git commit -m "feat: add scheduled posts queue check on server startup"
```

---

## Task 13: Full Integration Test

**Files:**
- Modify: `tests/test_server.py`

- [ ] **Step 1: Add end-to-end Core workflow test**

Append to `tests/test_server.py`:

```python
@pytest.mark.asyncio
async def test_core_workflow(server):
    """E2E: create → switch → context → update → list → delete."""
    from fastmcp import Client

    async with Client(server) as client:
        # Create
        result = await client.call_tool("create_project", {
            "name": "e2e-test",
            "url": "https://e2e.ru",
            "niche": "тестирование",
            "description": "E2E тест",
        })
        assert "создан" in result[0].text.lower()

        # Switch
        result = await client.call_tool("switch_project", {"name": "e2e-test"})
        assert "e2e-test" in result[0].text

        # Get context
        result = await client.call_tool("get_project_context", {})
        assert "e2e.ru" in result[0].text

        # Update
        result = await client.call_tool("update_project", {
            "field": "tone_of_voice",
            "value": "формальный",
        })
        assert "формальный" in result[0].text

        # List
        result = await client.call_tool("list_projects", {})
        assert "e2e-test" in result[0].text

        # Delete
        result = await client.call_tool("delete_project", {"name": "e2e-test"})
        assert "удалён" in result[0].text.lower()

        # Verify deleted
        result = await client.call_tool("list_projects", {})
        assert "e2e-test" not in result[0].text
```

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS (formatting: 6, http: 6, cache: 7, config: 6, projects: 10, context: 7, server: 3)

- [ ] **Step 3: Commit**

```bash
git add tests/test_server.py
git commit -m "test: add E2E integration test for Core workflow"
```

---

## Task 14: Final Verification

- [ ] **Step 1: Run complete test suite with coverage**

Run: `pytest tests/ -v --tb=short`
Expected: **45 tests PASS**, 0 failures

- [ ] **Step 2: Verify MCP server starts**

Run: `python -c "from marketolog.server import create_server; s = create_server(); print('OK:', len(s._tool_manager.list_tools()), 'tools')"`
Expected: `OK: 6 tools`

- [ ] **Step 3: Verify CLI auth status**

Run: `python -m marketolog auth status`
Expected: Prints table with 11 credentials, all `[-]`

- [ ] **Step 4: Final commit (if any uncommitted changes)**

```bash
git status
# If clean: done
# If changes: git add -A && git commit -m "chore: final cleanup for Phase 1"
```
