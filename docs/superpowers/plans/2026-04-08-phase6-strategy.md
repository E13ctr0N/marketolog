# Phase 6: Strategy — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 7 Strategy tools (`analyze_target_audience`, `analyze_positioning`, `competitor_intelligence`, `marketing_plan`, `channel_recommendation`, `brand_health`, `ai_visibility`) to the Marketolog MCP server, all read-only except `marketing_plan` (mutating).

**Architecture:** Each tool is a pure function in `src/marketolog/modules/strategy/`, follows existing patterns (config/cache/project_context params, Exa/HTTP for external data, fallback when API not configured). Tools registered in `server.py` with proper `ToolAnnotations`. Prompt resource `strategist.md` already exists — no changes needed.

**Tech Stack:** Python 3.12, FastMCP, httpx, respx (tests), pytest-asyncio, Exa API (optional)

---

## File Structure

```
src/marketolog/modules/strategy/
├── __init__.py          — module docstring
├── audience.py          — analyze_target_audience
├── positioning.py       — analyze_positioning
├── intelligence.py      — competitor_intelligence (deep analysis via Exa + fetch)
├── planning.py          — marketing_plan
├── channels.py          — channel_recommendation
├── brand.py             — brand_health
└── ai_visibility.py     — ai_visibility (Exa-based AI mention monitoring)

tests/test_modules/test_strategy/
├── __init__.py
├── conftest.py          — shared fixtures (config_with_keys, config_no_keys, cache, project_context)
├── test_audience.py
├── test_positioning.py
├── test_intelligence.py
├── test_planning.py
├── test_channels.py
├── test_brand.py
├── test_ai_visibility.py
└── test_integration.py  — server registration, annotations, tool count (46)
```

Modify: `src/marketolog/server.py` — add 7 strategy tool imports + registrations.

---

### Task 1: Module scaffold + `analyze_target_audience`

**Files:**
- Create: `src/marketolog/modules/strategy/__init__.py`
- Create: `src/marketolog/modules/strategy/audience.py`
- Create: `tests/test_modules/test_strategy/__init__.py`
- Create: `tests/test_modules/test_strategy/conftest.py`
- Create: `tests/test_modules/test_strategy/test_audience.py`

- [ ] **Step 1: Create test fixtures**

`tests/test_modules/test_strategy/__init__.py` — empty file.

`tests/test_modules/test_strategy/conftest.py`:

```python
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
```

- [ ] **Step 2: Write failing test for `analyze_target_audience`**

`tests/test_modules/test_strategy/test_audience.py`:

```python
"""Tests for analyze_target_audience tool."""

import pytest

from marketolog.modules.strategy.audience import run_analyze_target_audience


def test_analyze_target_audience_with_existing_data(project_context):
    """When project has target_audience segments, builds detailed profiles."""
    result = run_analyze_target_audience(project_context=project_context)

    assert isinstance(result, str)
    assert "фрилансеры" in result
    assert "малые команды" in result.lower() or "малых команд" in result.lower()
    assert "управление проектами" in result  # niche context used


def test_analyze_target_audience_empty_segments(project_context):
    """When no audience segments — returns prompt for gathering info."""
    project_context["target_audience"] = []
    result = run_analyze_target_audience(project_context=project_context)

    assert isinstance(result, str)
    assert "update_project" in result or "целевая аудитория" in result.lower()


def test_analyze_target_audience_no_key(project_context):
    """Works without any API keys — pure context assembly."""
    result = run_analyze_target_audience(project_context=project_context)

    assert isinstance(result, str)
    assert len(result) > 100
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_strategy/test_audience.py -v`
Expected: FAIL (ModuleNotFoundError — strategy module doesn't exist)

- [ ] **Step 4: Create module scaffold and implement**

`src/marketolog/modules/strategy/__init__.py`:

```python
"""Strategy module — target audience, positioning, marketing plans, brand health."""
```

`src/marketolog/modules/strategy/audience.py`:

```python
"""Analyze target audience — build ICP profiles from project context.

Assembles audience portraits: who they are, their pains, motivations,
and preferred channels. Works from project context data alone (no API).
"""


def run_analyze_target_audience(project_context: dict) -> str:
    """Build target audience profiles from project context.

    Args:
        project_context: Full project context dict.

    Returns:
        Formatted audience analysis with ICP profiles.
    """
    segments = project_context.get("target_audience", [])
    niche = project_context.get("niche", "")
    description = project_context.get("description", "")
    social = project_context.get("social", {})
    url = project_context.get("url", "")

    if not segments:
        return (
            "## Целевая аудитория\n\n"
            "Сегменты ЦА ещё не определены.\n\n"
            "Для анализа добавьте сегменты через `update_project`:\n"
            '  update_project("target_audience", '
            '"[{segment: фрилансеры, pain: хаос в задачах}]")\n\n'
            "Или опишите свой продукт подробнее — я помогу определить ЦА."
        )

    lines = [
        f"## Анализ целевой аудитории",
        f"**Продукт:** {description}",
        f"**Ниша:** {niche}",
        f"**URL:** {url}",
        "",
    ]

    for i, seg in enumerate(segments, 1):
        segment_name = seg.get("segment", f"Сегмент {i}")
        pain = seg.get("pain", "не указано")

        lines.append(f"### Сегмент {i}: {segment_name}")
        lines.append("")
        lines.append(f"**Основная боль:** {pain}")
        lines.append("")
        lines.append("**Портрет (ICP):**")
        lines.append(f"- Ищет решение для: {pain}")
        lines.append(f"- Область: {niche}")
        lines.append(f"- Мотивация: избавиться от «{pain}», получить контроль и результат")
        lines.append("")

        # Channel recommendations based on available social
        channels = []
        if social.get("telegram_channel"):
            channels.append("Telegram (быстрые обновления, чат с аудиторией)")
        if social.get("vk_group"):
            channels.append("VK (сообщества, таргетированная реклама)")
        if social.get("max_channel"):
            channels.append("MAX (новая аудитория, бизнес-сегмент)")
        if social.get("telegram_dzen_channel"):
            channels.append("Дзен (SEO-трафик, длинный контент)")

        if channels:
            lines.append("**Каналы привлечения:**")
            for ch in channels:
                lines.append(f"- {ch}")
            lines.append("")

    lines.append("### Рекомендации")
    lines.append("1. Используйте `analyze_positioning` для формулировки УТП под каждый сегмент")
    lines.append("2. Используйте `channel_recommendation` для приоритизации каналов")
    lines.append("3. Используйте `marketing_plan` для плана действий")

    return "\n".join(lines)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_strategy/test_audience.py -v`
Expected: 3 PASSED

- [ ] **Step 6: Commit**

```bash
git add src/marketolog/modules/strategy/__init__.py src/marketolog/modules/strategy/audience.py tests/test_modules/test_strategy/__init__.py tests/test_modules/test_strategy/conftest.py tests/test_modules/test_strategy/test_audience.py
git commit -m "feat(strategy): add analyze_target_audience — ICP profiles from context"
```

---

### Task 2: `analyze_positioning`

**Files:**
- Create: `src/marketolog/modules/strategy/positioning.py`
- Create: `tests/test_modules/test_strategy/test_positioning.py`

- [ ] **Step 1: Write failing test**

`tests/test_modules/test_strategy/test_positioning.py`:

```python
"""Tests for analyze_positioning tool."""

import pytest

from marketolog.modules.strategy.positioning import run_analyze_positioning


def test_positioning_with_competitors(project_context):
    """Builds positioning map when competitors are present."""
    result = run_analyze_positioning(project_context=project_context)

    assert isinstance(result, str)
    assert "позиционирование" in result.lower() or "УТП" in result
    assert "Trello" in result or "конкурент" in result.lower()
    assert "управление проектами" in result


def test_positioning_no_competitors(project_context):
    """Without competitors — still gives positioning guidance."""
    project_context["competitors"] = []
    result = run_analyze_positioning(project_context=project_context)

    assert isinstance(result, str)
    assert len(result) > 50


def test_positioning_uses_audience(project_context):
    """Positioning references audience segments."""
    result = run_analyze_positioning(project_context=project_context)

    assert isinstance(result, str)
    # Should reference at least the niche
    assert "управление проектами" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_strategy/test_positioning.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement**

`src/marketolog/modules/strategy/positioning.py`:

```python
"""Analyze positioning — USP, differentiators, competitive gaps.

Assembles a positioning analysis from project context: compares against
known competitors and highlights unique strengths and weak spots.
"""


def run_analyze_positioning(project_context: dict) -> str:
    """Analyze product positioning vs competitors.

    Args:
        project_context: Full project context dict.

    Returns:
        Formatted positioning analysis with USP suggestions.
    """
    niche = project_context.get("niche", "")
    description = project_context.get("description", "")
    competitors = project_context.get("competitors", [])
    audience = project_context.get("target_audience", [])
    url = project_context.get("url", "")

    lines = [
        "## Анализ позиционирования",
        f"**Продукт:** {description}",
        f"**Ниша:** {niche}",
        "",
    ]

    # Competitor map
    if competitors:
        lines.append("### Карта конкурентов")
        lines.append("")
        for comp in competitors:
            name = comp.get("name", comp.get("url", "—"))
            comp_url = comp.get("url", "")
            lines.append(f"- **{name}**" + (f" ({comp_url})" if comp_url else ""))
        lines.append("")
        lines.append(f"Всего конкурентов в поле зрения: {len(competitors)}")
        lines.append("")
    else:
        lines.append("### Конкуренты")
        lines.append("Конкуренты не указаны. Добавьте через `update_project`:")
        lines.append('  update_project("competitors", "[{name: ..., url: ...}]")')
        lines.append("")

    # USP framework
    lines.append("### Формула УТП")
    lines.append("")
    lines.append(f"**[{description}]** помогает")

    if audience:
        segments_str = ", ".join(seg.get("segment", "") for seg in audience if seg.get("segment"))
        lines.append(f"**[{segments_str}]**")
    else:
        lines.append("**[целевой аудитории]**")

    if audience:
        pains = [seg.get("pain", "") for seg in audience if seg.get("pain")]
        if pains:
            lines.append(f"решить: {'; '.join(pains)}")

    lines.append("")

    # Differentiation axes
    lines.append("### Оси дифференциации")
    lines.append("")
    lines.append("Проверьте, по каким осям ваш продукт выигрывает:")
    lines.append("1. **Цена** — дешевле/бесплатнее конкурентов?")
    lines.append("2. **Простота** — быстрее настроить и начать работать?")
    lines.append("3. **Локализация** — лучше адаптирован под Рунет?")
    lines.append("4. **Фокус на сегмент** — заточен под конкретный сценарий?")
    lines.append("5. **Интеграции** — работает с нужными инструментами?")
    lines.append("")

    # Weak spots to address
    lines.append("### Потенциальные слабые стороны")
    lines.append("")
    if not competitors:
        lines.append("- Нет данных о конкурентах — сложно оценить позицию")
    if not audience:
        lines.append("- Нет сегментов ЦА — позиционирование размытое")
    lines.append("- Проверьте: достаточно ли чётко описан продукт на главной странице?")
    lines.append("- Проверьте: совпадает ли УТП с реальными болями аудитории?")
    lines.append("")

    lines.append("### Следующие шаги")
    lines.append("1. `competitor_intelligence` — глубокий анализ каждого конкурента")
    lines.append("2. `channel_recommendation` — где продвигаться")
    lines.append("3. `marketing_plan` — план действий с бюджетом")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_strategy/test_positioning.py -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/strategy/positioning.py tests/test_modules/test_strategy/test_positioning.py
git commit -m "feat(strategy): add analyze_positioning — USP and differentiation analysis"
```

---

### Task 3: `competitor_intelligence`

**Files:**
- Create: `src/marketolog/modules/strategy/intelligence.py`
- Create: `tests/test_modules/test_strategy/test_intelligence.py`

- [ ] **Step 1: Write failing test**

`tests/test_modules/test_strategy/test_intelligence.py`:

```python
"""Tests for competitor_intelligence tool."""

import httpx
import pytest
import respx

from marketolog.modules.strategy.intelligence import run_competitor_intelligence

EXA_API = "https://api.exa.ai/search"


@respx.mock
@pytest.mark.asyncio
async def test_intelligence_with_exa(config_with_keys, cache, project_context):
    """Deep competitor analysis using Exa API."""
    respx.post(EXA_API).mock(
        return_value=httpx.Response(200, json={
            "results": [
                {"title": "Trello pricing review", "url": "https://example.com/1", "text": "Trello offers free tier..."},
                {"title": "Trello vs alternatives", "url": "https://example.com/2", "text": "Comparison shows..."},
            ]
        })
    )

    result = await run_competitor_intelligence(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "Trello" in result
    assert "конкурент" in result.lower() or "анализ" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_intelligence_with_explicit_urls(config_with_keys, cache, project_context):
    """Analyze specific competitor URLs."""
    respx.post(EXA_API).mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    result = await run_competitor_intelligence(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
        competitor_urls=["https://competitor.ru"],
    )

    assert isinstance(result, str)
    assert len(result) > 50


@respx.mock
@pytest.mark.asyncio
async def test_intelligence_no_exa(config_no_keys, cache, project_context):
    """Without Exa — returns context-based analysis."""
    result = await run_competitor_intelligence(
        project_context=project_context,
        config=config_no_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "Trello" in result or "конкурент" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_intelligence_cached(config_with_keys, cache, project_context):
    """Cached result returned without API call."""
    cache_key = "test-saas:competitors"
    cache.set("competitor_intel", cache_key, "cached intel", ttl_seconds=3600)

    result = await run_competitor_intelligence(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
    )

    assert result == "cached intel"
    assert len(respx.calls) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_strategy/test_intelligence.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement**

`src/marketolog/modules/strategy/intelligence.py`:

```python
"""Competitor intelligence — deep analysis via Exa API + project context.

Searches Exa for competitor mentions, reviews, pricing info.
Falls back to context-based analysis when Exa is not configured.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

EXA_API = "https://api.exa.ai/search"
CACHE_NS = "competitor_intel"
CACHE_TTL = 3600  # 1 hour


async def run_competitor_intelligence(
    project_context: dict,
    *,
    config: MarketologConfig,
    cache: FileCache,
    competitor_urls: list[str] | None = None,
) -> str:
    """Deep competitor analysis: product, pricing, content, channels.

    Args:
        project_context: Full project context.
        config: App configuration (Exa API key optional).
        cache: File cache.
        competitor_urls: Override competitor URLs (optional).

    Returns:
        Formatted competitor intelligence report.
    """
    project_name = project_context.get("name", "project")
    cache_key = f"{project_name}:competitors"

    cached = cache.get(CACHE_NS, cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    competitors = competitor_urls or [
        c.get("url", "") for c in project_context.get("competitors", []) if c.get("url")
    ]
    competitor_names = [
        c.get("name", c.get("url", "")) for c in project_context.get("competitors", [])
    ]

    niche = project_context.get("niche", "")

    if config.is_configured("exa_api_key") and competitors:
        report = await _search_exa_competitors(competitors, competitor_names, niche, config)
    else:
        report = _fallback_analysis(competitor_names, competitors, niche, project_context)

    cache.set(CACHE_NS, cache_key, report, ttl_seconds=CACHE_TTL)
    return report


async def _search_exa_competitors(
    urls: list[str],
    names: list[str],
    niche: str,
    config: MarketologConfig,
) -> str:
    """Search Exa for competitor intelligence."""
    token: str = config.exa_api_key  # type: ignore[assignment]

    lines = ["## Конкурентная разведка\n"]

    for i, url in enumerate(urls):
        name = names[i] if i < len(names) else url

        query = f"{name} {niche} обзор отзывы цены 2026"
        body = {
            "query": query,
            "numResults": 5,
            "type": "auto",
        }

        resp = await fetch_with_retry(
            EXA_API,
            method="POST",
            headers={
                "x-api-key": token,
                "Content-Type": "application/json",
            },
            json=body,
        )

        lines.append(f"### {name}")
        lines.append(f"URL: {url}")
        lines.append("")

        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                lines.append(f"Найдено {len(results)} источников:")
                for j, item in enumerate(results, 1):
                    title = item.get("title", "Без заголовка")
                    item_url = item.get("url", "")
                    lines.append(f"  {j}. {title}")
                    if item_url:
                        lines.append(f"     {item_url}")
            else:
                lines.append("Дополнительных данных не найдено.")
        else:
            lines.append("Не удалось получить данные из Exa.")

        lines.append("")

    lines.append("### Рекомендации")
    lines.append("- Используйте `analyze_competitors` (SEO) для технического сравнения сайтов")
    lines.append("- Используйте `analyze_positioning` для формулировки УТП на основе отличий")
    lines.append("- Используйте `content_gap` для поиска упущенных тем в контенте")

    return "\n".join(lines)


def _fallback_analysis(
    names: list[str],
    urls: list[str],
    niche: str,
    project_context: dict,
) -> str:
    """Context-based competitor analysis without Exa."""
    lines = ["## Конкурентная разведка\n"]

    if not names and not urls:
        lines.append("Конкуренты не указаны в проекте.")
        lines.append('Добавьте через `update_project("competitors", "[{name: ..., url: ...}]")`')
        lines.append("")
    else:
        for i, name in enumerate(names):
            url = urls[i] if i < len(urls) else ""
            lines.append(f"### {name}")
            if url:
                lines.append(f"URL: {url}")
            lines.append("")
            lines.append("**Что проанализировать:**")
            lines.append(f"- Продукт: какие задачи в нише «{niche}» решает?")
            lines.append("- Ценообразование: бесплатный тариф? Стоимость?")
            lines.append("- Контент: блог, соцсети, частота публикаций?")
            lines.append("- SEO: по каким запросам ранжируется?")
            lines.append("- Соцсети: какие площадки, активность?")
            lines.append("")

    lines.append("### Для глубокого анализа")
    lines.append("Настройте Exa API для автоматического сбора данных:")
    lines.append("    EXA_API_KEY=<ваш ключ>")
    lines.append("Получить: https://exa.ai")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_strategy/test_intelligence.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/strategy/intelligence.py tests/test_modules/test_strategy/test_intelligence.py
git commit -m "feat(strategy): add competitor_intelligence — Exa-powered deep analysis"
```

---

### Task 4: `marketing_plan`

**Files:**
- Create: `src/marketolog/modules/strategy/planning.py`
- Create: `tests/test_modules/test_strategy/test_planning.py`

- [ ] **Step 1: Write failing test**

`tests/test_modules/test_strategy/test_planning.py`:

```python
"""Tests for marketing_plan tool."""

import pytest

from marketolog.modules.strategy.planning import run_marketing_plan


def test_marketing_plan_default(project_context):
    """Generates 3-month plan by default."""
    result = run_marketing_plan(project_context=project_context)

    assert isinstance(result, str)
    assert "маркетинговый план" in result.lower() or "план" in result.lower()
    assert "3 месяц" in result or "3 month" in result.lower() or "квартал" in result.lower()
    assert "управление проектами" in result


def test_marketing_plan_with_budget(project_context):
    """Plan includes budget allocation when provided."""
    result = run_marketing_plan(
        project_context=project_context,
        period="1 month",
        budget="50000",
    )

    assert isinstance(result, str)
    assert "50" in result  # budget referenced
    assert "1 month" in result.lower() or "1 месяц" in result


def test_marketing_plan_minimal_context(project_context):
    """Works with minimal project data."""
    minimal = {
        "name": "test",
        "url": "https://test.ru",
        "niche": "тестирование",
        "description": "Тестовый продукт",
    }
    result = run_marketing_plan(project_context=minimal)

    assert isinstance(result, str)
    assert len(result) > 100


def test_marketing_plan_includes_channels(project_context):
    """Plan references configured social channels."""
    result = run_marketing_plan(project_context=project_context)

    assert isinstance(result, str)
    # Should mention at least one configured channel
    assert "telegram" in result.lower() or "vk" in result.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_strategy/test_planning.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement**

`src/marketolog/modules/strategy/planning.py`:

```python
"""Marketing plan — goals, channels, budget, metrics, calendar.

Generates a structured marketing plan based on project context.
Adapts recommendations to project scale: budget, team, and stage.
"""


def run_marketing_plan(
    project_context: dict,
    *,
    period: str = "3 months",
    budget: str | None = None,
) -> str:
    """Generate a marketing plan.

    Args:
        project_context: Full project context.
        period: Planning period (e.g. "1 month", "3 months").
        budget: Optional monthly budget in RUB.

    Returns:
        Formatted marketing plan.
    """
    niche = project_context.get("niche", "")
    description = project_context.get("description", "")
    audience = project_context.get("target_audience", [])
    competitors = project_context.get("competitors", [])
    social = project_context.get("social", {})
    seo = project_context.get("seo", {})

    lines = [
        f"## Маркетинговый план",
        f"**Продукт:** {description}",
        f"**Ниша:** {niche}",
        f"**Период:** {period}",
    ]

    if budget:
        lines.append(f"**Бюджет:** {budget} ₽/мес")
    lines.append("")

    # Goals
    lines.append("### Цели")
    lines.append("")
    lines.append("1. **Узнаваемость** — привлечь целевой трафик на сайт")
    lines.append("2. **Вовлечение** — нарастить подписчиков в соцсетях")
    lines.append("3. **Конверсия** — увеличить количество регистраций/заявок")
    lines.append("")

    # Channels
    lines.append("### Каналы продвижения")
    lines.append("")

    channel_list = []
    if social.get("telegram_channel"):
        channel_list.append(("Telegram", social["telegram_channel"], "контент + комьюнити"))
    if social.get("vk_group"):
        channel_list.append(("VK", social["vk_group"], "контент + таргет"))
    if social.get("max_channel"):
        channel_list.append(("MAX", social["max_channel"], "бизнес-аудитория"))
    if social.get("telegram_dzen_channel"):
        channel_list.append(("Дзен", social["telegram_dzen_channel"], "SEO + длинный контент"))

    keywords = seo.get("main_keywords", [])
    if keywords:
        channel_list.append(("SEO", ", ".join(keywords[:3]), "органический трафик"))

    if channel_list:
        for name, detail, purpose in channel_list:
            lines.append(f"- **{name}** ({detail}) — {purpose}")
    else:
        lines.append("- Каналы не настроены. Добавьте через `update_project`.")
    lines.append("")

    # Budget allocation
    if budget:
        try:
            monthly = int(budget)
        except ValueError:
            monthly = 0

        if monthly > 0:
            lines.append("### Распределение бюджета")
            lines.append("")
            lines.append(f"| Статья | Доля | Сумма |")
            lines.append(f"|--------|------|-------|")
            lines.append(f"| Контент-производство | 40% | {int(monthly * 0.4):,} ₽ |")
            lines.append(f"| Таргетированная реклама | 30% | {int(monthly * 0.3):,} ₽ |")
            lines.append(f"| SEO и техработы | 20% | {int(monthly * 0.2):,} ₽ |")
            lines.append(f"| Инструменты и аналитика | 10% | {int(monthly * 0.1):,} ₽ |")
            lines.append("")

    # Metrics
    lines.append("### KPI и метрики")
    lines.append("")
    lines.append("- **Трафик:** визиты/неделю (отслеживать через `weekly_digest`)")
    lines.append("- **SEO:** позиции по ключевым запросам (`check_positions`)")
    lines.append("- **Соцсети:** подписчики, охват, вовлечённость (`telegram_stats`, `vk_stats`)")
    lines.append("- **Конверсия:** цели в Метрике (`funnel_analysis`)")
    lines.append("")

    # Calendar outline
    lines.append("### Календарный план")
    lines.append("")

    if "month" in period and period.startswith("1"):
        lines.append("**Неделя 1-2:** Аудит текущего состояния, настройка аналитики")
        lines.append("**Неделя 3-4:** Запуск контента, первые публикации")
    else:
        lines.append("**Месяц 1:** Аудит, стратегия, настройка каналов")
        lines.append("**Месяц 2:** Контент-маркетинг, SEO-оптимизация, соцсети")
        lines.append("**Месяц 3:** Масштабирование, анализ результатов, корректировка")
    lines.append("")

    # Audience context
    if audience:
        lines.append("### Целевая аудитория (контекст)")
        for seg in audience:
            lines.append(f"- {seg.get('segment', '—')}: {seg.get('pain', '—')}")
        lines.append("")

    lines.append("### Следующие шаги")
    lines.append("1. `seo_audit` — техническое состояние сайта")
    lines.append("2. `content_plan` — детальный контент-план")
    lines.append("3. `smm_calendar` — расписание публикаций")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_strategy/test_planning.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/strategy/planning.py tests/test_modules/test_strategy/test_planning.py
git commit -m "feat(strategy): add marketing_plan — goals, channels, budget, KPI"
```

---

### Task 5: `channel_recommendation`

**Files:**
- Create: `src/marketolog/modules/strategy/channels.py`
- Create: `tests/test_modules/test_strategy/test_channels.py`

- [ ] **Step 1: Write failing test**

`tests/test_modules/test_strategy/test_channels.py`:

```python
"""Tests for channel_recommendation tool."""

import pytest

from marketolog.modules.strategy.channels import run_channel_recommendation


def test_channel_recommendation(project_context):
    """Recommends channels based on project context."""
    result = run_channel_recommendation(project_context=project_context)

    assert isinstance(result, str)
    assert "канал" in result.lower() or "рекомендац" in result.lower()
    assert "ROI" in result or "эффективность" in result.lower()


def test_channel_recommendation_with_social(project_context):
    """References configured social channels."""
    result = run_channel_recommendation(project_context=project_context)

    assert isinstance(result, str)
    assert "telegram" in result.lower()


def test_channel_recommendation_no_social(project_context):
    """Without social channels — recommends setting them up."""
    project_context["social"] = {}
    result = run_channel_recommendation(project_context=project_context)

    assert isinstance(result, str)
    assert len(result) > 100
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_strategy/test_channels.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement**

`src/marketolog/modules/strategy/channels.py`:

```python
"""Channel recommendation — prioritized marketing channels with ROI forecast.

Analyzes project context to recommend the most effective channels,
accounting for niche, audience, budget, and available platforms.
"""

# Channel effectiveness data for Russian market (general benchmarks)
CHANNEL_DATA: dict[str, dict] = {
    "seo": {
        "name": "SEO (Яндекс + Google)",
        "roi_range": "высокий (3-6 мес для результатов)",
        "cost": "низкая (при самостоятельной работе)",
        "effort": "высокие (постоянная работа)",
        "best_for": "долгосрочный органический трафик",
        "tools": "`seo_audit`, `keyword_research`, `check_positions`",
    },
    "telegram": {
        "name": "Telegram-канал",
        "roi_range": "средний-высокий (1-3 мес)",
        "cost": "низкая",
        "effort": "средние (3-5 постов/нед)",
        "best_for": "прямая связь с аудиторией, B2B, tech-аудитория",
        "tools": "`telegram_post`, `telegram_stats`",
    },
    "vk": {
        "name": "VK-сообщество + таргет",
        "roi_range": "средний (1-2 мес)",
        "cost": "средняя (таргет от 5000₽/мес)",
        "effort": "средние",
        "best_for": "широкая аудитория, B2C, ретаргетинг",
        "tools": "`vk_post`, `vk_stats`",
    },
    "dzen": {
        "name": "Яндекс.Дзен",
        "roi_range": "средний (2-4 мес)",
        "cost": "низкая",
        "effort": "средние (2-3 статьи/нед)",
        "best_for": "SEO-трафик, длинный контент, экспертность",
        "tools": "`dzen_publish`",
    },
    "max": {
        "name": "MAX (VK мессенджер)",
        "roi_range": "низкий-средний (новая площадка)",
        "cost": "низкая",
        "effort": "низкие",
        "best_for": "ранний доступ к новой аудитории, бизнес-сегмент",
        "tools": "`max_post`, `max_stats`",
    },
    "content_marketing": {
        "name": "Контент-маркетинг (блог)",
        "roi_range": "высокий (3-6 мес)",
        "cost": "средняя",
        "effort": "высокие",
        "best_for": "экспертность, SEO, воронка продаж",
        "tools": "`content_plan`, `generate_article`, `optimize_text`",
    },
}


def run_channel_recommendation(project_context: dict) -> str:
    """Recommend marketing channels with ROI forecast.

    Args:
        project_context: Full project context.

    Returns:
        Prioritized channel recommendations.
    """
    niche = project_context.get("niche", "")
    social = project_context.get("social", {})
    audience = project_context.get("target_audience", [])
    seo = project_context.get("seo", {})

    lines = [
        "## Рекомендация каналов продвижения",
        f"**Ниша:** {niche}",
        "",
    ]

    # Score and rank channels
    scored = _score_channels(social, audience, seo)

    lines.append("### Приоритет каналов (от высокого к низкому)")
    lines.append("")

    for rank, (channel_id, score, reason) in enumerate(scored, 1):
        data = CHANNEL_DATA[channel_id]
        configured = _is_configured(channel_id, social, seo)
        status = "✓ настроен" if configured else "✗ не настроен"

        lines.append(f"#### {rank}. {data['name']} [{status}]")
        lines.append(f"- **Прогноз ROI:** {data['roi_range']}")
        lines.append(f"- **Затраты:** {data['cost']}")
        lines.append(f"- **Трудозатраты:** {data['effort']}")
        lines.append(f"- **Лучше всего для:** {data['best_for']}")
        lines.append(f"- **Почему рекомендуем:** {reason}")
        lines.append(f"- **Инструменты:** {data['tools']}")
        lines.append("")

    lines.append("### Рекомендация")
    top = scored[0] if scored else None
    if top:
        top_name = CHANNEL_DATA[top[0]]["name"]
        lines.append(f"Начните с **{top_name}** — это даст максимальную отдачу при текущих ресурсах.")
    lines.append("Используйте `marketing_plan` для детального плана по выбранным каналам.")

    return "\n".join(lines)


def _score_channels(
    social: dict,
    audience: list[dict],
    seo: dict,
) -> list[tuple[str, int, str]]:
    """Score channels by relevance. Returns sorted (id, score, reason)."""
    scores: list[tuple[str, int, str]] = []

    # SEO — always high value
    has_keywords = bool(seo.get("main_keywords"))
    seo_score = 90 if has_keywords else 70
    scores.append(("seo", seo_score, "органический трафик — самый дешёвый в долгосроке"))

    # Telegram — great for B2B, tech
    has_tg = bool(social.get("telegram_channel"))
    tg_score = 85 if has_tg else 60
    scores.append(("telegram", tg_score, "прямой канал связи, высокая вовлечённость" if has_tg else "рекомендуем создать канал"))

    # Content marketing
    scores.append(("content_marketing", 75, "экспертный контент усиливает все остальные каналы"))

    # VK
    has_vk = bool(social.get("vk_group"))
    vk_score = 70 if has_vk else 50
    scores.append(("vk", vk_score, "широкий охват + таргетированная реклама" if has_vk else "полезен для B2C-аудитории"))

    # Dzen
    has_dzen = bool(social.get("telegram_dzen_channel"))
    dzen_score = 65 if has_dzen else 45
    scores.append(("dzen", dzen_score, "двойной эффект: контент + SEO" if has_dzen else "полезен для SEO-трафика"))

    # MAX
    has_max = bool(social.get("max_channel"))
    max_score = 40 if has_max else 25
    scores.append(("max", max_score, "новая площадка — низкая конкуренция"))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def _is_configured(channel_id: str, social: dict, seo: dict) -> bool:
    """Check if a channel is configured in the project."""
    mapping = {
        "seo": bool(seo.get("main_keywords")),
        "telegram": bool(social.get("telegram_channel")),
        "vk": bool(social.get("vk_group")),
        "dzen": bool(social.get("telegram_dzen_channel")),
        "max": bool(social.get("max_channel")),
        "content_marketing": True,  # always available
    }
    return mapping.get(channel_id, False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_strategy/test_channels.py -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/strategy/channels.py tests/test_modules/test_strategy/test_channels.py
git commit -m "feat(strategy): add channel_recommendation — prioritized channels with ROI"
```

---

### Task 6: `brand_health`

**Files:**
- Create: `src/marketolog/modules/strategy/brand.py`
- Create: `tests/test_modules/test_strategy/test_brand.py`

- [ ] **Step 1: Write failing test**

`tests/test_modules/test_strategy/test_brand.py`:

```python
"""Tests for brand_health tool."""

import httpx
import pytest
import respx

from marketolog.modules.strategy.brand import run_brand_health

EXA_API = "https://api.exa.ai/search"


@respx.mock
@pytest.mark.asyncio
async def test_brand_health_with_exa(config_with_keys, cache, project_context):
    """Brand monitoring via Exa API."""
    respx.post(EXA_API).mock(
        return_value=httpx.Response(200, json={
            "results": [
                {"title": "my-saas review", "url": "https://review.com/1"},
                {"title": "Отзывы my-saas", "url": "https://review.com/2"},
            ]
        })
    )

    result = await run_brand_health(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "бренд" in result.lower() or "упоминан" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_brand_health_no_exa(config_no_keys, cache, project_context):
    """Without Exa — returns guidance."""
    result = await run_brand_health(
        project_context=project_context,
        config=config_no_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "exa" in result.lower() or "настройте" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_brand_health_cached(config_with_keys, cache, project_context):
    """Cached result returned."""
    cache.set("brand_health", "test-saas", "cached brand", ttl_seconds=3600)

    result = await run_brand_health(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
    )

    assert result == "cached brand"
    assert len(respx.calls) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_strategy/test_brand.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement**

`src/marketolog/modules/strategy/brand.py`:

```python
"""Brand health — mentions, reviews, sentiment monitoring.

Uses Exa API to search for brand mentions across the web.
Falls back to a manual checklist when Exa is not configured.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

EXA_API = "https://api.exa.ai/search"
CACHE_NS = "brand_health"
CACHE_TTL = 3600  # 1 hour


async def run_brand_health(
    project_context: dict,
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    """Monitor brand health: mentions, reviews, dynamics.

    Args:
        project_context: Full project context.
        config: App configuration (Exa API key optional).
        cache: File cache.

    Returns:
        Brand health report.
    """
    project_name = project_context.get("name", "project")

    cached = cache.get(CACHE_NS, project_name)
    if cached is not None:
        return cached  # type: ignore[return-value]

    if config.is_configured("exa_api_key"):
        report = await _search_brand_mentions(project_context, config)
    else:
        report = _fallback_checklist(project_context)

    cache.set(CACHE_NS, project_name, report, ttl_seconds=CACHE_TTL)
    return report


async def _search_brand_mentions(project_context: dict, config: MarketologConfig) -> str:
    """Search Exa for brand mentions."""
    token: str = config.exa_api_key  # type: ignore[assignment]
    name = project_context.get("name", "")
    url = project_context.get("url", "")
    niche = project_context.get("niche", "")

    lines = [
        "## Здоровье бренда",
        f"**Бренд:** {name}",
        f"**URL:** {url}",
        "",
    ]

    # Search for mentions
    queries = [
        f'"{name}" отзывы {niche}',
        f'"{name}" обзор',
    ]

    all_results = []
    for query in queries:
        body = {
            "query": query,
            "numResults": 5,
            "type": "auto",
        }

        resp = await fetch_with_retry(
            EXA_API,
            method="POST",
            headers={
                "x-api-key": token,
                "Content-Type": "application/json",
            },
            json=body,
        )

        if resp.status_code == 200:
            results = resp.json().get("results", [])
            all_results.extend(results)

    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique_results = []
    for item in all_results:
        item_url = item.get("url", "")
        if item_url not in seen_urls:
            seen_urls.add(item_url)
            unique_results.append(item)

    lines.append(f"### Упоминания ({len(unique_results)} найдено)")
    lines.append("")

    if unique_results:
        for i, item in enumerate(unique_results, 1):
            title = item.get("title", "Без заголовка")
            item_url = item.get("url", "")
            lines.append(f"{i}. **{title}**")
            if item_url:
                lines.append(f"   {item_url}")
    else:
        lines.append("Упоминаний не найдено. Это может означать:")
        lines.append("- Бренд ещё не набрал достаточно упоминаний")
        lines.append("- Название бренда слишком общее")
    lines.append("")

    lines.append("### Рекомендации")
    lines.append("- Используйте `ai_visibility` для проверки упоминаний в AI-поисковиках")
    lines.append("- Отслеживайте динамику: запускайте `brand_health` еженедельно")
    lines.append("- Работайте с отзывами: отвечайте на негатив, поощряйте позитив")

    return "\n".join(lines)


def _fallback_checklist(project_context: dict) -> str:
    """Brand health checklist without Exa."""
    name = project_context.get("name", "")

    lines = [
        "## Здоровье бренда",
        f"**Бренд:** {name}",
        "",
        "### Ручной чек-лист",
        "",
        "Для автоматического мониторинга настройте Exa API:",
        "    EXA_API_KEY=<ваш ключ>",
        "Получить: https://exa.ai",
        "",
        "Пока API не настроен, проверьте вручную:",
        "",
        f'1. Поищите "{name}" в Яндексе — что на первой странице?',
        f'2. Поищите "{name} отзывы" — есть ли отзывы? Какой тон?',
        f'3. Проверьте упоминания в соцсетях: VK, Telegram',
        f'4. Проверьте рейтинги на отзовиках (если применимо)',
        f'5. Поищите "{name}" в ChatGPT / Perplexity — что отвечают AI?',
        "",
        "### Инструменты",
        "- `ai_visibility` — автоматическая проверка AI-упоминаний",
        "- `trend_research` — тренды в вашей нише",
    ]

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_strategy/test_brand.py -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/strategy/brand.py tests/test_modules/test_strategy/test_brand.py
git commit -m "feat(strategy): add brand_health — Exa-powered mention monitoring"
```

---

### Task 7: `ai_visibility`

**Files:**
- Create: `src/marketolog/modules/strategy/ai_visibility.py`
- Create: `tests/test_modules/test_strategy/test_ai_visibility.py`

- [ ] **Step 1: Write failing test**

`tests/test_modules/test_strategy/test_ai_visibility.py`:

```python
"""Tests for ai_visibility tool."""

import httpx
import pytest
import respx

from marketolog.modules.strategy.ai_visibility import run_ai_visibility

EXA_API = "https://api.exa.ai/search"


@respx.mock
@pytest.mark.asyncio
async def test_ai_visibility_with_exa(config_with_keys, cache, project_context):
    """AI visibility check via Exa API."""
    respx.post(EXA_API).mock(
        return_value=httpx.Response(200, json={
            "results": [
                {"title": "ChatGPT recommends my-saas", "url": "https://ai.com/1"},
                {"title": "Claude mentions my-saas", "url": "https://ai.com/2"},
            ]
        })
    )

    result = await run_ai_visibility(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "AI" in result or "ИИ" in result


@respx.mock
@pytest.mark.asyncio
async def test_ai_visibility_custom_brand(config_with_keys, cache, project_context):
    """Override brand_name parameter."""
    respx.post(EXA_API).mock(
        return_value=httpx.Response(200, json={"results": []})
    )

    result = await run_ai_visibility(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
        brand_name="CustomBrand",
    )

    assert isinstance(result, str)
    assert "CustomBrand" in result


@respx.mock
@pytest.mark.asyncio
async def test_ai_visibility_no_exa(config_no_keys, cache, project_context):
    """Without Exa — returns setup guidance."""
    result = await run_ai_visibility(
        project_context=project_context,
        config=config_no_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "exa" in result.lower() or "настройте" in result.lower()


@respx.mock
@pytest.mark.asyncio
async def test_ai_visibility_cached(config_with_keys, cache, project_context):
    """Cached result returned."""
    cache.set("ai_visibility", "test-saas", "cached ai viz", ttl_seconds=3600)

    result = await run_ai_visibility(
        project_context=project_context,
        config=config_with_keys,
        cache=cache,
    )

    assert result == "cached ai viz"
    assert len(respx.calls) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_strategy/test_ai_visibility.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement**

`src/marketolog/modules/strategy/ai_visibility.py`:

```python
"""AI visibility — monitor brand mentions in AI search answers.

Checks how AI assistants (ChatGPT, Claude, Perplexity, Google AI)
reference the brand. Uses Exa API to find AI-generated content
mentioning the brand.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

EXA_API = "https://api.exa.ai/search"
CACHE_NS = "ai_visibility"
CACHE_TTL = 7200  # 2 hours

AI_PLATFORMS = [
    ("ChatGPT", "chatgpt.com"),
    ("Perplexity", "perplexity.ai"),
    ("Google AI", "google.com/search AI overview"),
    ("Claude", "claude.ai"),
]


async def run_ai_visibility(
    project_context: dict,
    *,
    config: MarketologConfig,
    cache: FileCache,
    brand_name: str | None = None,
) -> str:
    """Monitor brand mentions in AI search answers.

    Args:
        project_context: Full project context.
        config: App configuration (Exa API key required).
        cache: File cache.
        brand_name: Override brand name (default: project name).

    Returns:
        AI visibility report.
    """
    name = brand_name or project_context.get("name", "project")

    cached = cache.get(CACHE_NS, name)
    if cached is not None:
        return cached  # type: ignore[return-value]

    if not config.is_configured("exa_api_key"):
        return _setup_instructions(name)

    report = await _check_ai_mentions(name, project_context, config)

    cache.set(CACHE_NS, name, report, ttl_seconds=CACHE_TTL)
    return report


async def _check_ai_mentions(
    brand_name: str,
    project_context: dict,
    config: MarketologConfig,
) -> str:
    """Search Exa for AI-generated content mentioning the brand."""
    token: str = config.exa_api_key  # type: ignore[assignment]
    niche = project_context.get("niche", "")
    url = project_context.get("url", "")

    lines = [
        "## AI-видимость бренда",
        f"**Бренд:** {brand_name}",
        f"**URL:** {url}",
        "",
    ]

    # Search for brand in AI-related contexts
    queries = [
        f'"{brand_name}" AI рекомендация {niche}',
        f'"{brand_name}" лучшие инструменты {niche} 2026',
    ]

    all_results = []
    for query in queries:
        body = {
            "query": query,
            "numResults": 5,
            "type": "auto",
        }

        resp = await fetch_with_retry(
            EXA_API,
            method="POST",
            headers={
                "x-api-key": token,
                "Content-Type": "application/json",
            },
            json=body,
        )

        if resp.status_code == 200:
            results = resp.json().get("results", [])
            all_results.extend(results)

    # Deduplicate
    seen_urls: set[str] = set()
    unique_results = []
    for item in all_results:
        item_url = item.get("url", "")
        if item_url not in seen_urls:
            seen_urls.add(item_url)
            unique_results.append(item)

    lines.append(f"### Упоминания в AI-контексте ({len(unique_results)} найдено)")
    lines.append("")

    if unique_results:
        for i, item in enumerate(unique_results, 1):
            title = item.get("title", "Без заголовка")
            item_url = item.get("url", "")
            lines.append(f"{i}. **{title}**")
            if item_url:
                lines.append(f"   {item_url}")
    else:
        lines.append(f"Упоминаний «{brand_name}» в AI-контексте не найдено.")
    lines.append("")

    # AI platform checklist
    lines.append("### Проверка по AI-платформам")
    lines.append("")
    lines.append("Рекомендуем проверить вручную:")
    for platform_name, domain in AI_PLATFORMS:
        lines.append(f"- **{platform_name}** — спросите: «какие инструменты для {niche}?»")
    lines.append("")

    # Recommendations
    lines.append("### Как улучшить AI-видимость")
    lines.append("")
    lines.append("1. **llms.txt** — добавьте файл (проверьте через `ai_seo_check`)")
    lines.append("2. **Schema markup** — структурированные данные помогают AI понять контент")
    lines.append("3. **Экспертный контент** — AI цитирует авторитетные источники")
    lines.append("4. **Упоминания на авторитетных сайтах** — AI обучается на публичных данных")
    lines.append("5. **Уникальные данные** — исследования и отчёты повышают цитируемость")

    return "\n".join(lines)


def _setup_instructions(brand_name: str) -> str:
    """Return setup instructions when Exa is not configured."""
    return (
        f"## AI-видимость: {brand_name}\n\n"
        "Для мониторинга AI-упоминаний настройте Exa API:\n\n"
        "    EXA_API_KEY=<ваш ключ>\n"
        "Получить: https://exa.ai\n\n"
        "Пока API не настроен, проверьте вручную:\n"
        f'1. ChatGPT: "какие инструменты для [ваша ниша]?"\n'
        f'2. Perplexity: "{brand_name} обзор"\n'
        f'3. Claude: "порекомендуй [ваша ниша]"\n\n'
        "Используйте `ai_seo_check` для проверки технической готовности к AI-поиску."
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_strategy/test_ai_visibility.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/strategy/ai_visibility.py tests/test_modules/test_strategy/test_ai_visibility.py
git commit -m "feat(strategy): add ai_visibility — AI search mention monitoring"
```

---

### Task 8: Register 7 Strategy tools in MCP server + integration tests

**Files:**
- Modify: `src/marketolog/server.py`
- Create: `tests/test_modules/test_strategy/test_integration.py`

- [ ] **Step 1: Write failing integration test**

`tests/test_modules/test_strategy/test_integration.py`:

```python
"""Integration tests — Strategy tools registered in MCP server."""

import asyncio
import pytest
from pathlib import Path

from marketolog.server import create_server


@pytest.fixture
def server(tmp_marketolog_dir: Path):
    return create_server(base_dir=tmp_marketolog_dir)


def test_server_has_strategy_tools(server):
    """Server must expose all 7 Strategy tools."""
    tools = asyncio.run(server._local_provider.list_tools())
    tool_names = {t.name for t in tools}
    expected_strategy = {
        "analyze_target_audience",
        "analyze_positioning",
        "competitor_intelligence",
        "marketing_plan",
        "channel_recommendation",
        "brand_health",
        "ai_visibility",
    }
    assert expected_strategy.issubset(tool_names), f"Missing: {expected_strategy - tool_names}"


def test_strategy_readonly_tools(server):
    """Analysis tools should be readOnlyHint=True."""
    tools = asyncio.run(server._local_provider.list_tools())
    readonly_tools = {
        "analyze_target_audience",
        "analyze_positioning",
        "competitor_intelligence",
        "channel_recommendation",
        "brand_health",
        "ai_visibility",
    }
    for tool in tools:
        if tool.name in readonly_tools:
            assert tool.annotations is not None, f"{tool.name} has no annotations"
            assert tool.annotations.readOnlyHint is True, f"{tool.name} should be READ_ONLY"


def test_marketing_plan_is_mutating(server):
    """marketing_plan should have readOnlyHint=False (creates plan document)."""
    tools = asyncio.run(server._local_provider.list_tools())
    for tool in tools:
        if tool.name == "marketing_plan":
            assert tool.annotations is not None
            assert tool.annotations.readOnlyHint is False, "marketing_plan should be MUTATING"
            break
    else:
        pytest.fail("marketing_plan tool not found")


def test_total_tool_count(server):
    """Server should have exactly 46 tools (6 Core + 8 SEO + 8 Analytics + 7 Content + 10 SMM + 7 Strategy)."""
    tools = asyncio.run(server._local_provider.list_tools())
    assert len(tools) == 46, f"Expected 46 tools, got {len(tools)}: {[t.name for t in tools]}"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_strategy/test_integration.py -v`
Expected: FAIL (strategy tools not registered yet)

- [ ] **Step 3: Register strategy tools in `server.py`**

Add imports after the SMM imports (after line 45 in `src/marketolog/server.py`):

```python
from marketolog.modules.strategy.audience import run_analyze_target_audience
from marketolog.modules.strategy.positioning import run_analyze_positioning
from marketolog.modules.strategy.intelligence import run_competitor_intelligence
from marketolog.modules.strategy.planning import run_marketing_plan
from marketolog.modules.strategy.channels import run_channel_recommendation
from marketolog.modules.strategy.brand import run_brand_health
from marketolog.modules.strategy.ai_visibility import run_ai_visibility
```

Add tool registrations after the SMM tools section (after line 483), before the `# --- Prompt Resources ---` section:

```python
    # --- Strategy Tools ---

    @mcp.tool(annotations=READ_ONLY)
    def analyze_target_audience() -> str:
        """Портреты ЦА (ICP): кто, боли, мотивация, каналы."""
        project = ctx.get_context()
        return run_analyze_target_audience(project_context=project)

    @mcp.tool(annotations=READ_ONLY)
    def analyze_positioning() -> str:
        """Позиционирование: отличия от конкурентов, УТП, слабые стороны."""
        project = ctx.get_context()
        return run_analyze_positioning(project_context=project)

    @mcp.tool(annotations=READ_ONLY)
    async def competitor_intelligence(
        competitor_urls: Annotated[list[str] | None, Field(description="URL конкурентов. Если не указаны — из проекта", default=None)] = None,
    ) -> str:
        """Глубокий анализ конкурентов: продукт, цены, контент, соцсети, SEO, каналы."""
        project = ctx.get_context()
        return await run_competitor_intelligence(
            project_context=project, config=config, cache=cache, competitor_urls=competitor_urls,
        )

    @mcp.tool(annotations=MUTATING)
    def marketing_plan(
        period: Annotated[str, Field(description="Период: '1 month', '3 months', '6 months'", default="3 months")] = "3 months",
        budget: Annotated[str | None, Field(description="Месячный бюджет в рублях", default=None)] = None,
    ) -> str:
        """Маркетинговый план: цели, каналы, бюджет, метрики, календарь."""
        project = ctx.get_context()
        return run_marketing_plan(project_context=project, period=period, budget=budget)

    @mcp.tool(annotations=READ_ONLY)
    def channel_recommendation() -> str:
        """Рекомендация каналов продвижения с прогнозом ROI."""
        project = ctx.get_context()
        return run_channel_recommendation(project_context=project)

    @mcp.tool(annotations=READ_ONLY)
    async def brand_health() -> str:
        """Здоровье бренда: упоминания, отзывы, динамика."""
        project = ctx.get_context()
        return await run_brand_health(project_context=project, config=config, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    async def ai_visibility(
        brand_name: Annotated[str | None, Field(description="Название бренда. Если не указано — из проекта", default=None)] = None,
    ) -> str:
        """Мониторинг упоминаний бренда в AI-ответах (ChatGPT, Claude, Perplexity)."""
        project = ctx.get_context()
        return await run_ai_visibility(
            project_context=project, config=config, cache=cache, brand_name=brand_name,
        )
```

- [ ] **Step 4: Update existing SMM integration test tool count**

In `tests/test_modules/test_smm/test_integration.py`, update `test_total_tool_count`:

```python
def test_total_tool_count(server):
    """Server should have exactly 46 tools (6 Core + 8 SEO + 8 Analytics + 7 Content + 10 SMM + 7 Strategy)."""
    tools = asyncio.run(server._local_provider.list_tools())
    assert len(tools) == 46, f"Expected 46 tools, got {len(tools)}: {[t.name for t in tools]}"
```

- [ ] **Step 5: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS (previous 159 + new ~24 strategy tests)

- [ ] **Step 6: Commit**

```bash
git add src/marketolog/server.py tests/test_modules/test_strategy/test_integration.py tests/test_modules/test_smm/test_integration.py
git commit -m "feat(strategy): register 7 Strategy tools in MCP server"
```

---

### Summary

| Task | Tool(s) | Tests | Type |
|------|---------|-------|------|
| 1 | `analyze_target_audience` | 3 | sync, context-only |
| 2 | `analyze_positioning` | 3 | sync, context-only |
| 3 | `competitor_intelligence` | 4 | async, Exa API |
| 4 | `marketing_plan` | 4 | sync, context-only |
| 5 | `channel_recommendation` | 3 | sync, context-only |
| 6 | `brand_health` | 3 | async, Exa API |
| 7 | `ai_visibility` | 4 | async, Exa API |
| 8 | Server registration + integration | 4 | integration |

**Total: 7 tools, 28 tests, 8 commits**
