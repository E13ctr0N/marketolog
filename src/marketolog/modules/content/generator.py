"""Content generation tools — assemble structured briefs for Claude.

These functions do NOT call any external API or generate text themselves.
They build context-rich Markdown prompts that Claude uses to produce content.
"""

from typing import Any

# ---------------------------------------------------------------------------
# Platform guidelines
# ---------------------------------------------------------------------------

PLATFORM_GUIDELINES: dict[str, dict[str, Any]] = {
    "telegram": {
        "name": "Telegram",
        "max_length": 4096,
        "format": "Короткие абзацы, эмодзи, жирный текст через **",
        "style": "Разговорный, неформальный, на ты",
        "features": "Эмодзи в начале абзацев, форматирование Markdown, призыв к реакции",
    },
    "vk": {
        "name": "ВКонтакте (VK)",
        "max_length": 16384,
        "format": "Смешанный — короткий или длинный текст, вопросы к аудитории",
        "style": "Дружелюбный, вовлекающий, можно использовать опросы",
        "features": "Вопросы в конце, хэштеги, упоминания, опросы",
    },
    "max": {
        "name": "Max (ex-OK)",
        "max_length": 4096,
        "format": "Короткие абзацы, эмодзи, неформальный тон",
        "style": "Разговорный, как Telegram",
        "features": "Эмодзи, форматирование, реакции",
    },
    "dzen": {
        "name": "Дзен",
        "max_length": 0,  # unlimited
        "format": "Лонгрид, SEO-оптимизированный заголовок, подзаголовки H2/H3",
        "style": "Экспертный, информационный, развёрнутые объяснения",
        "features": "SEO-заголовки, оглавление, форматирование статьи",
    },
    "carousel": {
        "name": "Карусель (слайды)",
        "max_length": 0,
        "format": "5–10 слайдов, каждый — одна мысль, крупный текст",
        "style": "Лаконичный, визуальный, тезисный",
        "features": "Заголовок-слайд, по одному тезису на слайд, финальный CTA-слайд",
    },
    "video_script": {
        "name": "Сценарий видео",
        "max_length": 0,
        "format": "Хук (0–5 сек), основная часть, CTA в конце",
        "style": "Разговорный, динамичный, с паузами",
        "features": "Секунды тайминга, ремарки для монтажа, хук в самом начале",
    },
}

# Word-count targets by length label
_LENGTH_TARGETS: dict[str, str] = {
    "short": "~800 слов",
    "medium": "~1500 слов",
    "long": "~3000 слов",
}

# Default repurposing formats when caller doesn't specify
_DEFAULT_FORMATS = ["telegram", "vk", "carousel"]


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def run_generate_article(
    topic: str,
    project_context: dict[str, Any],
    keywords: list[str] | None = None,
    length: str = "medium",
) -> str:
    """Assemble an SEO article brief for Claude.

    Args:
        topic: Article topic / working title.
        project_context: Full project context dict.
        keywords: Target SEO keywords. Falls back to project SEO keywords if None.
        length: One of "short" (~800 words), "medium" (~1500), "long" (~3000).

    Returns:
        Markdown string with structured article brief.
    """
    niche = project_context.get("niche", "")
    tone_of_voice = project_context.get("tone_of_voice", "")
    description = project_context.get("description", "")

    # Keywords: use provided, otherwise fall back to project SEO keywords
    seo = project_context.get("seo", {})
    project_keywords: list[str] = seo.get("main_keywords", [])
    effective_keywords = keywords if keywords is not None else project_keywords

    # Target audience
    target_audience: list[dict] = project_context.get("target_audience", [])

    # Length target
    length_target = _LENGTH_TARGETS.get(length, _LENGTH_TARGETS["medium"])

    lines: list[str] = []

    lines.append("# Задание: написать SEO-статью")
    lines.append("")

    # --- Project context ---
    lines.append("## Контекст проекта")
    lines.append("")
    if niche:
        lines.append(f"- **Ниша:** {niche}")
    if description:
        lines.append(f"- **Продукт:** {description}")
    if tone_of_voice:
        lines.append(f"- **Tone of Voice:** {tone_of_voice}")
    lines.append("")

    # --- Article spec ---
    lines.append("## Параметры статьи")
    lines.append("")
    lines.append(f"- **Тема:** {topic}")
    lines.append(f"- **Объём:** {length_target}")
    if effective_keywords:
        kw_str = ", ".join(effective_keywords)
        lines.append(f"- **Ключевые слова:** {kw_str}")
    lines.append("")

    # --- Target audience ---
    if target_audience:
        lines.append("## Целевая аудитория")
        lines.append("")
        for segment in target_audience:
            seg_name = segment.get("segment", "")
            pain = segment.get("pain", "")
            if pain:
                lines.append(f"- **{seg_name}** — боль: {pain}")
            else:
                lines.append(f"- {seg_name}")
        lines.append("")

    # --- Structure guidelines ---
    lines.append("## Структура статьи")
    lines.append("")
    lines.append("Придерживайся следующей структуры:")
    lines.append("")
    if effective_keywords:
        lines.append(
            f"- **H1** — заголовок статьи, содержит главный ключевой запрос «{effective_keywords[0]}»"
        )
    else:
        lines.append("- **H1** — заголовок статьи, содержит главный ключевой запрос")
    lines.append("- **Вступление** — 2–3 абзаца, проблема читателя + что он узнает из статьи")
    lines.append("- **3–5 разделов H2** — каждый раскрывает один аспект темы")
    lines.append("  - Внутри H2 можно использовать H3 для подпунктов")
    lines.append("  - Каждый раздел заканчивается кратким выводом или советом")
    lines.append("- **Заключение** — краткое резюме + призыв к действию")
    lines.append("")

    # --- SEO instructions ---
    if effective_keywords:
        lines.append("## SEO-рекомендации")
        lines.append("")
        lines.append("- Включи ключевые слова естественным образом — не переспамливай")
        lines.append(f"- Главный ключ «{effective_keywords[0]}» — в H1, первом абзаце и заключении")
        if len(effective_keywords) > 1:
            secondary = ", ".join(f"«{k}»" for k in effective_keywords[1:])
            lines.append(f"- Вторичные ключи {secondary} — в H2 и теле статьи")
        lines.append("- Мета-описание — до 160 символов, включи главный ключ")
        lines.append("")

    # --- Tone instructions ---
    lines.append("## Стиль и тон")
    lines.append("")
    if tone_of_voice:
        lines.append(f"Пиши в стиле: **{tone_of_voice}**")
    lines.append("- Избегай канцелярита и пассивного залога")
    lines.append("- Используй конкретные примеры и цифры")
    lines.append("- Разбивай длинные предложения на короткие")
    lines.append("")

    return "\n".join(lines)


def run_generate_post(
    platform: str,
    project_context: dict[str, Any],
    topic: str | None = None,
) -> str:
    """Assemble a social media post brief for Claude.

    Args:
        platform: Target platform key — "telegram", "vk", "max", "dzen".
        project_context: Full project context dict.
        topic: Post topic. If None, Claude is asked to suggest based on niche.

    Returns:
        Markdown string with structured post brief.
    """
    niche = project_context.get("niche", "")
    tone_of_voice = project_context.get("tone_of_voice", "")
    description = project_context.get("description", "")

    # SEO keywords for context
    seo = project_context.get("seo", {})
    project_keywords: list[str] = seo.get("main_keywords", [])

    # Platform info
    guide = PLATFORM_GUIDELINES.get(platform, PLATFORM_GUIDELINES["telegram"])
    platform_name = guide["name"]
    max_length = guide["max_length"]
    fmt = guide["format"]
    style = guide["style"]
    features = guide["features"]

    lines: list[str] = []

    lines.append(f"# Задание: написать пост для {platform_name}")
    lines.append("")

    # --- Project context ---
    lines.append("## Контекст проекта")
    lines.append("")
    if niche:
        lines.append(f"- **Ниша:** {niche}")
    if description:
        lines.append(f"- **Продукт:** {description}")
    if tone_of_voice:
        lines.append(f"- **Tone of Voice:** {tone_of_voice}")
    lines.append("")

    # --- Platform spec ---
    lines.append(f"## Платформа: {platform_name}")
    lines.append("")
    if max_length:
        lines.append(f"- **Максимальная длина:** {max_length} символов")
    else:
        lines.append("- **Длина:** без ограничений")
    lines.append(f"- **Формат:** {fmt}")
    lines.append(f"- **Стиль:** {style}")
    lines.append(f"- **Особенности:** {features}")
    lines.append("")

    # --- Topic ---
    lines.append("## Тема поста")
    lines.append("")
    if topic:
        lines.append(f"**{topic}**")
    else:
        lines.append(
            "Тема не задана. Предложи актуальную тему исходя из ниши проекта и ключевых слов:"
        )
        if niche:
            lines.append(f"- Ниша: {niche}")
        if project_keywords:
            lines.append(f"- Ключевые слова: {', '.join(project_keywords)}")
    lines.append("")

    # --- Assignment ---
    lines.append("## Задание")
    lines.append("")
    lines.append(
        f"Напиши готовый пост для публикации в {platform_name}. "
        "Текст должен сразу быть пригоден для копирования без дополнительного редактирования."
    )
    lines.append("")
    lines.append("Требования:")
    lines.append(f"- Соблюдай ограничение длины ({max_length} символов)" if max_length else "- Длина — на твоё усмотрение, исходя из формата")
    lines.append(f"- Используй: {features}")
    if tone_of_voice:
        lines.append(f"- Tone of Voice: {tone_of_voice}")
    lines.append("")

    return "\n".join(lines)


def run_repurpose_content(
    text: str,
    project_context: dict[str, Any],
    formats: list[str] | None = None,
) -> str:
    """Assemble a content repurposing brief for Claude.

    Takes an existing piece of content and asks Claude to adapt it
    to multiple target formats.

    Args:
        text: Source content text (will be truncated to 2000 chars).
        project_context: Full project context dict.
        formats: Target format keys. Defaults to ["telegram", "vk", "carousel"].

    Returns:
        Markdown string with structured repurposing brief.
    """
    tone_of_voice = project_context.get("tone_of_voice", "")
    niche = project_context.get("niche", "")
    description = project_context.get("description", "")

    effective_formats = formats if formats is not None else _DEFAULT_FORMATS

    # Truncate source text
    truncated = text[:2000]
    was_truncated = len(text) > 2000

    lines: list[str] = []

    lines.append("# Задание: адаптировать контент под разные форматы")
    lines.append("")

    # --- Project context ---
    lines.append("## Контекст проекта")
    lines.append("")
    if niche:
        lines.append(f"- **Ниша:** {niche}")
    if description:
        lines.append(f"- **Продукт:** {description}")
    if tone_of_voice:
        lines.append(f"- **Tone of Voice:** {tone_of_voice}")
    lines.append("")

    # --- Source text ---
    lines.append("## Исходный материал")
    lines.append("")
    if was_truncated:
        lines.append("*(текст сокращён до 2000 символов)*")
        lines.append("")
    lines.append(truncated)
    lines.append("")

    # --- Target formats ---
    lines.append("## Целевые форматы")
    lines.append("")
    lines.append(
        "Адаптируй исходный материал под каждый из форматов ниже. "
        "Для каждого формата — отдельный раздел с готовым текстом."
    )
    lines.append("")

    for fmt_key in effective_formats:
        guide = PLATFORM_GUIDELINES.get(fmt_key)
        if guide is None:
            # Unknown format — include as-is
            lines.append(f"### {fmt_key.capitalize()}")
            lines.append("")
            lines.append(f"Адаптируй текст под формат «{fmt_key}».")
            lines.append("")
            continue

        platform_name = guide["name"]
        max_length = guide["max_length"]
        fmt = guide["format"]
        style = guide["style"]
        features = guide["features"]

        lines.append(f"### {platform_name}")
        lines.append("")
        if max_length:
            lines.append(f"- **Длина:** до {max_length} символов")
        else:
            lines.append("- **Длина:** без ограничений")
        lines.append(f"- **Формат:** {fmt}")
        lines.append(f"- **Стиль:** {style}")
        lines.append(f"- **Особенности:** {features}")
        lines.append("")

    # --- Tone reminder ---
    if tone_of_voice:
        lines.append("## Стиль и тон")
        lines.append("")
        lines.append(
            f"Во всех форматах сохраняй tone of voice проекта: **{tone_of_voice}**"
        )
        lines.append("")

    return "\n".join(lines)
