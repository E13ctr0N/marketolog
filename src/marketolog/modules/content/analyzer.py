"""Content Analyzer — readability, SEO signals, heading structure, images.

Fetches a URL and builds a structured Markdown report covering:
- Title & meta description (length + warnings)
- Heading structure (H1/H2/H3 counts + text)
- Content stats (word count, sentence count, avg sentence length)
- Image audit (total count, missing alt attributes)
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

CACHE_NS = "content_analysis"
CACHE_TTL = 3600  # 1 hour

TITLE_MIN = 30
TITLE_MAX = 70
DESC_MIN = 70
DESC_MAX = 160
CONTENT_MIN_WORDS = 300


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_analyze_content(url: str, *, cache: FileCache) -> str:
    """Fetch *url* and return a content analysis report string.

    Steps:
    1. Cache hit → return immediately.
    2. Fetch URL via fetch_with_retry.
    3. Return error message on non-200.
    4. Parse HTML with BeautifulSoup("lxml").
    5. Build and cache the report.
    """
    cached = cache.get(CACHE_NS, url)
    if cached is not None:
        return cached  # type: ignore[return-value]

    response = await fetch_with_retry(url)

    if response.status_code != 200:
        report = (
            f"Ошибка при получении страницы {url}: "
            f"статус {response.status_code}."
        )
        return report

    soup = BeautifulSoup(response.text, "lxml")
    report = _build_report(url, soup)

    cache.set(CACHE_NS, url, report, ttl_seconds=CACHE_TTL)
    return report


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------


def _build_report(url: str, soup: BeautifulSoup) -> str:
    parts: list[str] = [f"# Анализ контента: {url}\n"]

    parts.append(_section_title_meta(soup))
    parts.append(_section_headings(soup))
    parts.append(_section_content(soup))
    parts.append(_section_images(soup))

    return "\n".join(parts)


# ---- Title & Meta ----------------------------------------------------------


def _section_title_meta(soup: BeautifulSoup) -> str:
    lines = ["## Title & Meta\n"]

    # Title
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else None
    if title_text:
        length = len(title_text)
        lines.append(f"- **Title:** {title_text} ({length} симв.)")
        if length < TITLE_MIN:
            lines.append(f"  ⚠ Title слишком короткий (< {TITLE_MIN} симв.)")
        elif length > TITLE_MAX:
            lines.append(f"  ⚠ Title слишком длинный (> {TITLE_MAX} симв.)")
        else:
            lines.append("  ✓ Длина Title в норме")
    else:
        lines.append("- **Title:** ОТСУТСТВУЕТ ⚠")

    # Meta description
    desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    desc_text = desc_tag.get("content", "").strip() if desc_tag else ""  # type: ignore[union-attr]
    if desc_text:
        length = len(desc_text)
        lines.append(f"- **Meta description:** {desc_text} ({length} симв.)")
        if length < DESC_MIN:
            lines.append(f"  ⚠ Description слишком короткий (< {DESC_MIN} симв.)")
        elif length > DESC_MAX:
            lines.append(f"  ⚠ Description слишком длинный (> {DESC_MAX} симв.)")
        else:
            lines.append("  ✓ Длина Description в норме")
    else:
        lines.append("- **Meta description:** ОТСУТСТВУЕТ ⚠")

    return "\n".join(lines)


# ---- Headings --------------------------------------------------------------


def _section_headings(soup: BeautifulSoup) -> str:
    lines = ["\n## Заголовки (Heading Structure)\n"]

    h1_tags = soup.find_all("h1")
    h2_tags = soup.find_all("h2")
    h3_tags = soup.find_all("h3")

    # H1
    h1_count = len(h1_tags)
    if h1_count == 0:
        lines.append("- **H1:** ОТСУТСТВУЕТ ⚠")
    else:
        marker = "✓" if h1_count == 1 else "⚠ (несколько H1)"
        lines.append(f"- **H1** ({h1_count} шт.) {marker}")
        for tag in h1_tags:
            lines.append(f"  - {tag.get_text(strip=True)}")

    # H2
    if h2_tags:
        lines.append(f"- **H2** ({len(h2_tags)} шт.)")
        for tag in h2_tags:
            lines.append(f"  - {tag.get_text(strip=True)}")
    else:
        lines.append("- **H2:** не найдено")

    # H3
    if h3_tags:
        lines.append(f"- **H3** ({len(h3_tags)} шт.)")
        for tag in h3_tags:
            lines.append(f"  - {tag.get_text(strip=True)}")

    return "\n".join(lines)


# ---- Content stats ---------------------------------------------------------


def _section_content(soup: BeautifulSoup) -> str:
    lines = ["\n## Контент\n"]

    # Extract visible text (strip script/style)
    for el in soup(["script", "style", "head"]):
        el.decompose()

    text = soup.get_text(separator=" ", strip=True)
    words = text.split()
    word_count = len(words)

    # Sentence count — split by . ! ?
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    sentence_count = len(sentences)
    avg_len = round(word_count / sentence_count, 1) if sentence_count else 0

    lines.append(f"- **Слов:** {word_count}")
    lines.append(f"- **Предложений:** {sentence_count}")
    lines.append(f"- **Среднее слов в предложении:** {avg_len}")

    if word_count < CONTENT_MIN_WORDS:
        lines.append(
            f"  ⚠ Контент короткий (< {CONTENT_MIN_WORDS} слов) — "
            "рекомендуется расширить для SEO"
        )

    return "\n".join(lines)


# ---- Images ----------------------------------------------------------------


def _section_images(soup: BeautifulSoup) -> str:
    lines = ["\n## Изображения\n"]

    all_imgs = soup.find_all("img")
    total = len(all_imgs)
    no_alt = [img for img in all_imgs if not img.get("alt", "").strip()]
    no_alt_count = len(no_alt)

    lines.append(f"- **Всего изображений:** {total}")
    lines.append(f"- **Без атрибута alt:** {no_alt_count}")

    if no_alt_count > 0:
        lines.append(
            f"  ⚠ {no_alt_count} изображений без alt — "
            "добавьте описания для доступности и SEO"
        )

    return "\n".join(lines)
