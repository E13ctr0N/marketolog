"""Text optimizer — SEO analysis of Markdown/plain text.

Pure sync function, no external API calls, no cache.
Analyzes keyword density, heading structure, readability,
and keyword placement in headings/first paragraph.
"""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Markdown stripping
# ---------------------------------------------------------------------------


def _strip_markdown(text: str) -> str:
    """Remove Markdown formatting and return plain text.

    Strips:
    - Heading markers (# ## ###)
    - Bold/italic (**text**, *text*, __text__, _text_)
    - Links [label](url)
    - List markers (-, *, +, numbered)
    - Code blocks (``` and `)
    - Collapses multiple whitespace into single spaces
    """
    # Remove fenced code blocks
    text = re.sub(r"```[\s\S]*?```", " ", text)
    # Remove inline code
    text = re.sub(r"`[^`]*`", " ", text)
    # Remove heading markers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic markers
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)
    # Remove links — keep label
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # Remove list markers
    text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_headings(text: str) -> list[tuple[int, str]]:
    """Extract headings from Markdown text.

    Returns list of (level, heading_text) tuples for H1–H3.
    """
    headings: list[tuple[int, str]] = []
    pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    for match in pattern.finditer(text):
        level = len(match.group(1))
        heading_text = match.group(2).strip()
        headings.append((level, heading_text))
    return headings


def _count_keyword_occurrences(plain_text: str, keyword: str) -> int:
    """Count non-overlapping case-insensitive keyword occurrences."""
    return len(re.findall(re.escape(keyword.lower()), plain_text.lower()))


def _get_first_paragraph(plain_text: str) -> str:
    """Return the first non-empty sentence group (~first paragraph) of plain text."""
    # Split by sentence endings or double newlines
    sentences = re.split(r"(?<=[.!?])\s+", plain_text)
    # Return first ~2 sentences as proxy for first paragraph
    return " ".join(sentences[:2])


def _avg_sentence_length(plain_text: str) -> float:
    """Average words per sentence."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", plain_text) if s.strip()]
    if not sentences:
        return 0.0
    word_counts = [len(s.split()) for s in sentences]
    return sum(word_counts) / len(word_counts)


def _indicator(ok: bool) -> str:
    return "✓" if ok else "⚠"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_optimize_text(text: str, target_keywords: list[str]) -> str:
    """Analyze text for SEO quality and return a formatted Markdown report.

    Args:
        text: Source text (may contain Markdown formatting).
        target_keywords: List of target keywords to analyze.

    Returns:
        Formatted Markdown report with ✓/⚠ indicators.
    """
    plain_text = _strip_markdown(text)
    words = plain_text.split()
    total_words = len(words)
    headings = _extract_headings(text)

    h1_headings = [h for level, h in headings if level == 1]
    h2_headings = [h for level, h in headings if level == 2]
    h3_headings = [h for level, h in headings if level == 3]
    all_heading_text = " ".join(h for _, h in headings).lower()

    first_paragraph = _get_first_paragraph(plain_text)
    avg_sent_len = _avg_sentence_length(plain_text)

    lines: list[str] = []

    # --- Header ---
    lines.append("# Отчёт по оптимизации текста")
    lines.append("")

    # --- Text length ---
    lines.append("## Объём текста")
    lines.append("")
    short_warning = total_words < 300
    length_indicator = _indicator(not short_warning)
    lines.append(f"- **Слов:** {total_words} {length_indicator}")
    if short_warning:
        lines.append(
            f"  ⚠ Текст короткий ({total_words} слов). "
            "Рекомендуется минимум 300 слов для SEO-статьи."
        )
    lines.append("")

    # --- Heading structure ---
    lines.append("## Структура заголовков")
    lines.append("")
    has_h1 = len(h1_headings) == 1
    has_h2 = len(h2_headings) > 0

    lines.append(f"- **H1:** {len(h1_headings)} шт. {_indicator(has_h1)}")
    if h1_headings:
        for h in h1_headings:
            lines.append(f"  - «{h}»")
    elif not h1_headings:
        lines.append("  ⚠ H1 отсутствует")

    lines.append(f"- **H2:** {len(h2_headings)} шт. {_indicator(has_h2)}")
    if h2_headings:
        for h in h2_headings:
            lines.append(f"  - «{h}»")

    if h3_headings:
        lines.append(f"- **H3:** {len(h3_headings)} шт.")
        for h in h3_headings:
            lines.append(f"  - «{h}»")
    lines.append("")

    # --- Keyword density ---
    lines.append("## Плотность ключевых слов")
    lines.append("")

    if total_words == 0:
        lines.append("Нет слов для анализа.")
    else:
        for keyword in target_keywords:
            kw_words = len(keyword.split())
            count = _count_keyword_occurrences(plain_text, keyword)
            # density = occurrences * words_in_keyword / total_words * 100
            density = count * kw_words / total_words * 100
            density_ok = 0.5 <= density <= 3.0
            indicator = _indicator(density_ok)

            in_headings = keyword.lower() in all_heading_text
            in_first_para = keyword.lower() in first_paragraph.lower()

            lines.append(f"### «{keyword}»")
            lines.append(f"- **Вхождений:** {count}")
            lines.append(f"- **Плотность:** {density:.1f}% {indicator}")
            lines.append(f"  *(рекомендуется 0.5–3.0%)*")
            lines.append(f"- **В заголовках:** {'да ' + _indicator(True) if in_headings else 'нет ' + _indicator(False)}")
            lines.append(f"- **В первом абзаце:** {'да ' + _indicator(True) if in_first_para else 'нет ' + _indicator(False)}")
            lines.append("")

    # --- Readability ---
    lines.append("## Читаемость")
    lines.append("")
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", plain_text) if s.strip()]
    sent_count = len(sentences)
    readable_ok = avg_sent_len <= 20
    lines.append(f"- **Предложений:** {sent_count}")
    lines.append(f"- **Среднее слов в предложении:** {avg_sent_len:.1f} {_indicator(readable_ok)}")
    if not readable_ok:
        lines.append("  ⚠ Предложения слишком длинные. Рекомендуется до 20 слов.")
    else:
        lines.append("  ✓ Хорошая читаемость.")
    lines.append("")

    # --- Summary ---
    lines.append("## Итого")
    lines.append("")
    issues: list[str] = []
    if short_warning:
        issues.append(f"текст короткий ({total_words} слов)")
    if not has_h1:
        issues.append("нет H1")
    if not has_h2:
        issues.append("нет H2")
    if not readable_ok:
        issues.append(f"длинные предложения (ср. {avg_sent_len:.0f} слов)")

    if issues:
        lines.append(f"⚠ Найдены замечания: {', '.join(issues)}.")
    else:
        lines.append("✓ Текст соответствует базовым SEO-требованиям.")
    lines.append("")

    return "\n".join(lines)
