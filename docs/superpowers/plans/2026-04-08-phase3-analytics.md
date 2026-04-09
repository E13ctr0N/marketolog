# Phase 3: Analytics Module — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 8 Analytics tools to the Marketolog MCP server: Yandex Metrika reports/goals/funnel, Google Search Console, traffic sources, AI referral tracking, weekly digest, and UTM generation.

**Architecture:** Each tool lives in a focused module file under `src/marketolog/modules/analytics/`. All tools use the shared `FileCache`, `fetch_with_retry`, `format_tabular` utilities. Tools that need API credentials check `config.is_configured()` and return setup instructions when missing. All tools are `READ_ONLY` (no mutations). `generate_utm` is pure local logic; the rest call external APIs (Yandex Metrika, Google SC).

**Tech Stack:** Python 3.12, FastMCP, httpx, pytest + pytest-asyncio + respx for mocking

---

## File Structure

| File | Responsibility |
|---|---|
| `src/marketolog/modules/analytics/__init__.py` | Package marker |
| `src/marketolog/modules/analytics/utm.py` | `generate_utm()` — local UTM link builder |
| `src/marketolog/modules/analytics/metrika.py` | `run_metrika_report()`, `run_metrika_goals()` — Yandex Metrika API |
| `src/marketolog/modules/analytics/search_console.py` | `run_search_console_report()` — Google Search Console API |
| `src/marketolog/modules/analytics/traffic_sources.py` | `run_traffic_sources()` — combines Metrika + SC data |
| `src/marketolog/modules/analytics/funnel.py` | `run_funnel_analysis()` — Yandex Metrika goals/funnels |
| `src/marketolog/modules/analytics/ai_referral.py` | `run_ai_referral_report()` — AI search engine traffic |
| `src/marketolog/modules/analytics/digest.py` | `run_weekly_digest()` — aggregated weekly report |
| `src/marketolog/prompts/analyst.md` | Analyst role prompt |
| `src/marketolog/server.py` | Register 8 analytics tools + analyst resource |
| `tests/test_modules/test_analytics/conftest.py` | Shared fixtures for analytics tests |
| `tests/test_modules/test_analytics/test_utm.py` | Tests for generate_utm |
| `tests/test_modules/test_analytics/test_metrika.py` | Tests for metrika_report + metrika_goals |
| `tests/test_modules/test_analytics/test_search_console.py` | Tests for search_console_report |
| `tests/test_modules/test_analytics/test_traffic_sources.py` | Tests for traffic_sources |
| `tests/test_modules/test_analytics/test_funnel.py` | Tests for funnel_analysis |
| `tests/test_modules/test_analytics/test_ai_referral.py` | Tests for ai_referral_report |
| `tests/test_modules/test_analytics/test_digest.py` | Tests for weekly_digest |
| `tests/test_modules/test_analytics/test_integration.py` | Server integration: 22 tools, resources, annotations |

---

### Task 1: Package scaffolding + generate_utm

**Files:**
- Create: `src/marketolog/modules/analytics/__init__.py`
- Create: `src/marketolog/modules/analytics/utm.py`
- Create: `tests/test_modules/test_analytics/__init__.py`
- Create: `tests/test_modules/test_analytics/conftest.py`
- Create: `tests/test_modules/test_analytics/test_utm.py`

- [ ] **Step 1: Create package dirs and conftest**

```python
# src/marketolog/modules/analytics/__init__.py
"""Analytics module — Metrika, Search Console, traffic, funnels, digest."""
```

```python
# tests/test_modules/test_analytics/__init__.py
```

```python
# tests/test_modules/test_analytics/conftest.py
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
```

- [ ] **Step 2: Write failing tests for generate_utm**

```python
# tests/test_modules/test_analytics/test_utm.py
"""Tests for UTM link generator."""

from marketolog.modules.analytics.utm import generate_utm


def test_basic_utm():
    """Minimal required params: url, source, medium."""
    result = generate_utm(
        url="https://example.ru",
        source="telegram",
        medium="social",
    )
    assert result == "https://example.ru?utm_source=telegram&utm_medium=social"


def test_full_utm():
    """All UTM params provided."""
    result = generate_utm(
        url="https://example.ru/pricing",
        source="vk",
        medium="cpc",
        campaign="spring_sale",
        term="таск трекер",
        content="banner_top",
    )
    assert "utm_source=vk" in result
    assert "utm_medium=cpc" in result
    assert "utm_campaign=spring_sale" in result
    assert "utm_term=" in result  # URL-encoded cyrillic
    assert "utm_content=banner_top" in result
    assert result.startswith("https://example.ru/pricing?")


def test_utm_preserves_existing_query():
    """URL already has query params — UTM appended with &."""
    result = generate_utm(
        url="https://example.ru?ref=main",
        source="google",
        medium="organic",
    )
    assert "ref=main" in result
    assert "utm_source=google" in result
    assert result.count("?") == 1


def test_utm_encodes_cyrillic():
    """Cyrillic characters in term/content are URL-encoded."""
    result = generate_utm(
        url="https://example.ru",
        source="yandex",
        medium="cpc",
        term="управление задачами",
    )
    # Should be percent-encoded, not raw cyrillic in query
    assert "utm_term=" in result
    # Decoded form should match
    from urllib.parse import unquote
    assert "управление задачами" in unquote(result)


def test_utm_returns_markdown_block():
    """generate_utm returns a formatted string with the link and breakdown."""
    result = generate_utm(
        url="https://example.ru",
        source="telegram",
        medium="social",
        campaign="launch",
    )
    # Should contain the URL
    assert "https://example.ru" in result
    assert "utm_source=telegram" in result
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_analytics/test_utm.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'marketolog.modules.analytics.utm'`

- [ ] **Step 4: Implement generate_utm**

```python
# src/marketolog/modules/analytics/utm.py
"""UTM link generator — creates tagged URLs for campaign tracking."""

from urllib.parse import urlencode, urlparse, parse_qs, urlunparse, quote


def generate_utm(
    url: str,
    source: str,
    medium: str,
    campaign: str | None = None,
    term: str | None = None,
    content: str | None = None,
) -> str:
    """Generate a UTM-tagged URL.

    Args:
        url: Base URL to tag.
        source: Traffic source (e.g. "telegram", "vk", "yandex").
        medium: Marketing medium (e.g. "social", "cpc", "email").
        campaign: Campaign name (optional).
        term: Paid keyword (optional).
        content: Ad variation identifier (optional).

    Returns:
        Formatted string with UTM link and parameter breakdown.
    """
    parsed = urlparse(url)
    existing_params = parse_qs(parsed.query, keep_blank_values=True)

    utm_params: dict[str, str] = {
        "utm_source": source,
        "utm_medium": medium,
    }
    if campaign:
        utm_params["utm_campaign"] = campaign
    if term:
        utm_params["utm_term"] = term
    if content:
        utm_params["utm_content"] = content

    # Merge existing query params with UTM params
    merged: dict[str, str] = {}
    for k, v_list in existing_params.items():
        merged[k] = v_list[0] if v_list else ""
    merged.update(utm_params)

    new_query = urlencode(merged, quote_via=quote)
    tagged_url = urlunparse((
        parsed.scheme, parsed.netloc, parsed.path,
        parsed.params, new_query, parsed.fragment,
    ))

    # Build readable breakdown
    lines = [f"**UTM-ссылка:**\n`{tagged_url}`\n"]
    lines.append("**Параметры:**")
    for key, val in utm_params.items():
        lines.append(f"- {key} = {val}")

    return "\n".join(lines)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_analytics/test_utm.py -v`
Expected: PASS (all 5 tests)

- [ ] **Step 6: Commit**

```bash
git add src/marketolog/modules/analytics/__init__.py src/marketolog/modules/analytics/utm.py tests/test_modules/test_analytics/__init__.py tests/test_modules/test_analytics/conftest.py tests/test_modules/test_analytics/test_utm.py
git commit -m "feat(analytics): add generate_utm — UTM link builder"
```

---

### Task 2: metrika_report + metrika_goals

**Files:**
- Create: `src/marketolog/modules/analytics/metrika.py`
- Create: `tests/test_modules/test_analytics/test_metrika.py`

Yandex Metrika API: `GET https://api-metrika.yandex.net/stat/v1/data` with `Authorization: OAuth <token>` header. Counter ID from `config.yandex_metrika_counter` or `project.seo.yandex_metrika_id`.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_modules/test_analytics/test_metrika.py
"""Tests for Yandex Metrika report and goals tools."""

import httpx
import pytest
import respx

from marketolog.modules.analytics.metrika import run_metrika_report, run_metrika_goals

METRIKA_BASE = "https://api-metrika.yandex.net"
STAT_URL = f"{METRIKA_BASE}/stat/v1/data"
GOALS_URL = f"{METRIKA_BASE}/management/v1/counter/12345678/goals"

SAMPLE_STAT_RESPONSE = {
    "total_rows": 3,
    "data": [
        {
            "dimensions": [{"name": "organic"}],
            "metrics": [1200, 800, 35.5, 2.1],
        },
        {
            "dimensions": [{"name": "direct"}],
            "metrics": [500, 400, 40.0, 1.8],
        },
        {
            "dimensions": [{"name": "social"}],
            "metrics": [300, 250, 28.0, 3.0],
        },
    ],
    "total_rows_rounded": False,
    "totals": [2000, 1450, 34.5, 2.3],
}

SAMPLE_GOALS_RESPONSE = {
    "goals": [
        {"id": 1, "name": "Регистрация", "type": "url", "conditions": []},
        {"id": 2, "name": "Покупка", "type": "action", "conditions": []},
    ]
}


@respx.mock
@pytest.mark.asyncio
async def test_metrika_report(config_with_keys, cache):
    """Full metrika report with mocked API."""
    respx.get(STAT_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_STAT_RESPONSE)
    )

    report = await run_metrika_report(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )

    assert isinstance(report, str)
    assert "organic" in report
    assert "2000" in report or "2,000" in report or "2000" in report.replace(",", "")


@respx.mock
@pytest.mark.asyncio
async def test_metrika_report_cached(config_with_keys, cache):
    """Cached result returns without HTTP calls."""
    cache.set("metrika_report", "12345678:7d:default", "cached report", ttl_seconds=3600)

    report = await run_metrika_report(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )

    assert report == "cached report"
    assert len(respx.calls) == 0


@respx.mock
@pytest.mark.asyncio
async def test_metrika_report_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    report = await run_metrika_report(
        counter_id="12345678", config=config_no_keys, cache=cache,
    )

    assert "YANDEX_OAUTH_TOKEN" in report


@respx.mock
@pytest.mark.asyncio
async def test_metrika_goals(config_with_keys, cache):
    """Fetch goals list."""
    respx.get(GOALS_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_GOALS_RESPONSE)
    )

    report = await run_metrika_goals(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )

    assert "Регистрация" in report
    assert "Покупка" in report


@respx.mock
@pytest.mark.asyncio
async def test_metrika_goals_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    report = await run_metrika_goals(
        counter_id="12345678", config=config_no_keys, cache=cache,
    )

    assert "YANDEX_OAUTH_TOKEN" in report
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_analytics/test_metrika.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement metrika.py**

```python
# src/marketolog/modules/analytics/metrika.py
"""Yandex Metrika API — reports and goals.

Uses Yandex Metrika Stat API v1 for traffic data and Management API for goals.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.formatting import format_tabular
from marketolog.utils.http import fetch_with_retry

BASE_URL = "https://api-metrika.yandex.net"
CACHE_TTL = 1800  # 30 min

SETUP_INSTRUCTIONS = """\
Яндекс.Метрика не настроена.

Для использования задайте переменные окружения:

    YANDEX_OAUTH_TOKEN=<ваш OAuth-токен>
    YANDEX_METRIKA_COUNTER=<ID счётчика>

Получить токен: https://oauth.yandex.ru/
ID счётчика: https://metrika.yandex.ru/ → Настройки → Код счётчика
"""


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"OAuth {token}"}


async def run_metrika_report(
    counter_id: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
    period: str = "7d",
    metrics: str | None = None,
) -> str:
    """Fetch Yandex Metrika traffic report.

    Args:
        counter_id: Metrika counter ID.
        config: App configuration with OAuth token.
        cache: File cache instance.
        period: Period shorthand — "7d", "30d", "90d", or "today".
        metrics: Comma-separated metric names override.

    Returns:
        Formatted Markdown report.
    """
    if not config.is_configured("yandex_oauth_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.yandex_oauth_token  # type: ignore[assignment]

    cache_key = f"{counter_id}:{period}:{metrics or 'default'}"
    cached = cache.get("metrika_report", cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    date1, date2 = _period_to_dates(period)
    default_metrics = "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:avgVisitDurationSeconds"

    params = {
        "id": counter_id,
        "date1": date1,
        "date2": date2,
        "metrics": metrics or default_metrics,
        "dimensions": "ym:s:lastTrafficSource",
        "sort": "-ym:s:visits",
        "limit": 20,
    }

    resp = await fetch_with_retry(
        f"{BASE_URL}/stat/v1/data",
        headers=_auth_headers(token),
        params=params,
    )

    if resp.status_code != 200:
        return f"Ошибка Метрики (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    report = _format_stat_report(counter_id, period, data)

    cache.set("metrika_report", cache_key, report, ttl_seconds=CACHE_TTL)
    return report


async def run_metrika_goals(
    counter_id: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    """Fetch Yandex Metrika goals list.

    Args:
        counter_id: Metrika counter ID.
        config: App configuration with OAuth token.
        cache: File cache instance.

    Returns:
        Formatted goals list.
    """
    if not config.is_configured("yandex_oauth_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.yandex_oauth_token  # type: ignore[assignment]

    cached = cache.get("metrika_goals", counter_id)
    if cached is not None:
        return cached  # type: ignore[return-value]

    resp = await fetch_with_retry(
        f"{BASE_URL}/management/v1/counter/{counter_id}/goals",
        headers=_auth_headers(token),
    )

    if resp.status_code != 200:
        return f"Ошибка при получении целей (HTTP {resp.status_code}): {resp.text[:200]}"

    goals = resp.json().get("goals", [])
    report = _format_goals(counter_id, goals)

    cache.set("metrika_goals", counter_id, report, ttl_seconds=CACHE_TTL)
    return report


def _period_to_dates(period: str) -> tuple[str, str]:
    """Convert period shorthand to (date1, date2) for Metrika API."""
    from datetime import date, timedelta
    today = date.today()
    days_map = {"today": 0, "7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 7)
    start = today - timedelta(days=max(days, 1))
    return start.isoformat(), today.isoformat()


def _format_stat_report(counter_id: str, period: str, data: dict) -> str:
    lines = [f"## Отчёт Яндекс.Метрика (счётчик {counter_id}, период: {period})\n"]

    totals = data.get("totals", [])
    if totals:
        labels = ["Визиты", "Посетители", "Отказы (%)", "Ср. длительность (сек)"]
        lines.append("### Итого")
        for label, val in zip(labels, totals):
            formatted = f"{val:,.0f}" if isinstance(val, (int, float)) and label != "Отказы (%)" else str(val)
            lines.append(f"- **{label}:** {formatted}")
        lines.append("")

    rows = data.get("data", [])
    if rows:
        lines.append("### По источникам трафика")
        table_data = []
        for row in rows:
            dims = row.get("dimensions", [])
            mets = row.get("metrics", [])
            source_name = dims[0].get("name", "—") if dims else "—"
            table_data.append({
                "Источник": source_name,
                "Визиты": int(mets[0]) if len(mets) > 0 else 0,
                "Посетители": int(mets[1]) if len(mets) > 1 else 0,
                "Отказы (%)": round(mets[2], 1) if len(mets) > 2 else 0,
                "Ср. длит. (сек)": round(mets[3], 1) if len(mets) > 3 else 0,
            })
        lines.append(format_tabular(table_data))

    return "\n".join(lines)


def _format_goals(counter_id: str, goals: list[dict]) -> str:
    lines = [f"## Цели Яндекс.Метрика (счётчик {counter_id})\n"]

    if not goals:
        lines.append("Цели не настроены.")
        return "\n".join(lines)

    table_data = [
        {
            "ID": g.get("id", "—"),
            "Название": g.get("name", "—"),
            "Тип": g.get("type", "—"),
        }
        for g in goals
    ]
    lines.append(format_tabular(table_data))
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_analytics/test_metrika.py -v`
Expected: PASS (all 5 tests)

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/analytics/metrika.py tests/test_modules/test_analytics/test_metrika.py
git commit -m "feat(analytics): add metrika_report + metrika_goals — Yandex Metrika API"
```

---

### Task 3: search_console_report

**Files:**
- Create: `src/marketolog/modules/analytics/search_console.py`
- Create: `tests/test_modules/test_analytics/test_search_console.py`

Google Search Console uses `POST https://www.googleapis.com/webmasters/v3/sites/{siteUrl}/searchAnalytics/query` with a service account JWT. Since `google-auth` is a heavy dep, we'll use a simpler approach: read the service account JSON, sign a JWT with `PyJWT` + `cryptography`, and call the API directly. However, to keep deps light, we'll use `httpx` and accept that the user provides a pre-obtained access token in the credentials file, OR we document that `google-auth` is optional. For simplicity, we mock the auth in tests and use `fetch_with_retry`.

Actually, let's keep it simple: the `GOOGLE_SC_CREDENTIALS` config points to a service account JSON file. We'll add `google-auth` as an optional dependency and handle its absence gracefully. If not installed, return setup instructions.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_modules/test_analytics/test_search_console.py
"""Tests for Google Search Console report tool."""

import httpx
import pytest
import respx

from marketolog.modules.analytics.search_console import run_search_console_report

SC_API_URL = "https://www.googleapis.com/webmasters/v3/sites/https%3A%2F%2Fexample.ru/searchAnalytics/query"

SAMPLE_SC_RESPONSE = {
    "rows": [
        {
            "keys": ["таск трекер"],
            "clicks": 120,
            "impressions": 3500,
            "ctr": 0.034,
            "position": 6.2,
        },
        {
            "keys": ["управление задачами"],
            "clicks": 85,
            "impressions": 2100,
            "ctr": 0.040,
            "position": 8.5,
        },
        {
            "keys": ["бесплатный таск трекер"],
            "clicks": 30,
            "impressions": 800,
            "ctr": 0.037,
            "position": 14.1,
        },
    ],
    "responseAggregationType": "byPage",
}


@respx.mock
@pytest.mark.asyncio
async def test_search_console_report(config_with_keys, cache, monkeypatch):
    """Full SC report with mocked API and mocked auth."""
    # Mock the _get_access_token to skip real Google auth
    import marketolog.modules.analytics.search_console as sc_mod
    monkeypatch.setattr(sc_mod, "_get_access_token", lambda creds_path: "fake-token")

    respx.post(SC_API_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_SC_RESPONSE)
    )

    report = await run_search_console_report(
        site_url="https://example.ru",
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(report, str)
    assert "таск трекер" in report
    assert "120" in report


@respx.mock
@pytest.mark.asyncio
async def test_search_console_report_cached(config_with_keys, cache, monkeypatch):
    """Cached result returns without HTTP calls."""
    cache.set("search_console", "https://example.ru:7d", "cached SC report", ttl_seconds=3600)

    report = await run_search_console_report(
        site_url="https://example.ru",
        config=config_with_keys,
        cache=cache,
    )

    assert report == "cached SC report"
    assert len(respx.calls) == 0


@respx.mock
@pytest.mark.asyncio
async def test_search_console_no_credentials(config_no_keys, cache):
    """Without credentials — returns setup instructions."""
    report = await run_search_console_report(
        site_url="https://example.ru",
        config=config_no_keys,
        cache=cache,
    )

    assert "GOOGLE_SC_CREDENTIALS" in report
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_analytics/test_search_console.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement search_console.py**

```python
# src/marketolog/modules/analytics/search_console.py
"""Google Search Console API — search performance report.

Uses the Search Analytics API to fetch queries, clicks, impressions, CTR, and position data.
Auth: Google Service Account JSON file (path in GOOGLE_SC_CREDENTIALS).
"""

import json
from urllib.parse import quote

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.formatting import format_tabular
from marketolog.utils.http import fetch_with_retry

SC_API_BASE = "https://www.googleapis.com/webmasters/v3/sites"
CACHE_NS = "search_console"
CACHE_TTL = 1800  # 30 min

SETUP_INSTRUCTIONS = """\
Google Search Console не настроен.

Для использования задайте переменную окружения:

    GOOGLE_SC_CREDENTIALS=/path/to/service-account.json

1. Создайте Service Account в Google Cloud Console
2. Добавьте его email в Search Console как пользователя
3. Скачайте JSON-ключ и укажите путь в переменной
"""


def _get_access_token(credentials_path: str) -> str | None:
    """Get Google access token from service account JSON.

    Uses google-auth library if available, otherwise returns None.
    """
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
        credentials.refresh(Request())
        return credentials.token
    except ImportError:
        return None
    except Exception:
        return None


async def run_search_console_report(
    site_url: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
    period: str = "7d",
) -> str:
    """Fetch Google Search Console performance report.

    Args:
        site_url: Site URL as registered in Search Console.
        config: App configuration with Google SC credentials path.
        cache: File cache instance.
        period: Period shorthand — "7d", "28d", "90d".

    Returns:
        Formatted Markdown report.
    """
    if not config.is_configured("google_sc_credentials"):
        return SETUP_INSTRUCTIONS

    cache_key = f"{site_url}:{period}"
    cached = cache.get(CACHE_NS, cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    creds_path: str = config.google_sc_credentials  # type: ignore[assignment]
    token = _get_access_token(creds_path)
    if token is None:
        return (
            "Не удалось получить токен Google SC.\n\n"
            "Убедитесь, что установлен пакет `google-auth`:\n"
            "    pip install google-auth\n\n"
            "И что путь в GOOGLE_SC_CREDENTIALS указывает на валидный service account JSON."
        )

    from datetime import date, timedelta
    today = date.today()
    # SC data has 2-3 day delay
    end_date = today - timedelta(days=3)
    days_map = {"7d": 7, "28d": 28, "90d": 90}
    days = days_map.get(period, 7)
    start_date = end_date - timedelta(days=days)

    encoded_url = quote(site_url, safe="")
    api_url = f"{SC_API_BASE}/{encoded_url}/searchAnalytics/query"

    body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["query"],
        "rowLimit": 50,
    }

    resp = await fetch_with_retry(
        api_url,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
    )

    if resp.status_code != 200:
        return f"Ошибка Google SC (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    report = _format_sc_report(site_url, period, data)

    cache.set(CACHE_NS, cache_key, report, ttl_seconds=CACHE_TTL)
    return report


def _format_sc_report(site_url: str, period: str, data: dict) -> str:
    lines = [f"## Google Search Console: {site_url} (период: {period})\n"]

    rows = data.get("rows", [])
    if not rows:
        lines.append("Нет данных за выбранный период.")
        return "\n".join(lines)

    total_clicks = sum(r.get("clicks", 0) for r in rows)
    total_impressions = sum(r.get("impressions", 0) for r in rows)
    avg_ctr = total_clicks / total_impressions if total_impressions > 0 else 0

    lines.append("### Сводка")
    lines.append(f"- **Клики:** {total_clicks:,}")
    lines.append(f"- **Показы:** {total_impressions:,}")
    lines.append(f"- **Средний CTR:** {avg_ctr:.1%}")
    lines.append("")

    lines.append("### Топ запросы")
    table_data = [
        {
            "Запрос": r["keys"][0] if r.get("keys") else "—",
            "Клики": r.get("clicks", 0),
            "Показы": r.get("impressions", 0),
            "CTR": f"{r.get('ctr', 0):.1%}",
            "Позиция": round(r.get("position", 0), 1),
        }
        for r in rows
    ]
    lines.append(format_tabular(table_data))

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_analytics/test_search_console.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/analytics/search_console.py tests/test_modules/test_analytics/test_search_console.py
git commit -m "feat(analytics): add search_console_report — Google SC API"
```

---

### Task 4: traffic_sources

**Files:**
- Create: `src/marketolog/modules/analytics/traffic_sources.py`
- Create: `tests/test_modules/test_analytics/test_traffic_sources.py`

Combines Yandex Metrika traffic source data. If SC is also available, adds organic Google data. Falls back gracefully if only one source is configured.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_modules/test_analytics/test_traffic_sources.py
"""Tests for traffic_sources tool."""

import httpx
import pytest
import respx

from marketolog.modules.analytics.traffic_sources import run_traffic_sources

METRIKA_STAT_URL = "https://api-metrika.yandex.net/stat/v1/data"

SAMPLE_SOURCES = {
    "data": [
        {"dimensions": [{"name": "organic"}], "metrics": [1200]},
        {"dimensions": [{"name": "direct"}], "metrics": [500]},
        {"dimensions": [{"name": "social"}], "metrics": [300]},
        {"dimensions": [{"name": "referral"}], "metrics": [100]},
    ],
    "totals": [2100],
}


@respx.mock
@pytest.mark.asyncio
async def test_traffic_sources(config_with_keys, cache):
    """Traffic sources report from Metrika."""
    respx.get(METRIKA_STAT_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_SOURCES)
    )

    report = await run_traffic_sources(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )

    assert isinstance(report, str)
    assert "organic" in report
    assert "social" in report
    # Should have percentage breakdown
    assert "%" in report


@respx.mock
@pytest.mark.asyncio
async def test_traffic_sources_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    report = await run_traffic_sources(
        counter_id="12345678", config=config_no_keys, cache=cache,
    )

    assert "YANDEX_OAUTH_TOKEN" in report


@respx.mock
@pytest.mark.asyncio
async def test_traffic_sources_cached(config_with_keys, cache):
    """Cached result returned."""
    cache.set("traffic_sources", "12345678:7d", "cached sources", ttl_seconds=3600)

    report = await run_traffic_sources(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )

    assert report == "cached sources"
    assert len(respx.calls) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_analytics/test_traffic_sources.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement traffic_sources.py**

```python
# src/marketolog/modules/analytics/traffic_sources.py
"""Traffic sources breakdown — Yandex Metrika source analysis."""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

METRIKA_BASE = "https://api-metrika.yandex.net"
CACHE_NS = "traffic_sources"
CACHE_TTL = 1800  # 30 min

SETUP_INSTRUCTIONS = """\
Яндекс.Метрика не настроена.

Для анализа источников трафика задайте переменные окружения:

    YANDEX_OAUTH_TOKEN=<ваш OAuth-токен>
    YANDEX_METRIKA_COUNTER=<ID счётчика>
"""


async def run_traffic_sources(
    counter_id: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
    period: str = "7d",
) -> str:
    """Analyze traffic sources from Yandex Metrika.

    Args:
        counter_id: Metrika counter ID.
        config: App configuration.
        cache: File cache.
        period: "7d", "30d", "90d".

    Returns:
        Formatted traffic sources report with percentages.
    """
    if not config.is_configured("yandex_oauth_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.yandex_oauth_token  # type: ignore[assignment]

    cache_key = f"{counter_id}:{period}"
    cached = cache.get(CACHE_NS, cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    from marketolog.modules.analytics.metrika import _period_to_dates, _auth_headers

    date1, date2 = _period_to_dates(period)

    resp = await fetch_with_retry(
        f"{METRIKA_BASE}/stat/v1/data",
        headers=_auth_headers(token),
        params={
            "id": counter_id,
            "date1": date1,
            "date2": date2,
            "metrics": "ym:s:visits",
            "dimensions": "ym:s:lastTrafficSource",
            "sort": "-ym:s:visits",
            "limit": 20,
        },
    )

    if resp.status_code != 200:
        return f"Ошибка Метрики (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    report = _format_sources(counter_id, period, data)

    cache.set(CACHE_NS, cache_key, report, ttl_seconds=CACHE_TTL)
    return report


def _format_sources(counter_id: str, period: str, data: dict) -> str:
    lines = [f"## Источники трафика (счётчик {counter_id}, период: {period})\n"]

    rows = data.get("data", [])
    totals = data.get("totals", [0])
    total_visits = totals[0] if totals else 0

    if not rows:
        lines.append("Нет данных за выбранный период.")
        return "\n".join(lines)

    lines.append(f"**Всего визитов:** {int(total_visits):,}\n")

    source_names = {
        "organic": "Поисковые системы",
        "direct": "Прямые заходы",
        "social": "Социальные сети",
        "referral": "Ссылки с сайтов",
        "ad": "Реклама",
        "internal": "Внутренние переходы",
        "email": "Email-рассылки",
        "messenger": "Мессенджеры",
    }

    for row in rows:
        dims = row.get("dimensions", [])
        mets = row.get("metrics", [0])
        source_key = dims[0].get("name", "—") if dims else "—"
        visits = int(mets[0]) if mets else 0
        pct = (visits / total_visits * 100) if total_visits > 0 else 0
        label = source_names.get(source_key, source_key)
        bar = "█" * int(pct / 5) if pct >= 5 else "▏"
        lines.append(f"- **{label}** ({source_key}): {visits:,} ({pct:.1f}%) {bar}")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_analytics/test_traffic_sources.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/analytics/traffic_sources.py tests/test_modules/test_analytics/test_traffic_sources.py
git commit -m "feat(analytics): add traffic_sources — source breakdown with percentages"
```

---

### Task 5: funnel_analysis

**Files:**
- Create: `src/marketolog/modules/analytics/funnel.py`
- Create: `tests/test_modules/test_analytics/test_funnel.py`

Uses Metrika API with goal-specific metrics to analyze conversion funnels.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_modules/test_analytics/test_funnel.py
"""Tests for funnel analysis tool."""

import httpx
import pytest
import respx

from marketolog.modules.analytics.funnel import run_funnel_analysis

METRIKA_STAT_URL = "https://api-metrika.yandex.net/stat/v1/data"
METRIKA_GOALS_URL = "https://api-metrika.yandex.net/management/v1/counter/12345678/goals"

SAMPLE_GOALS = {
    "goals": [
        {"id": 1, "name": "Регистрация", "type": "url"},
        {"id": 2, "name": "Покупка", "type": "action"},
    ]
}

SAMPLE_FUNNEL_DATA = {
    "data": [
        {"dimensions": [{"name": "organic"}], "metrics": [1000, 50, 5.0, 10, 1.0]},
        {"dimensions": [{"name": "direct"}], "metrics": [500, 20, 4.0, 3, 0.6]},
    ],
    "totals": [1500, 70, 4.7, 13, 0.87],
}


@respx.mock
@pytest.mark.asyncio
async def test_funnel_analysis(config_with_keys, cache):
    """Funnel analysis with goals data."""
    respx.get(METRIKA_GOALS_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_GOALS)
    )
    respx.get(METRIKA_STAT_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_FUNNEL_DATA)
    )

    report = await run_funnel_analysis(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )

    assert isinstance(report, str)
    assert "Регистрация" in report or "воронк" in report.lower()
    assert "organic" in report


@respx.mock
@pytest.mark.asyncio
async def test_funnel_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    report = await run_funnel_analysis(
        counter_id="12345678", config=config_no_keys, cache=cache,
    )

    assert "YANDEX_OAUTH_TOKEN" in report


@respx.mock
@pytest.mark.asyncio
async def test_funnel_specific_goal(config_with_keys, cache):
    """Request analysis for a specific goal."""
    respx.get(METRIKA_GOALS_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_GOALS)
    )
    respx.get(METRIKA_STAT_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_FUNNEL_DATA)
    )

    report = await run_funnel_analysis(
        counter_id="12345678", config=config_with_keys, cache=cache,
        goal="Регистрация",
    )

    assert isinstance(report, str)
    assert "Регистрация" in report
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_analytics/test_funnel.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement funnel.py**

```python
# src/marketolog/modules/analytics/funnel.py
"""Funnel analysis — goal conversion by traffic source via Yandex Metrika."""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.formatting import format_tabular
from marketolog.utils.http import fetch_with_retry

METRIKA_BASE = "https://api-metrika.yandex.net"
CACHE_NS = "funnel_analysis"
CACHE_TTL = 1800

SETUP_INSTRUCTIONS = """\
Яндекс.Метрика не настроена.

Для анализа воронки задайте переменные окружения:

    YANDEX_OAUTH_TOKEN=<ваш OAuth-токен>
    YANDEX_METRIKA_COUNTER=<ID счётчика>
"""


async def run_funnel_analysis(
    counter_id: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
    goal: str | None = None,
    period: str = "30d",
) -> str:
    """Analyze conversion funnel by traffic source.

    Args:
        counter_id: Metrika counter ID.
        config: App configuration.
        cache: File cache.
        goal: Goal name to analyze (None = first goal).
        period: Period shorthand.

    Returns:
        Formatted funnel analysis report.
    """
    if not config.is_configured("yandex_oauth_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.yandex_oauth_token  # type: ignore[assignment]

    cache_key = f"{counter_id}:{goal or 'first'}:{period}"
    cached = cache.get(CACHE_NS, cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    from marketolog.modules.analytics.metrika import _period_to_dates, _auth_headers

    # Step 1: get goals to find goal ID
    goals_resp = await fetch_with_retry(
        f"{METRIKA_BASE}/management/v1/counter/{counter_id}/goals",
        headers=_auth_headers(token),
    )
    if goals_resp.status_code != 200:
        return f"Ошибка при получении целей (HTTP {goals_resp.status_code})"

    goals = goals_resp.json().get("goals", [])
    if not goals:
        return "Цели не настроены в Метрике. Создайте хотя бы одну цель для анализа воронки."

    # Find target goal
    target_goal = goals[0]
    if goal:
        for g in goals:
            if g.get("name", "").lower() == goal.lower():
                target_goal = g
                break

    goal_id = target_goal["id"]
    goal_name = target_goal.get("name", f"Goal {goal_id}")

    # Step 2: fetch funnel data (visits + goal reaches + conversion by source)
    date1, date2 = _period_to_dates(period)

    metrics = (
        f"ym:s:visits,"
        f"ym:s:goal{goal_id}reaches,"
        f"ym:s:goal{goal_id}conversionRate,"
        f"ym:s:goal{goal_id}revenue,"
        f"ym:s:bounceRate"
    )

    resp = await fetch_with_retry(
        f"{METRIKA_BASE}/stat/v1/data",
        headers=_auth_headers(token),
        params={
            "id": counter_id,
            "date1": date1,
            "date2": date2,
            "metrics": metrics,
            "dimensions": "ym:s:lastTrafficSource",
            "sort": f"-ym:s:goal{goal_id}reaches",
            "limit": 20,
        },
    )

    if resp.status_code != 200:
        return f"Ошибка Метрики (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    report = _format_funnel(counter_id, goal_name, period, data)

    cache.set(CACHE_NS, cache_key, report, ttl_seconds=CACHE_TTL)
    return report


def _format_funnel(counter_id: str, goal_name: str, period: str, data: dict) -> str:
    lines = [f"## Анализ воронки: {goal_name} (период: {period})\n"]

    totals = data.get("totals", [])
    if totals and len(totals) >= 3:
        lines.append("### Сводка")
        lines.append(f"- **Визиты:** {int(totals[0]):,}")
        lines.append(f"- **Достижения цели:** {int(totals[1]):,}")
        lines.append(f"- **Конверсия:** {totals[2]:.1f}%")
        if len(totals) >= 5:
            lines.append(f"- **Отказы:** {totals[4]:.1f}%")
        lines.append("")

    rows = data.get("data", [])
    if rows:
        lines.append("### По источникам (откуда → конверсия)")
        table_data = []
        for row in rows:
            dims = row.get("dimensions", [])
            mets = row.get("metrics", [])
            source = dims[0].get("name", "—") if dims else "—"
            table_data.append({
                "Источник": source,
                "Визиты": int(mets[0]) if len(mets) > 0 else 0,
                "Достижения": int(mets[1]) if len(mets) > 1 else 0,
                "Конверсия (%)": round(mets[2], 1) if len(mets) > 2 else 0,
                "Отказы (%)": round(mets[4], 1) if len(mets) > 4 else 0,
            })
        lines.append(format_tabular(table_data))

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_analytics/test_funnel.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/analytics/funnel.py tests/test_modules/test_analytics/test_funnel.py
git commit -m "feat(analytics): add funnel_analysis — goal conversion by source"
```

---

### Task 6: ai_referral_report

**Files:**
- Create: `src/marketolog/modules/analytics/ai_referral.py`
- Create: `tests/test_modules/test_analytics/test_ai_referral.py`

Analyzes Metrika referrer data to identify traffic from AI search engines (ChatGPT, Perplexity, Claude, Google AI Overviews).

- [ ] **Step 1: Write failing tests**

```python
# tests/test_modules/test_analytics/test_ai_referral.py
"""Tests for AI referral report tool."""

import httpx
import pytest
import respx

from marketolog.modules.analytics.ai_referral import run_ai_referral_report

METRIKA_STAT_URL = "https://api-metrika.yandex.net/stat/v1/data"

SAMPLE_REFERRER_DATA = {
    "data": [
        {"dimensions": [{"name": "chat.openai.com"}], "metrics": [45, 30]},
        {"dimensions": [{"name": "perplexity.ai"}], "metrics": [20, 15]},
        {"dimensions": [{"name": "claude.ai"}], "metrics": [10, 8]},
        {"dimensions": [{"name": "google.com"}], "metrics": [500, 350]},
        {"dimensions": [{"name": "yandex.ru"}], "metrics": [300, 200]},
    ],
    "totals": [875, 603],
}


@respx.mock
@pytest.mark.asyncio
async def test_ai_referral_report(config_with_keys, cache):
    """AI referral report identifies AI search traffic."""
    respx.get(METRIKA_STAT_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_REFERRER_DATA)
    )

    report = await run_ai_referral_report(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )

    assert isinstance(report, str)
    assert "ChatGPT" in report or "chat.openai.com" in report
    assert "Perplexity" in report or "perplexity.ai" in report
    assert "Claude" in report or "claude.ai" in report


@respx.mock
@pytest.mark.asyncio
async def test_ai_referral_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    report = await run_ai_referral_report(
        counter_id="12345678", config=config_no_keys, cache=cache,
    )

    assert "YANDEX_OAUTH_TOKEN" in report


@respx.mock
@pytest.mark.asyncio
async def test_ai_referral_no_ai_traffic(config_with_keys, cache):
    """When no AI referrer domains found — report says so."""
    no_ai_data = {
        "data": [
            {"dimensions": [{"name": "google.com"}], "metrics": [500, 350]},
            {"dimensions": [{"name": "yandex.ru"}], "metrics": [300, 200]},
        ],
        "totals": [800, 550],
    }
    respx.get(METRIKA_STAT_URL).mock(
        return_value=httpx.Response(200, json=no_ai_data)
    )

    report = await run_ai_referral_report(
        counter_id="12345678", config=config_with_keys, cache=cache,
    )

    assert "не обнаружен" in report.lower() or "0" in report
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_analytics/test_ai_referral.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement ai_referral.py**

```python
# src/marketolog/modules/analytics/ai_referral.py
"""AI referral traffic analysis — identifies visits from AI search engines.

Tracks traffic from: ChatGPT, Perplexity, Claude, Google AI Overviews,
Microsoft Copilot, You.com, Phind, and other AI-powered search tools.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

METRIKA_BASE = "https://api-metrika.yandex.net"
CACHE_NS = "ai_referral"
CACHE_TTL = 1800

SETUP_INSTRUCTIONS = """\
Яндекс.Метрика не настроена.

Для отчёта по AI-трафику задайте переменные окружения:

    YANDEX_OAUTH_TOKEN=<ваш OAuth-токен>
    YANDEX_METRIKA_COUNTER=<ID счётчика>
"""

# Known AI search engine referrer domains
AI_DOMAINS: dict[str, str] = {
    "chat.openai.com": "ChatGPT",
    "chatgpt.com": "ChatGPT",
    "perplexity.ai": "Perplexity",
    "claude.ai": "Claude",
    "copilot.microsoft.com": "Microsoft Copilot",
    "you.com": "You.com",
    "phind.com": "Phind",
    "bard.google.com": "Google Bard",
    "gemini.google.com": "Google Gemini",
    "labs.google.com": "Google AI (Labs)",
}


async def run_ai_referral_report(
    counter_id: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
    period: str = "30d",
) -> str:
    """Analyze traffic from AI search engines.

    Args:
        counter_id: Metrika counter ID.
        config: App configuration.
        cache: File cache.
        period: Period shorthand.

    Returns:
        Formatted AI referral report.
    """
    if not config.is_configured("yandex_oauth_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.yandex_oauth_token  # type: ignore[assignment]

    cache_key = f"{counter_id}:{period}"
    cached = cache.get(CACHE_NS, cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    from marketolog.modules.analytics.metrika import _period_to_dates, _auth_headers

    date1, date2 = _period_to_dates(period)

    resp = await fetch_with_retry(
        f"{METRIKA_BASE}/stat/v1/data",
        headers=_auth_headers(token),
        params={
            "id": counter_id,
            "date1": date1,
            "date2": date2,
            "metrics": "ym:s:visits,ym:s:users",
            "dimensions": "ym:s:refererDomain",
            "sort": "-ym:s:visits",
            "limit": 200,
        },
    )

    if resp.status_code != 200:
        return f"Ошибка Метрики (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    report = _format_ai_report(counter_id, period, data)

    cache.set(CACHE_NS, cache_key, report, ttl_seconds=CACHE_TTL)
    return report


def _format_ai_report(counter_id: str, period: str, data: dict) -> str:
    lines = [f"## AI-трафик (счётчик {counter_id}, период: {period})\n"]

    rows = data.get("data", [])
    totals = data.get("totals", [0, 0])
    total_visits = totals[0] if totals else 0

    # Filter AI referrers
    ai_rows: list[dict] = []
    for row in rows:
        dims = row.get("dimensions", [])
        domain = dims[0].get("name", "") if dims else ""
        ai_name = _match_ai_domain(domain)
        if ai_name:
            mets = row.get("metrics", [0, 0])
            ai_rows.append({
                "domain": domain,
                "name": ai_name,
                "visits": int(mets[0]) if mets else 0,
                "users": int(mets[1]) if len(mets) > 1 else 0,
            })

    if not ai_rows:
        lines.append("AI-трафик не обнаружен за выбранный период.\n")
        lines.append("Это нормально — AI-поисковики пока дают мало прямого трафика.")
        lines.append("Рекомендации по улучшению видимости для AI:")
        lines.append("- Проверьте `ai_seo_check` для анализа готовности сайта")
        lines.append("- Добавьте файл `llms.txt` на сайт")
        lines.append("- Структурируйте контент с JSON-LD schema")
        return "\n".join(lines)

    total_ai = sum(r["visits"] for r in ai_rows)
    ai_share = (total_ai / total_visits * 100) if total_visits > 0 else 0

    lines.append("### Сводка")
    lines.append(f"- **AI-визиты:** {total_ai:,} из {int(total_visits):,} ({ai_share:.1f}%)")
    lines.append("")

    lines.append("### По источникам")
    for r in sorted(ai_rows, key=lambda x: x["visits"], reverse=True):
        pct = (r["visits"] / total_visits * 100) if total_visits > 0 else 0
        lines.append(f"- **{r['name']}** ({r['domain']}): {r['visits']:,} визитов, {r['users']:,} уник. ({pct:.2f}%)")

    return "\n".join(lines)


def _match_ai_domain(domain: str) -> str | None:
    """Match a referrer domain to a known AI search engine."""
    domain_lower = domain.lower()
    for ai_domain, ai_name in AI_DOMAINS.items():
        if ai_domain in domain_lower:
            return ai_name
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_analytics/test_ai_referral.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/analytics/ai_referral.py tests/test_modules/test_analytics/test_ai_referral.py
git commit -m "feat(analytics): add ai_referral_report — AI search traffic tracking"
```

---

### Task 7: weekly_digest

**Files:**
- Create: `src/marketolog/modules/analytics/digest.py`
- Create: `tests/test_modules/test_analytics/test_digest.py`

Aggregates data from Metrika (traffic, goals) into a concise weekly summary. It calls `run_metrika_report` and `run_metrika_goals` internally, then builds a digest.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_modules/test_analytics/test_digest.py
"""Tests for weekly digest tool."""

import httpx
import pytest
import respx

from marketolog.modules.analytics.digest import run_weekly_digest

METRIKA_STAT_URL = "https://api-metrika.yandex.net/stat/v1/data"

SAMPLE_WEEKLY_DATA = {
    "data": [
        {"dimensions": [{"name": "organic"}], "metrics": [800, 600, 30.0, 120]},
        {"dimensions": [{"name": "direct"}], "metrics": [400, 300, 35.0, 90]},
        {"dimensions": [{"name": "social"}], "metrics": [200, 150, 25.0, 150]},
    ],
    "totals": [1400, 1050, 30.5, 115],
}


@respx.mock
@pytest.mark.asyncio
async def test_weekly_digest(config_with_keys, cache):
    """Weekly digest with Metrika data."""
    respx.get(METRIKA_STAT_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_WEEKLY_DATA)
    )

    report = await run_weekly_digest(
        counter_id="12345678",
        project_name="test-project",
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(report, str)
    assert "дайджест" in report.lower() or "Дайджест" in report
    assert "1,400" in report or "1400" in report
    assert "organic" in report or "Поиск" in report


@respx.mock
@pytest.mark.asyncio
async def test_weekly_digest_no_token(config_no_keys, cache):
    """Without token — returns setup instructions."""
    report = await run_weekly_digest(
        counter_id="12345678",
        project_name="test-project",
        config=config_no_keys,
        cache=cache,
    )

    assert "YANDEX_OAUTH_TOKEN" in report


@respx.mock
@pytest.mark.asyncio
async def test_weekly_digest_cached(config_with_keys, cache):
    """Cached result returned."""
    from datetime import date
    week_key = f"12345678:{date.today().isocalendar()[1]}"
    cache.set("weekly_digest", week_key, "cached digest", ttl_seconds=3600)

    report = await run_weekly_digest(
        counter_id="12345678",
        project_name="test-project",
        config=config_with_keys,
        cache=cache,
    )

    assert report == "cached digest"
    assert len(respx.calls) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_analytics/test_digest.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement digest.py**

```python
# src/marketolog/modules/analytics/digest.py
"""Weekly digest — aggregated weekly performance report.

Combines Metrika traffic data into a concise weekly summary with
trends and recommendations trigger points.
"""

from datetime import date, timedelta

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

METRIKA_BASE = "https://api-metrika.yandex.net"
CACHE_NS = "weekly_digest"
CACHE_TTL = 3600  # 1 hour

SETUP_INSTRUCTIONS = """\
Яндекс.Метрика не настроена.

Для еженедельного дайджеста задайте переменные окружения:

    YANDEX_OAUTH_TOKEN=<ваш OAuth-токен>
    YANDEX_METRIKA_COUNTER=<ID счётчика>
"""


async def run_weekly_digest(
    counter_id: str,
    project_name: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    """Generate weekly performance digest.

    Args:
        counter_id: Metrika counter ID.
        project_name: Project name for the report header.
        config: App configuration.
        cache: File cache.

    Returns:
        Formatted weekly digest.
    """
    if not config.is_configured("yandex_oauth_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.yandex_oauth_token  # type: ignore[assignment]

    week_num = date.today().isocalendar()[1]
    cache_key = f"{counter_id}:{week_num}"
    cached = cache.get(CACHE_NS, cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    from marketolog.modules.analytics.metrika import _auth_headers

    # Fetch this week's data
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = today

    resp = await fetch_with_retry(
        f"{METRIKA_BASE}/stat/v1/data",
        headers=_auth_headers(token),
        params={
            "id": counter_id,
            "date1": week_start.isoformat(),
            "date2": week_end.isoformat(),
            "metrics": "ym:s:visits,ym:s:users,ym:s:bounceRate,ym:s:avgVisitDurationSeconds",
            "dimensions": "ym:s:lastTrafficSource",
            "sort": "-ym:s:visits",
            "limit": 10,
        },
    )

    if resp.status_code != 200:
        return f"Ошибка Метрики (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    report = _format_digest(project_name, week_start, week_end, data)

    cache.set(CACHE_NS, cache_key, report, ttl_seconds=CACHE_TTL)
    return report


def _format_digest(
    project_name: str,
    week_start: date,
    week_end: date,
    data: dict,
) -> str:
    lines = [
        f"## Недельный дайджест \"{project_name}\"",
        f"Период: {week_start.strftime('%d.%m')} — {week_end.strftime('%d.%m.%Y')}\n",
    ]

    totals = data.get("totals", [])
    if totals:
        visits = int(totals[0]) if len(totals) > 0 else 0
        users = int(totals[1]) if len(totals) > 1 else 0
        bounce = totals[2] if len(totals) > 2 else 0
        avg_dur = totals[3] if len(totals) > 3 else 0

        lines.append("### Ключевые метрики")
        lines.append(f"- **Визиты:** {visits:,}")
        lines.append(f"- **Посетители:** {users:,}")
        lines.append(f"- **Отказы:** {bounce:.1f}%")
        mins = int(avg_dur) // 60
        secs = int(avg_dur) % 60
        lines.append(f"- **Ср. время на сайте:** {mins}:{secs:02d}")
        lines.append("")

    rows = data.get("data", [])
    if rows:
        total_visits = int(totals[0]) if totals else 1
        lines.append("### Источники трафика")
        for row in rows:
            dims = row.get("dimensions", [])
            mets = row.get("metrics", [0])
            source = dims[0].get("name", "—") if dims else "—"
            visits = int(mets[0]) if mets else 0
            pct = (visits / total_visits * 100) if total_visits > 0 else 0
            lines.append(f"- {source}: {visits:,} ({pct:.0f}%)")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_analytics/test_digest.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/analytics/digest.py tests/test_modules/test_analytics/test_digest.py
git commit -m "feat(analytics): add weekly_digest — aggregated weekly report"
```

---

### Task 8: Register 8 analytics tools in server.py + analyst prompt + integration tests

**Files:**
- Create: `src/marketolog/prompts/analyst.md`
- Modify: `src/marketolog/server.py` (add imports, register 8 tools, add analyst resource)
- Create: `tests/test_modules/test_analytics/test_integration.py`

- [ ] **Step 1: Create analyst.md prompt**

```markdown
# src/marketolog/prompts/analyst.md
# Аналитик

Ты — опытный маркетинговый аналитик, специализирующийся на веб-аналитике и data-driven маркетинге для бизнеса в Рунете.

## Принципы работы

- Всегда начинай с данных, не с предположений
- Переводи цифры в конкретные действия: не "отказы высокие", а "отказы 45% на /pricing — проверь скорость загрузки и первый экран"
- Сравнивай с предыдущим периодом — тренд важнее абсолютного числа
- Выделяй аномалии и точки роста
- Приоритизируй инсайты по потенциальному влиянию на бизнес

## Доступные инструменты

- `metrika_report` — основной трафик и поведение
- `metrika_goals` — цели и конверсии
- `search_console_report` — поисковые запросы из Google
- `traffic_sources` — откуда приходят посетители
- `funnel_analysis` — воронка конверсии по источникам
- `weekly_digest` — еженедельная сводка
- `ai_referral_report` — трафик от AI-поисковиков (новый канал!)
- `generate_utm` — UTM-разметка для отслеживания кампаний

## Формат ответа

1. Сводка (3-5 ключевых цифр)
2. Что изменилось (тренды, аномалии)
3. Почему (гипотезы на основе данных)
4. Что делать (конкретные действия, приоритизированные по влиянию)
```

- [ ] **Step 2: Write integration tests**

```python
# tests/test_modules/test_analytics/test_integration.py
"""Integration tests — analytics tools registered in MCP server."""

import asyncio
import pytest
from pathlib import Path

from marketolog.server import create_server


@pytest.fixture
def server(tmp_marketolog_dir: Path):
    return create_server(base_dir=tmp_marketolog_dir)


def test_server_has_analytics_tools(server):
    """Server must expose all 8 analytics tools."""
    tools = asyncio.run(server._local_provider.list_tools())
    tool_names = {t.name for t in tools}
    expected_analytics = {
        "metrika_report", "metrika_goals", "search_console_report",
        "traffic_sources", "funnel_analysis", "weekly_digest",
        "ai_referral_report", "generate_utm",
    }
    assert expected_analytics.issubset(tool_names), f"Missing: {expected_analytics - tool_names}"


def test_server_has_analyst_resource(server):
    """Server must expose analyst prompt as a resource."""
    resources = asyncio.run(server._local_provider.list_resources())
    resource_uris = {str(r.uri) for r in resources}
    assert any("analyst" in uri for uri in resource_uris)


def test_analytics_tools_are_read_only(server):
    """All analytics tools should have readOnlyHint=True."""
    tools = asyncio.run(server._local_provider.list_tools())
    analytics_tools = {
        "metrika_report", "metrika_goals", "search_console_report",
        "traffic_sources", "funnel_analysis", "weekly_digest",
        "ai_referral_report", "generate_utm",
    }
    for tool in tools:
        if tool.name in analytics_tools:
            assert tool.annotations is not None, f"{tool.name} has no annotations"
            assert tool.annotations.readOnlyHint is True, f"{tool.name} should be readOnlyHint=True"


def test_total_tool_count(server):
    """Server should have exactly 22 tools (6 Core + 8 SEO + 8 Analytics)."""
    tools = asyncio.run(server._local_provider.list_tools())
    assert len(tools) == 22, f"Expected 22 tools, got {len(tools)}: {[t.name for t in tools]}"
```

- [ ] **Step 3: Run integration tests to verify they fail**

Run: `pytest tests/test_modules/test_analytics/test_integration.py -v`
Expected: FAIL — tools not registered yet

- [ ] **Step 4: Add imports and register tools in server.py**

Add these imports at the top of `src/marketolog/server.py`, after the SEO imports:

```python
from marketolog.modules.analytics.utm import generate_utm as _generate_utm
from marketolog.modules.analytics.metrika import run_metrika_report, run_metrika_goals
from marketolog.modules.analytics.search_console import run_search_console_report
from marketolog.modules.analytics.traffic_sources import run_traffic_sources
from marketolog.modules.analytics.funnel import run_funnel_analysis
from marketolog.modules.analytics.ai_referral import run_ai_referral_report
from marketolog.modules.analytics.digest import run_weekly_digest
```

Add these tool registrations in `create_server()`, after the SEO tools block and before the Prompt Resources block:

```python
    # --- Analytics Tools ---

    def _get_counter_id() -> str:
        """Get Metrika counter ID from config or project context."""
        if config.yandex_metrika_counter:
            return config.yandex_metrika_counter
        project = ctx.get_context()
        return project.get("seo", {}).get("yandex_metrika_id", "")

    @mcp.tool(annotations=READ_ONLY)
    def generate_utm_link(
        url: Annotated[str, Field(description="URL для UTM-разметки")],
        source: Annotated[str, Field(description="Источник трафика (telegram, vk, email...)")],
        medium: Annotated[str, Field(description="Канал (social, cpc, email...)")],
        campaign: Annotated[str | None, Field(description="Название кампании", default=None)] = None,
        term: Annotated[str | None, Field(description="Ключевое слово (для платной рекламы)", default=None)] = None,
        content: Annotated[str | None, Field(description="Вариант объявления", default=None)] = None,
    ) -> str:
        """Генерация UTM-размеченной ссылки для отслеживания кампаний."""
        return _generate_utm(url=url, source=source, medium=medium, campaign=campaign, term=term, content=content)

    @mcp.tool(annotations=READ_ONLY)
    async def metrika_report(
        period: Annotated[str, Field(description="Период: 7d, 30d, 90d, today", default="7d")] = "7d",
        metrics: Annotated[str | None, Field(description="Метрики (через запятую)", default=None)] = None,
    ) -> str:
        """Отчёт Яндекс.Метрика: визиты, источники, поведение, конверсии."""
        counter_id = _get_counter_id()
        if not counter_id:
            return "Укажите YANDEX_METRIKA_COUNTER или добавьте yandex_metrika_id в проект."
        return await run_metrika_report(counter_id=counter_id, config=config, cache=cache, period=period, metrics=metrics)

    @mcp.tool(annotations=READ_ONLY)
    async def metrika_goals() -> str:
        """Список целей и конверсий в Яндекс.Метрике."""
        counter_id = _get_counter_id()
        if not counter_id:
            return "Укажите YANDEX_METRIKA_COUNTER или добавьте yandex_metrika_id в проект."
        return await run_metrika_goals(counter_id=counter_id, config=config, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    async def search_console_report(
        period: Annotated[str, Field(description="Период: 7d, 28d, 90d", default="7d")] = "7d",
    ) -> str:
        """Google Search Console: запросы, клики, позиции, CTR."""
        project = ctx.get_context()
        site_url = project.get("seo", {}).get("search_console_url", project["url"])
        return await run_search_console_report(site_url=site_url, config=config, cache=cache, period=period)

    @mcp.tool(annotations=READ_ONLY)
    async def traffic_sources(
        period: Annotated[str, Field(description="Период: 7d, 30d, 90d", default="7d")] = "7d",
    ) -> str:
        """Сводка по источникам трафика: поиск, соцсети, прямые, реферальные."""
        counter_id = _get_counter_id()
        if not counter_id:
            return "Укажите YANDEX_METRIKA_COUNTER или добавьте yandex_metrika_id в проект."
        return await run_traffic_sources(counter_id=counter_id, config=config, cache=cache, period=period)

    @mcp.tool(annotations=READ_ONLY)
    async def funnel_analysis(
        goal: Annotated[str | None, Field(description="Название цели (если не указана — первая цель)", default=None)] = None,
    ) -> str:
        """Анализ воронки конверсии: источник → визиты → цель → конверсия."""
        counter_id = _get_counter_id()
        if not counter_id:
            return "Укажите YANDEX_METRIKA_COUNTER или добавьте yandex_metrika_id в проект."
        return await run_funnel_analysis(counter_id=counter_id, config=config, cache=cache, goal=goal)

    @mcp.tool(annotations=READ_ONLY)
    async def weekly_digest() -> str:
        """Еженедельный дайджест: ключевые метрики, источники, тренды."""
        counter_id = _get_counter_id()
        if not counter_id:
            return "Укажите YANDEX_METRIKA_COUNTER или добавьте yandex_metrika_id в проект."
        project = ctx.get_context()
        project_name = project.get("name", "Проект")
        return await run_weekly_digest(counter_id=counter_id, project_name=project_name, config=config, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    async def ai_referral_report(
        period: Annotated[str, Field(description="Период: 7d, 30d, 90d", default="30d")] = "30d",
    ) -> str:
        """Трафик с AI-поисковиков: ChatGPT, Perplexity, Claude, Google AI Overviews."""
        counter_id = _get_counter_id()
        if not counter_id:
            return "Укажите YANDEX_METRIKA_COUNTER или добавьте yandex_metrika_id в проект."
        return await run_ai_referral_report(counter_id=counter_id, config=config, cache=cache, period=period)
```

Add the analyst resource registration after the `seo_expert_prompt` resource:

```python
    @mcp.resource("marketolog://prompts/analyst")
    def analyst_prompt() -> str:
        """Промпт аналитика."""
        return (prompts_dir / "analyst.md").read_text(encoding="utf-8")
```

- [ ] **Step 5: Run all tests**

Run: `pytest tests/ -v`
Expected: ALL PASS (78 old + ~24 new = ~102 tests)

- [ ] **Step 6: Commit**

```bash
git add src/marketolog/prompts/analyst.md src/marketolog/server.py tests/test_modules/test_analytics/test_integration.py
git commit -m "feat(analytics): register 8 analytics tools in MCP server + analyst prompt"
```

---

## Summary

| Task | Files | Tools | Tests |
|---|---|---|---|
| 1 | utm.py + conftest | generate_utm | 5 |
| 2 | metrika.py | metrika_report, metrika_goals | 5 |
| 3 | search_console.py | search_console_report | 3 |
| 4 | traffic_sources.py | traffic_sources | 3 |
| 5 | funnel.py | funnel_analysis | 3 |
| 6 | ai_referral.py | ai_referral_report | 3 |
| 7 | digest.py | weekly_digest | 3 |
| 8 | server.py + analyst.md + integration | Registration + prompt | 4 |
| **Total** | **~19 files** | **8 tools** | **~29 tests** |

After completion: **22 tools** in MCP server (6 Core + 8 SEO + 8 Analytics), **~107 tests**.
