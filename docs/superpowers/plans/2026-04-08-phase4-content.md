# Phase 4: Content Module — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 7 Content tools to the Marketolog MCP server: content planning, article/post generation (context assembly for Claude), text optimization, content analysis, meta generation, and content repurposing.

**Architecture:** Content tools do NOT generate text themselves — they assemble context (SEO data, tone of voice, keywords, platform format) and return structured prompts/data to Claude. Claude generates text using this context + the `content_writer.md` role prompt. Each tool lives in a focused file under `src/marketolog/modules/content/`. Tools use `FileCache`, `fetch_with_retry`, `format_tabular` from shared utils. All are `READ_ONLY`.

**Tech Stack:** Python 3.12, FastMCP, httpx, BeautifulSoup + lxml (for analyze_content), pytest + pytest-asyncio + respx

---

## File Structure

| File | Responsibility |
|---|---|
| `src/marketolog/modules/content/__init__.py` | Package marker |
| `src/marketolog/modules/content/planner.py` | `run_content_plan()` — generates content calendar with topics, formats, keywords |
| `src/marketolog/modules/content/generator.py` | `run_generate_article()`, `run_generate_post()`, `run_repurpose_content()` — context assembly for Claude |
| `src/marketolog/modules/content/optimizer.py` | `run_optimize_text()` — SEO text analysis with keyword density, structure check |
| `src/marketolog/modules/content/analyzer.py` | `run_analyze_content()` — fetches URL, analyzes readability + SEO signals |
| `src/marketolog/modules/content/meta.py` | `run_generate_meta()` — generates title/description/H1 suggestions |
| `src/marketolog/prompts/content_writer.md` | Content writer role prompt |
| `src/marketolog/server.py` | Register 7 content tools + content_writer resource |
| `tests/test_modules/test_content/conftest.py` | Shared fixtures |
| `tests/test_modules/test_content/test_planner.py` | Tests for content_plan |
| `tests/test_modules/test_content/test_generator.py` | Tests for generate_article, generate_post, repurpose_content |
| `tests/test_modules/test_content/test_optimizer.py` | Tests for optimize_text |
| `tests/test_modules/test_content/test_analyzer.py` | Tests for analyze_content |
| `tests/test_modules/test_content/test_meta.py` | Tests for generate_meta |
| `tests/test_modules/test_content/test_integration.py` | Server integration: 29 tools, resources, annotations |

---

### Task 1: Package scaffolding + content_plan

**Files:**
- Create: `src/marketolog/modules/content/__init__.py`
- Create: `src/marketolog/modules/content/planner.py`
- Create: `tests/test_modules/test_content/__init__.py`
- Create: `tests/test_modules/test_content/conftest.py`
- Create: `tests/test_modules/test_content/test_planner.py`

- [ ] **Step 1: Create package dirs and conftest**

```python
# src/marketolog/modules/content/__init__.py
"""Content module — planning, generation, optimization, analysis."""
```

```python
# tests/test_modules/test_content/__init__.py
```

```python
# tests/test_modules/test_content/conftest.py
from pathlib import Path

import pytest

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache


@pytest.fixture
def config_with_keys() -> MarketologConfig:
    """Config with relevant API keys set."""
    return MarketologConfig(
        yandex_oauth_token="test-yandex-token",
        pagespeed_api_key="test-pagespeed-key",
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
    """Minimal project context for content tools."""
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
        "seo": {
            "main_keywords": ["таск трекер", "управление задачами"],
        },
        "competitors": [
            {"name": "Trello", "url": "https://trello.com"},
        ],
        "social": {
            "telegram_channel": "@mysaas_channel",
            "vk_group": "mysaas",
        },
    }
```

- [ ] **Step 2: Write failing tests for content_plan**

```python
# tests/test_modules/test_content/test_planner.py
"""Tests for content plan tool."""

import pytest

from marketolog.modules.content.planner import run_content_plan


def test_content_plan_basic(project_context):
    """Content plan returns structured plan with topics."""
    result = run_content_plan(
        project_context=project_context,
        period="2 weeks",
        topics_count=5,
    )

    assert isinstance(result, str)
    assert "контент" in result.lower() or "план" in result.lower()
    # Should include project niche context
    assert "управление проектами" in result or "таск трекер" in result
    # Should have numbered topics
    assert "1." in result or "1)" in result


def test_content_plan_includes_keywords(project_context):
    """Plan should reference SEO keywords from project."""
    result = run_content_plan(
        project_context=project_context,
        period="1 month",
        topics_count=3,
    )

    # Should mention keywords from project context
    assert "таск трекер" in result or "управление задачами" in result


def test_content_plan_includes_audience(project_context):
    """Plan should reference target audience."""
    result = run_content_plan(
        project_context=project_context,
        period="1 week",
        topics_count=3,
    )

    # Should mention audience segments
    assert "фрилансер" in result.lower() or "команд" in result.lower()


def test_content_plan_default_params(project_context):
    """Plan works with default parameters."""
    result = run_content_plan(project_context=project_context)

    assert isinstance(result, str)
    assert len(result) > 100  # Should be substantial
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_content/test_planner.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement planner.py**

```python
# src/marketolog/modules/content/planner.py
"""Content plan generator — assembles context for Claude to create a content calendar.

This tool does NOT generate the plan itself. It collects project context
(niche, keywords, audience, tone, competitors, channels) and returns a
structured brief that Claude uses with content_writer.md prompt.
"""


def run_content_plan(
    project_context: dict,
    period: str = "2 weeks",
    topics_count: int = 10,
) -> str:
    """Assemble content planning context for Claude.

    Args:
        project_context: Full project context dict.
        period: Planning period (e.g. "1 week", "2 weeks", "1 month").
        topics_count: Number of topics to suggest.

    Returns:
        Structured brief for Claude to generate a content plan.
    """
    name = project_context.get("name", "Проект")
    niche = project_context.get("niche", "")
    description = project_context.get("description", "")
    tone = project_context.get("tone_of_voice", "нейтральный")

    keywords = project_context.get("seo", {}).get("main_keywords", [])
    audience = project_context.get("target_audience", [])
    competitors = project_context.get("competitors", [])
    social = project_context.get("social", {})

    lines = [
        f"## Контент-план: {name}",
        f"**Период:** {period}",
        f"**Количество тем:** {topics_count}",
        "",
        "### Контекст проекта",
        f"- **Ниша:** {niche}",
        f"- **Описание:** {description}",
        f"- **Tone of voice:** {tone}",
        "",
    ]

    if keywords:
        lines.append("### SEO-ключевые слова")
        for kw in keywords:
            lines.append(f"- {kw}")
        lines.append("")

    if audience:
        lines.append("### Целевая аудитория")
        for seg in audience:
            segment = seg.get("segment", "")
            pain = seg.get("pain", "")
            lines.append(f"- **{segment}**: {pain}")
        lines.append("")

    if competitors:
        lines.append("### Конкуренты (для контент-дифференциации)")
        for comp in competitors:
            lines.append(f"- {comp.get('name', '')} ({comp.get('url', '')})")
        lines.append("")

    channels = []
    if social.get("telegram_channel"):
        channels.append("Telegram")
    if social.get("vk_group"):
        channels.append("VK")
    if social.get("max_channel"):
        channels.append("MAX")
    if social.get("telegram_dzen_channel"):
        channels.append("Дзен")

    if channels:
        lines.append(f"### Каналы: {', '.join(channels)}")
        lines.append("")

    lines.append("### Задание")
    lines.append(f"Составь контент-план на {period} из {topics_count} тем.")
    lines.append("Для каждой темы укажи:")
    lines.append("1. Заголовок")
    lines.append("2. Формат (статья, пост, карусель, видео-скрипт)")
    lines.append("3. Целевые ключевые слова")
    lines.append("4. Площадка (блог, Telegram, VK, Дзен)")
    lines.append("5. Целевая аудитория (какой сегмент)")
    lines.append("6. Краткий тезис (о чём)")

    return "\n".join(lines)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_content/test_planner.py -v`
Expected: PASS (all 4 tests)

- [ ] **Step 6: Commit**

```bash
git add src/marketolog/modules/content/__init__.py src/marketolog/modules/content/planner.py tests/test_modules/test_content/__init__.py tests/test_modules/test_content/conftest.py tests/test_modules/test_content/test_planner.py
git commit -m "feat(content): add content_plan — content calendar context assembly"
```

---

### Task 2: generate_article + generate_post + repurpose_content

**Files:**
- Create: `src/marketolog/modules/content/generator.py`
- Create: `tests/test_modules/test_content/test_generator.py`

These tools assemble context for Claude — they do NOT generate text. They return a structured brief with project context, keywords, tone of voice, and platform-specific guidelines.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_modules/test_content/test_generator.py
"""Tests for content generation tools (context assembly)."""

import pytest

from marketolog.modules.content.generator import (
    run_generate_article,
    run_generate_post,
    run_repurpose_content,
)


def test_generate_article(project_context):
    """Article context includes topic, keywords, tone."""
    result = run_generate_article(
        topic="Как выбрать таск-трекер для команды",
        project_context=project_context,
        keywords=["таск трекер", "управление задачами"],
        length="medium",
    )

    assert isinstance(result, str)
    assert "таск-трекер" in result.lower() or "таск трекер" in result.lower()
    assert "дружелюбный" in result or "tone" in result.lower()
    # Should have structure guidelines
    assert "H1" in result or "заголов" in result.lower()


def test_generate_article_defaults(project_context):
    """Article works with minimal params — keywords from project."""
    result = run_generate_article(
        topic="Обзор рынка",
        project_context=project_context,
    )

    assert isinstance(result, str)
    assert "таск трекер" in result or "управление задачами" in result


def test_generate_post_telegram(project_context):
    """Post context for Telegram includes platform guidelines."""
    result = run_generate_post(
        platform="telegram",
        project_context=project_context,
        topic="Новая фича",
    )

    assert isinstance(result, str)
    assert "telegram" in result.lower()
    # Should mention platform-specific formatting
    assert "эмодзи" in result.lower() or "emoji" in result.lower() or "форматирован" in result.lower()


def test_generate_post_vk(project_context):
    """Post context for VK includes VK-specific guidelines."""
    result = run_generate_post(
        platform="vk",
        project_context=project_context,
        topic="Кейс клиента",
    )

    assert isinstance(result, str)
    assert "vk" in result.lower() or "вк" in result.lower()


def test_generate_post_no_topic(project_context):
    """Post without topic — should suggest based on niche."""
    result = run_generate_post(
        platform="telegram",
        project_context=project_context,
    )

    assert isinstance(result, str)
    assert "управление проектами" in result or "таск трекер" in result


def test_repurpose_content(project_context):
    """Repurpose text into multiple formats."""
    source_text = "Длинная статья о том, как управлять задачами в команде. " * 10

    result = run_repurpose_content(
        text=source_text,
        project_context=project_context,
    )

    assert isinstance(result, str)
    assert "telegram" in result.lower()
    assert "vk" in result.lower()


def test_repurpose_specific_formats(project_context):
    """Repurpose to specific formats only."""
    source_text = "Статья о продуктивности для фрилансеров." * 5

    result = run_repurpose_content(
        text=source_text,
        project_context=project_context,
        formats=["telegram", "carousel"],
    )

    assert isinstance(result, str)
    assert "telegram" in result.lower()
    assert "карусель" in result.lower() or "carousel" in result.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_content/test_generator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement generator.py**

```python
# src/marketolog/modules/content/generator.py
"""Content generation — context assembly for Claude.

These tools do NOT generate text. They collect project context, SEO data,
tone of voice, and platform guidelines, returning a structured brief
for Claude to generate content using the content_writer.md prompt.
"""

PLATFORM_GUIDELINES: dict[str, dict[str, str]] = {
    "telegram": {
        "name": "Telegram",
        "max_length": "4096 символов",
        "format": "Короткие абзацы, эмодзи для структуры, жирный для акцентов",
        "style": "Неформальный, вовлекающий, с призывом к действию",
        "features": "Поддержка Markdown, ссылки, хештеги",
    },
    "vk": {
        "name": "VK (ВКонтакте)",
        "max_length": "16384 символов",
        "format": "Заголовок, разделение на абзацы, 1-2 изображения рекомендуется",
        "style": "Дружелюбный, с вопросами к аудитории, опросы приветствуются",
        "features": "Форматирование текста, прикреплённые ссылки, опросы",
    },
    "max": {
        "name": "MAX",
        "max_length": "4096 символов",
        "format": "Аналогично Telegram: короткие блоки, эмодзи",
        "style": "Неформальный, адаптивный",
        "features": "Markdown, кнопки, ссылки",
    },
    "dzen": {
        "name": "Дзен",
        "max_length": "без ограничений (статья)",
        "format": "Длинный формат, подзаголовки H2/H3, изображения в тексте",
        "style": "Информативный, экспертный, SEO-оптимизированный",
        "features": "Полноценный HTML-редактор, обложка, подборки",
    },
}


def run_generate_article(
    topic: str,
    project_context: dict,
    keywords: list[str] | None = None,
    length: str = "medium",
) -> str:
    """Assemble context for Claude to generate an SEO-optimized article.

    Args:
        topic: Article topic.
        project_context: Full project context.
        keywords: Target SEO keywords (defaults to project keywords).
        length: "short" (~800 words), "medium" (~1500), "long" (~3000).

    Returns:
        Structured brief for Claude.
    """
    niche = project_context.get("niche", "")
    tone = project_context.get("tone_of_voice", "нейтральный")
    audience = project_context.get("target_audience", [])

    if keywords is None:
        keywords = project_context.get("seo", {}).get("main_keywords", [])

    length_map = {"short": "~800 слов", "medium": "~1500 слов", "long": "~3000 слов"}
    target_length = length_map.get(length, "~1500 слов")

    lines = [
        f"## Задание: SEO-статья",
        f"**Тема:** {topic}",
        f"**Объём:** {target_length}",
        "",
        "### Контекст",
        f"- **Ниша:** {niche}",
        f"- **Tone of voice:** {tone}",
    ]

    if audience:
        segments = ", ".join(seg.get("segment", "") for seg in audience)
        lines.append(f"- **Целевая аудитория:** {segments}")

    lines.append("")

    if keywords:
        lines.append("### SEO-требования")
        lines.append(f"- **Целевые ключевые слова:** {', '.join(keywords)}")
        lines.append("- Основной ключ — в H1, первом абзаце, 2-3 подзаголовках H2")
        lines.append("- Плотность ключевых слов: 1-2% от текста")
        lines.append("- Используй LSI-синонимы и связанные фразы")
        lines.append("")

    lines.append("### Структура статьи")
    lines.append("- **H1:** один, содержит основной ключ")
    lines.append("- **H2:** 3-5 подзаголовков, раскрывающих тему")
    lines.append("- **Вступление:** зацепка + обещание пользы (2-3 предложения)")
    lines.append("- **Основная часть:** практичный, полезный контент")
    lines.append("- **Заключение:** итог + призыв к действию")
    lines.append("- **Meta description:** до 160 символов, с ключом")

    return "\n".join(lines)


def run_generate_post(
    platform: str,
    project_context: dict,
    topic: str | None = None,
) -> str:
    """Assemble context for Claude to generate a social media post.

    Args:
        platform: Target platform ("telegram", "vk", "max", "dzen").
        project_context: Full project context.
        topic: Post topic (if None, suggest based on niche).

    Returns:
        Structured brief for Claude.
    """
    niche = project_context.get("niche", "")
    tone = project_context.get("tone_of_voice", "нейтральный")
    keywords = project_context.get("seo", {}).get("main_keywords", [])

    platform_key = platform.lower()
    guidelines = PLATFORM_GUIDELINES.get(platform_key, PLATFORM_GUIDELINES["telegram"])

    lines = [
        f"## Задание: пост для {guidelines['name']}",
    ]

    if topic:
        lines.append(f"**Тема:** {topic}")
    else:
        lines.append(f"**Тема:** предложи на основе ниши \"{niche}\" и ключевых слов")

    lines.extend([
        "",
        "### Контекст проекта",
        f"- **Ниша:** {niche}",
        f"- **Tone of voice:** {tone}",
    ])

    if keywords:
        lines.append(f"- **Ключевые слова:** {', '.join(keywords)}")

    lines.extend([
        "",
        f"### Требования площадки: {guidelines['name']}",
        f"- **Макс. длина:** {guidelines['max_length']}",
        f"- **Форматирование:** {guidelines['format']}",
        f"- **Стиль:** {guidelines['style']}",
        f"- **Возможности:** {guidelines['features']}",
    ])

    return "\n".join(lines)


def run_repurpose_content(
    text: str,
    project_context: dict,
    formats: list[str] | None = None,
) -> str:
    """Assemble context for Claude to repurpose content into multiple formats.

    Args:
        text: Source text to repurpose.
        project_context: Full project context.
        formats: Target formats (default: all social platforms + carousel).

    Returns:
        Structured brief for Claude.
    """
    tone = project_context.get("tone_of_voice", "нейтральный")

    if formats is None:
        formats = ["telegram", "vk", "carousel"]

    lines = [
        "## Задание: репёрпосинг контента",
        "",
        "### Исходный текст",
        f"```",
        text[:2000] + ("..." if len(text) > 2000 else ""),
        f"```",
        f"(длина: {len(text)} символов)",
        "",
        f"**Tone of voice:** {tone}",
        "",
        "### Целевые форматы",
    ]

    for fmt in formats:
        fmt_lower = fmt.lower()
        if fmt_lower in PLATFORM_GUIDELINES:
            g = PLATFORM_GUIDELINES[fmt_lower]
            lines.append(f"\n#### {g['name']}")
            lines.append(f"- Макс. длина: {g['max_length']}")
            lines.append(f"- Стиль: {g['style']}")
            lines.append(f"- Формат: {g['format']}")
        elif fmt_lower == "carousel":
            lines.append("\n#### Карусель (Instagram / VK)")
            lines.append("- 5-10 слайдов")
            lines.append("- Заголовок на каждом слайде")
            lines.append("- Ключевая мысль + визуальная подсказка")
            lines.append("- Последний слайд — призыв к действию")
        elif fmt_lower == "video_script":
            lines.append("\n#### Видео-скрипт")
            lines.append("- Хук (первые 3 секунды)")
            lines.append("- Основная часть (60-90 секунд)")
            lines.append("- Призыв к действию")

    lines.append("\n### Инструкция")
    lines.append("Адаптируй исходный текст под каждый формат отдельно.")
    lines.append("Сохраняй ключевые идеи, но переписывай под стиль площадки.")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_content/test_generator.py -v`
Expected: PASS (all 7 tests)

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/content/generator.py tests/test_modules/test_content/test_generator.py
git commit -m "feat(content): add generate_article + generate_post + repurpose_content"
```

---

### Task 3: optimize_text

**Files:**
- Create: `src/marketolog/modules/content/optimizer.py`
- Create: `tests/test_modules/test_content/test_optimizer.py`

Analyzes text for SEO: keyword density, structure (headings), readability metrics, and returns optimization suggestions.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_modules/test_content/test_optimizer.py
"""Tests for text optimizer tool."""

import pytest

from marketolog.modules.content.optimizer import run_optimize_text


SAMPLE_TEXT = """# Как выбрать таск-трекер для команды

Таск-трекер — инструмент для управления задачами. Выбор правильного таск-трекера важен для продуктивности.

## Критерии выбора

При выборе таск-трекера обратите внимание на:
- Удобство интерфейса
- Интеграции
- Стоимость

## Топ-5 решений

Рассмотрим лучшие таск-трекеры для малых команд.

Каждый из них имеет свои преимущества в управлении задачами.
"""


def test_optimize_text_basic():
    """Optimizer returns analysis with keyword density."""
    result = run_optimize_text(
        text=SAMPLE_TEXT,
        target_keywords=["таск-трекер", "управление задачами"],
    )

    assert isinstance(result, str)
    assert "плотность" in result.lower() or "density" in result.lower() or "%" in result
    assert "таск-трекер" in result


def test_optimize_text_structure_analysis():
    """Optimizer checks heading structure."""
    result = run_optimize_text(
        text=SAMPLE_TEXT,
        target_keywords=["таск-трекер"],
    )

    assert "H1" in result or "заголов" in result.lower()
    assert "H2" in result


def test_optimize_text_short():
    """Short text gets length warning."""
    result = run_optimize_text(
        text="Короткий текст.",
        target_keywords=["ключ"],
    )

    assert isinstance(result, str)
    # Should warn about short text
    assert "корот" in result.lower() or "длин" in result.lower() or "слов" in result.lower()


def test_optimize_text_readability():
    """Optimizer includes readability analysis."""
    result = run_optimize_text(
        text=SAMPLE_TEXT,
        target_keywords=["таск-трекер"],
    )

    # Should mention sentence or readability metrics
    assert "предложен" in result.lower() or "читаем" in result.lower() or "слов" in result.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_content/test_optimizer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement optimizer.py**

```python
# src/marketolog/modules/content/optimizer.py
"""SEO text optimizer — analyzes text for keyword density, structure, readability."""

import re


def run_optimize_text(
    text: str,
    target_keywords: list[str],
) -> str:
    """Analyze text for SEO optimization opportunities.

    Checks:
    - Keyword density for each target keyword
    - Heading structure (H1, H2, H3)
    - Text length and word count
    - Average sentence length (readability proxy)
    - Keyword presence in headings and first paragraph

    Args:
        text: The text to analyze (Markdown format).
        target_keywords: List of target SEO keywords.

    Returns:
        Formatted optimization report.
    """
    lines_list = text.strip().split("\n")
    plain_text = _strip_markdown(text)
    words = plain_text.split()
    word_count = len(words)

    lines = ["## SEO-анализ текста\n"]

    # --- Text length ---
    lines.append("### Объём")
    lines.append(f"- **Слов:** {word_count}")
    lines.append(f"- **Символов:** {len(plain_text)}")
    if word_count < 300:
        lines.append("- ⚠ Текст короткий (< 300 слов). Для SEO рекомендуется минимум 800 слов.")
    elif word_count < 800:
        lines.append("- ⚠ Текст средней длины. Для конкурентных запросов рекомендуется 1000+ слов.")
    else:
        lines.append("- ✓ Достаточная длина для SEO.")
    lines.append("")

    # --- Keyword density ---
    lines.append("### Плотность ключевых слов")
    text_lower = plain_text.lower()
    for kw in target_keywords:
        kw_lower = kw.lower()
        count = text_lower.count(kw_lower)
        density = (count * len(kw_lower.split()) / word_count * 100) if word_count > 0 else 0
        status = "✓" if 0.5 <= density <= 3.0 else "⚠"
        lines.append(f"- **\"{kw}\"**: {count} раз ({density:.1f}%) {status}")

    lines.append("")

    # --- Heading structure ---
    h1_list = re.findall(r"^# (.+)$", text, re.MULTILINE)
    h2_list = re.findall(r"^## (.+)$", text, re.MULTILINE)
    h3_list = re.findall(r"^### (.+)$", text, re.MULTILINE)

    lines.append("### Структура заголовков")
    lines.append(f"- **H1:** {len(h1_list)} шт." + (" ✓" if len(h1_list) == 1 else " ⚠ (должен быть ровно 1)"))
    if h1_list:
        lines.append(f"  → \"{h1_list[0]}\"")
    lines.append(f"- **H2:** {len(h2_list)} шт." + (" ✓" if 2 <= len(h2_list) <= 8 else " ⚠"))
    for h2 in h2_list:
        lines.append(f"  → \"{h2}\"")
    lines.append(f"- **H3:** {len(h3_list)} шт.")
    lines.append("")

    # --- Keywords in headings ---
    lines.append("### Ключевые слова в заголовках")
    all_headings = " ".join(h1_list + h2_list + h3_list).lower()
    for kw in target_keywords:
        found = kw.lower() in all_headings
        status = "✓ присутствует" if found else "⚠ отсутствует"
        lines.append(f"- \"{kw}\": {status}")
    lines.append("")

    # --- First paragraph ---
    first_para = ""
    for line in lines_list:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            first_para = stripped
            break

    if first_para:
        lines.append("### Первый абзац")
        kw_in_first = any(kw.lower() in first_para.lower() for kw in target_keywords)
        if kw_in_first:
            lines.append("- ✓ Ключевое слово присутствует в первом абзаце")
        else:
            lines.append("- ⚠ Ключевое слово отсутствует в первом абзаце")
        lines.append("")

    # --- Readability ---
    sentences = re.split(r"[.!?]+", plain_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    avg_sentence_len = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

    lines.append("### Читаемость")
    lines.append(f"- **Предложений:** {len(sentences)}")
    lines.append(f"- **Ср. длина предложения:** {avg_sentence_len:.1f} слов")
    if avg_sentence_len > 20:
        lines.append("- ⚠ Предложения длинные — упрости для лучшей читаемости")
    elif avg_sentence_len < 8:
        lines.append("- ⚠ Предложения слишком короткие — может быть рваный ритм")
    else:
        lines.append("- ✓ Хорошая длина предложений")

    return "\n".join(lines)


def _strip_markdown(text: str) -> str:
    """Remove Markdown formatting to get plain text."""
    # Remove headings markers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", text)
    # Remove links
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    # Remove list markers
    text = re.sub(r"^[-*]\s+", "", text, flags=re.MULTILINE)
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_content/test_optimizer.py -v`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/content/optimizer.py tests/test_modules/test_content/test_optimizer.py
git commit -m "feat(content): add optimize_text — SEO text analysis"
```

---

### Task 4: analyze_content

**Files:**
- Create: `src/marketolog/modules/content/analyzer.py`
- Create: `tests/test_modules/test_content/test_analyzer.py`

Fetches a URL and analyzes the page content: readability, SEO signals, structure. Uses BeautifulSoup.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_modules/test_content/test_analyzer.py
"""Tests for content analyzer tool."""

import httpx
import pytest
import respx

from marketolog.modules.content.analyzer import run_analyze_content

SAMPLE_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
  <title>Как выбрать таск-трекер — Руководство 2026</title>
  <meta name="description" content="Полное руководство по выбору таск-трекера для команды.">
</head>
<body>
  <h1>Как выбрать таск-трекер для команды</h1>
  <p>Выбор правильного таск-трекера — важный шаг для продуктивности. Рассмотрим ключевые критерии.</p>
  <h2>Критерии выбора</h2>
  <p>При выборе обратите внимание на удобство интерфейса, интеграции и стоимость.</p>
  <h2>Топ решений</h2>
  <p>Лучшие таск-трекеры для малых команд включают множество решений на рынке.</p>
  <img src="img1.jpg" alt="Сравнение трекеров">
  <img src="img2.jpg">
</body>
</html>"""


@respx.mock
@pytest.mark.asyncio
async def test_analyze_content(cache):
    """Full content analysis of a page."""
    respx.get("https://example.ru/blog/article").mock(
        return_value=httpx.Response(200, text=SAMPLE_PAGE)
    )

    report = await run_analyze_content(
        url="https://example.ru/blog/article",
        cache=cache,
    )

    assert isinstance(report, str)
    assert "таск-трекер" in report.lower() or "title" in report.lower()
    assert "H1" in report or "заголов" in report.lower()
    assert "H2" in report


@respx.mock
@pytest.mark.asyncio
async def test_analyze_content_cached(cache):
    """Cached result returned."""
    cache.set("content_analysis", "https://example.ru/page", "cached analysis", ttl_seconds=3600)

    report = await run_analyze_content(
        url="https://example.ru/page",
        cache=cache,
    )

    assert report == "cached analysis"
    assert len(respx.calls) == 0


@respx.mock
@pytest.mark.asyncio
async def test_analyze_content_error(cache):
    """Handle HTTP errors gracefully."""
    respx.get("https://example.ru/404").mock(
        return_value=httpx.Response(404, text="Not Found")
    )

    report = await run_analyze_content(
        url="https://example.ru/404",
        cache=cache,
    )

    assert isinstance(report, str)
    assert "404" in report or "ошибк" in report.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_content/test_analyzer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement analyzer.py**

```python
# src/marketolog/modules/content/analyzer.py
"""Content analyzer — fetches URL and analyzes page content for SEO and readability."""

import re

from bs4 import BeautifulSoup

from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

CACHE_NS = "content_analysis"
CACHE_TTL = 3600


async def run_analyze_content(
    url: str,
    *,
    cache: FileCache,
) -> str:
    """Fetch and analyze page content.

    Checks: title, description, headings, text length, images,
    readability metrics.

    Args:
        url: Page URL to analyze.
        cache: File cache instance.

    Returns:
        Formatted content analysis report.
    """
    cached = cache.get(CACHE_NS, url)
    if cached is not None:
        return cached  # type: ignore[return-value]

    resp = await fetch_with_retry(url)
    if resp.status_code != 200:
        return f"Ошибка загрузки страницы (HTTP {resp.status_code}): {url}"

    soup = BeautifulSoup(resp.text, "lxml")
    report = _build_report(url, soup)

    cache.set(CACHE_NS, url, report, ttl_seconds=CACHE_TTL)
    return report


def _build_report(url: str, soup: BeautifulSoup) -> str:
    lines = [f"## Анализ контента: {url}\n"]

    # --- Title & Meta ---
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag.get("content", "").strip() if desc_tag else ""

    lines.append("### Title & Meta")
    if title:
        lines.append(f"- **Title:** {title} ({len(title)} символов)")
        if len(title) < 30:
            lines.append("  ⚠ Слишком короткий (рекомендуется 50-60)")
        elif len(title) > 70:
            lines.append("  ⚠ Слишком длинный (рекомендуется 50-60)")
    else:
        lines.append("- **Title:** ⚠ ОТСУТСТВУЕТ")

    if description:
        lines.append(f"- **Description:** {description} ({len(description)} символов)")
        if len(description) > 160:
            lines.append("  ⚠ Длиннее 160 символов — будет обрезано в выдаче")
    else:
        lines.append("- **Description:** ⚠ ОТСУТСТВУЕТ")
    lines.append("")

    # --- Headings ---
    h1_tags = soup.find_all("h1")
    h2_tags = soup.find_all("h2")
    h3_tags = soup.find_all("h3")

    lines.append("### Заголовки")
    lines.append(f"- **H1:** {len(h1_tags)} шт." + (" ✓" if len(h1_tags) == 1 else " ⚠"))
    for h in h1_tags:
        lines.append(f"  → \"{h.get_text(strip=True)}\"")
    lines.append(f"- **H2:** {len(h2_tags)} шт.")
    for h in h2_tags:
        lines.append(f"  → \"{h.get_text(strip=True)}\"")
    lines.append(f"- **H3:** {len(h3_tags)} шт.")
    lines.append("")

    # --- Text content ---
    body = soup.find("body")
    if body:
        text = body.get_text(separator=" ", strip=True)
    else:
        text = soup.get_text(separator=" ", strip=True)

    words = text.split()
    word_count = len(words)

    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    avg_sentence = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

    lines.append("### Контент")
    lines.append(f"- **Слов:** {word_count}")
    lines.append(f"- **Предложений:** {len(sentences)}")
    lines.append(f"- **Ср. длина предложения:** {avg_sentence:.1f} слов")

    if word_count < 300:
        lines.append("- ⚠ Мало контента (< 300 слов)")
    elif word_count > 3000:
        lines.append("- ✓ Объёмный контент (хорошо для SEO)")
    lines.append("")

    # --- Images ---
    all_imgs = soup.find_all("img")
    no_alt = [img for img in all_imgs if not img.get("alt", "").strip()]

    lines.append("### Изображения")
    lines.append(f"- **Всего:** {len(all_imgs)}")
    lines.append(f"- **Без alt:** {len(no_alt)}" + (" ⚠" if no_alt else " ✓"))

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_content/test_analyzer.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/content/analyzer.py tests/test_modules/test_content/test_analyzer.py
git commit -m "feat(content): add analyze_content — page content analysis"
```

---

### Task 5: generate_meta

**Files:**
- Create: `src/marketolog/modules/content/meta.py`
- Create: `tests/test_modules/test_content/test_meta.py`

Generates title, meta description, and H1 suggestions based on text or URL content.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_modules/test_content/test_meta.py
"""Tests for meta generation tool."""

import pytest

from marketolog.modules.content.meta import run_generate_meta


def test_generate_meta_from_text():
    """Generate meta from raw text."""
    text = """
    Как выбрать таск-трекер для команды в 2026 году.
    Рассмотрим ключевые критерии: удобство, интеграции, стоимость.
    Лучшие решения для малых команд.
    """

    result = run_generate_meta(
        text=text,
        keywords=["таск-трекер", "управление задачами"],
    )

    assert isinstance(result, str)
    assert "title" in result.lower() or "Title" in result
    assert "description" in result.lower() or "Description" in result
    assert "H1" in result


def test_generate_meta_with_keywords():
    """Meta suggestions reference target keywords."""
    result = run_generate_meta(
        text="Статья о продуктивности и управлении проектами.",
        keywords=["продуктивность", "управление проектами"],
    )

    assert "продуктивность" in result or "управление проектами" in result


def test_generate_meta_empty_keywords():
    """Works without keywords."""
    result = run_generate_meta(
        text="Обзор лучших инструментов для работы.",
    )

    assert isinstance(result, str)
    assert "title" in result.lower() or "Title" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_modules/test_content/test_meta.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement meta.py**

```python
# src/marketolog/modules/content/meta.py
"""Meta tag generator — assembles context for Claude to generate title, description, H1."""


def run_generate_meta(
    text: str,
    keywords: list[str] | None = None,
) -> str:
    """Assemble context for Claude to generate meta tags.

    Args:
        text: Source text or page content to base meta on.
        keywords: Target SEO keywords.

    Returns:
        Structured brief for Claude to generate title, description, H1.
    """
    # Extract first ~500 chars as context
    preview = text.strip()[:500]

    lines = [
        "## Задание: генерация мета-тегов",
        "",
        "### Исходный контент",
        f"```",
        preview,
        f"```",
        "",
    ]

    if keywords:
        lines.append("### Целевые ключевые слова")
        for kw in keywords:
            lines.append(f"- {kw}")
        lines.append("")

    lines.extend([
        "### Требования",
        "",
        "Сгенерируй три варианта для каждого элемента:",
        "",
        "**Title (тег `<title>`):**",
        "- Длина: 50-60 символов",
        "- Содержит основной ключ ближе к началу",
        "- Привлекает внимание, побуждает к клику",
        "",
        "**Meta Description (мета-описание):**",
        "- Длина: 140-160 символов",
        "- Содержит основной и дополнительный ключ",
        "- Описывает содержание + призыв к действию",
        "",
        "**H1 (основной заголовок):**",
        "- Содержит основной ключ",
        "- Одна штука на страницу",
        "- Отличается от Title (не дублирует)",
        "- Информативный, понятный читателю",
    ])

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_modules/test_content/test_meta.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
git add src/marketolog/modules/content/meta.py tests/test_modules/test_content/test_meta.py
git commit -m "feat(content): add generate_meta — title/description/H1 suggestions"
```

---

### Task 6: content_writer.md prompt + register 7 tools in server + integration tests

**Files:**
- Create: `src/marketolog/prompts/content_writer.md`
- Modify: `src/marketolog/server.py`
- Create: `tests/test_modules/test_content/test_integration.py`

- [ ] **Step 1: Create content_writer.md prompt**

```markdown
# src/marketolog/prompts/content_writer.md
# Контент-райтер

Ты — опытный контент-маркетолог и SEO-копирайтер для бизнеса в Рунете.

## Принципы работы

- Пиши в tone of voice проекта (бери из контекста)
- Каждый текст решает задачу: привлечь трафик, вовлечь, конвертировать
- SEO-оптимизация без потери читаемости — ключи вплетаются естественно
- Адаптируй стиль под площадку: блог ≠ Telegram ≠ VK ≠ Дзен
- Не лей воду — каждое предложение несёт ценность

## Доступные инструменты

- `content_plan` — составить контент-план
- `generate_article` — контекст для SEO-статьи
- `generate_post` — контекст для поста в соцсеть
- `optimize_text` — SEO-анализ текста
- `analyze_content` — анализ существующей страницы
- `generate_meta` — генерация title/description/H1
- `repurpose_content` — адаптация текста под разные площадки

## Форматы контента

### Блог-статья
- H1 с ключом, 3-5 H2, 800-3000 слов
- Вступление (зацепка), основная часть (польза), заключение (CTA)
- Meta: title 50-60 chars, description 140-160 chars

### Telegram-пост
- До 4096 символов, эмодзи для структуры
- Хук в первой строке, польза в теле, CTA в конце

### VK-пост
- До 16384 символов, вопросы к аудитории
- Визуал рекомендуется, опросы повышают вовлечённость

### Дзен-статья
- Длинный формат, подзаголовки, изображения
- SEO-оптимизация критична (индексируется Яндексом)
```

- [ ] **Step 2: Write integration tests**

```python
# tests/test_modules/test_content/test_integration.py
"""Integration tests — content tools registered in MCP server."""

import asyncio
import pytest
from pathlib import Path

from marketolog.server import create_server


@pytest.fixture
def server(tmp_marketolog_dir: Path):
    return create_server(base_dir=tmp_marketolog_dir)


def test_server_has_content_tools(server):
    """Server must expose all 7 content tools."""
    tools = asyncio.run(server._local_provider.list_tools())
    tool_names = {t.name for t in tools}
    expected_content = {
        "content_plan", "generate_article", "generate_post",
        "optimize_text", "analyze_content", "generate_meta",
        "repurpose_content",
    }
    assert expected_content.issubset(tool_names), f"Missing: {expected_content - tool_names}"


def test_server_has_content_writer_resource(server):
    """Server must expose content_writer prompt as a resource."""
    resources = asyncio.run(server._local_provider.list_resources())
    resource_uris = {str(r.uri) for r in resources}
    assert any("content_writer" in uri for uri in resource_uris)


def test_content_tools_are_read_only(server):
    """All content tools should have readOnlyHint=True."""
    tools = asyncio.run(server._local_provider.list_tools())
    content_tools = {
        "content_plan", "generate_article", "generate_post",
        "optimize_text", "analyze_content", "generate_meta",
        "repurpose_content",
    }
    for tool in tools:
        if tool.name in content_tools:
            assert tool.annotations is not None, f"{tool.name} has no annotations"
            assert tool.annotations.readOnlyHint is True, f"{tool.name} should be readOnlyHint=True"


def test_total_tool_count(server):
    """Server should have exactly 29 tools (6 Core + 8 SEO + 8 Analytics + 7 Content)."""
    tools = asyncio.run(server._local_provider.list_tools())
    assert len(tools) == 29, f"Expected 29 tools, got {len(tools)}: {[t.name for t in tools]}"
```

- [ ] **Step 3: Run integration tests — verify they fail**

Run: `pytest tests/test_modules/test_content/test_integration.py -v`
Expected: FAIL — tools not registered

- [ ] **Step 4: Add imports and register tools in server.py**

Read `src/marketolog/server.py` first. Then add:

**Imports** (after analytics imports):

```python
from marketolog.modules.content.planner import run_content_plan
from marketolog.modules.content.generator import run_generate_article, run_generate_post, run_repurpose_content
from marketolog.modules.content.optimizer import run_optimize_text
from marketolog.modules.content.analyzer import run_analyze_content
from marketolog.modules.content.meta import run_generate_meta
```

**7 tool registrations** (after Analytics tools block, before `# --- Prompt Resources ---`):

```python
    # --- Content Tools ---

    @mcp.tool(annotations=READ_ONLY)
    def content_plan(
        period: Annotated[str, Field(description="Период планирования: '1 week', '2 weeks', '1 month'", default="2 weeks")] = "2 weeks",
        topics_count: Annotated[int, Field(description="Количество тем", default=10)] = 10,
    ) -> str:
        """Контент-план: темы, форматы, ключевые слова, календарь."""
        project = ctx.get_context()
        return run_content_plan(project_context=project, period=period, topics_count=topics_count)

    @mcp.tool(annotations=READ_ONLY)
    def generate_article(
        topic: Annotated[str, Field(description="Тема статьи")],
        keywords: Annotated[list[str] | None, Field(description="Целевые ключевые слова", default=None)] = None,
        length: Annotated[str, Field(description="Объём: short, medium, long", default="medium")] = "medium",
    ) -> str:
        """SEO-оптимизированная статья: собирает контекст (ключи, tone of voice, аудитория) для генерации."""
        project = ctx.get_context()
        return run_generate_article(topic=topic, project_context=project, keywords=keywords, length=length)

    @mcp.tool(annotations=READ_ONLY)
    def generate_post(
        platform: Annotated[str, Field(description="Площадка: telegram, vk, max, dzen")],
        topic: Annotated[str | None, Field(description="Тема поста (если не указана — предложит)", default=None)] = None,
    ) -> str:
        """Пост для площадки: собирает контекст + гайдлайны площадки для генерации."""
        project = ctx.get_context()
        return run_generate_post(platform=platform, project_context=project, topic=topic)

    @mcp.tool(annotations=READ_ONLY)
    def optimize_text(
        text: Annotated[str, Field(description="Текст для анализа (Markdown)")],
        target_keywords: Annotated[list[str], Field(description="Целевые ключевые слова")],
    ) -> str:
        """SEO-оптимизация текста: плотность ключей, структура, читаемость, рекомендации."""
        return run_optimize_text(text=text, target_keywords=target_keywords)

    @mcp.tool(annotations=READ_ONLY)
    async def analyze_content(
        url: Annotated[str | None, Field(description="URL страницы для анализа. Если не указан — URL проекта", default=None)] = None,
    ) -> str:
        """Анализ контента страницы: читаемость, SEO-оценка, заголовки, мета-теги."""
        if url is None:
            url = ctx.get_context()["url"]
        return await run_analyze_content(url=url, cache=cache)

    @mcp.tool(annotations=READ_ONLY)
    def generate_meta(
        text: Annotated[str, Field(description="Текст или содержимое страницы для генерации мета-тегов")],
        keywords: Annotated[list[str] | None, Field(description="Целевые ключевые слова", default=None)] = None,
    ) -> str:
        """Генерация title, description, H1 — собирает контекст и требования."""
        return run_generate_meta(text=text, keywords=keywords)

    @mcp.tool(annotations=READ_ONLY)
    def repurpose_content(
        text: Annotated[str, Field(description="Исходный текст для адаптации")],
        formats: Annotated[list[str] | None, Field(description="Целевые форматы: telegram, vk, max, dzen, carousel, video_script", default=None)] = None,
    ) -> str:
        """Репёрпосинг контента: адаптация текста под разные площадки и форматы."""
        project = ctx.get_context()
        return run_repurpose_content(text=text, project_context=project, formats=formats)
```

**Content writer resource** (after `analyst_prompt` resource):

```python
    @mcp.resource("marketolog://prompts/content_writer")
    def content_writer_prompt() -> str:
        """Промпт контент-райтера."""
        return (prompts_dir / "content_writer.md").read_text(encoding="utf-8")
```

**IMPORTANT:** Also update the SEO and Analytics integration tests' `test_total_tool_count` to expect 29 instead of 22.

- [ ] **Step 5: Run ALL tests**

Run: `pytest tests/ -v`
Expected: ALL PASS (~107 old + ~21 new = ~128 tests)

- [ ] **Step 6: Commit**

```bash
git add src/marketolog/prompts/content_writer.md src/marketolog/server.py tests/test_modules/test_content/test_integration.py tests/test_modules/test_seo/test_integration.py tests/test_modules/test_analytics/test_integration.py
git commit -m "feat(content): register 7 content tools in MCP server + content_writer prompt"
```

---

## Summary

| Task | Files | Tools | Tests |
|---|---|---|---|
| 1 | planner.py + conftest | content_plan | 4 |
| 2 | generator.py | generate_article, generate_post, repurpose_content | 7 |
| 3 | optimizer.py | optimize_text | 4 |
| 4 | analyzer.py | analyze_content | 3 |
| 5 | meta.py | generate_meta | 3 |
| 6 | server.py + content_writer.md + integration | Registration + prompt | 4 |
| **Total** | **~16 files** | **7 tools** | **~25 tests** |

After completion: **29 tools** in MCP server (6 Core + 8 SEO + 8 Analytics + 7 Content), **~132 tests**.
