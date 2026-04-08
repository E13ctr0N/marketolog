"""Content plan tool — assembles project context for Claude to generate a content calendar."""

from typing import Any


def run_content_plan(
    project_context: dict[str, Any],
    period: str = "1 month",
    topics_count: int = 10,
) -> str:
    """Assemble a structured content plan brief for Claude.

    Does NOT call any external API — builds a context-rich Markdown prompt
    that Claude can use to generate a content calendar.

    Args:
        project_context: Full project context dict with niche, audience, SEO, etc.
        period: Calendar period (e.g. "1 week", "2 weeks", "1 month").
        topics_count: Number of content topics to request.

    Returns:
        Markdown string with project context and structured assignment for Claude.
    """
    name = project_context.get("name", "")
    url = project_context.get("url", "")
    niche = project_context.get("niche", "")
    description = project_context.get("description", "")
    tone_of_voice = project_context.get("tone_of_voice", "")

    # SEO keywords
    seo = project_context.get("seo", {})
    main_keywords: list[str] = seo.get("main_keywords", [])

    # Target audience
    target_audience: list[dict] = project_context.get("target_audience", [])

    # Competitors
    competitors: list[dict] = project_context.get("competitors", [])

    # Social channels
    social: dict = project_context.get("social", {})

    # --- Build sections ---
    lines: list[str] = []

    lines.append("# Контент-план: задание для составления")
    lines.append("")

    # Project context section
    lines.append("## Контекст проекта")
    lines.append("")
    if name:
        lines.append(f"- **Название:** {name}")
    if url:
        lines.append(f"- **Сайт:** {url}")
    if niche:
        lines.append(f"- **Ниша:** {niche}")
    if description:
        lines.append(f"- **Описание:** {description}")
    if tone_of_voice:
        lines.append(f"- **Tone of Voice:** {tone_of_voice}")
    lines.append("")

    # SEO keywords section
    if main_keywords:
        lines.append("## SEO-ключевые слова")
        lines.append("")
        for kw in main_keywords:
            lines.append(f"- {kw}")
        lines.append("")

    # Target audience section
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

    # Competitors section
    if competitors:
        lines.append("## Конкуренты")
        lines.append("")
        for comp in competitors:
            comp_name = comp.get("name", "")
            comp_url = comp.get("url", "")
            if comp_url:
                lines.append(f"- [{comp_name}]({comp_url})")
            else:
                lines.append(f"- {comp_name}")
        lines.append("")

    # Channels section
    if social:
        lines.append("## Каналы публикации")
        lines.append("")
        channel_map = {
            "telegram_channel": "Telegram",
            "vk_group": "ВКонтакте",
            "instagram": "Instagram",
            "youtube": "YouTube",
            "tiktok": "TikTok",
            "dzen": "Дзен",
            "blog": "Блог",
        }
        for key, label in channel_map.items():
            value = social.get(key)
            if value:
                lines.append(f"- {label}: {value}")
        lines.append("")

    # Assignment section
    lines.append("## Задание")
    lines.append("")
    lines.append(
        f"Составь контент-план на **{period}** — **{topics_count} тем**."
    )
    lines.append("")
    lines.append(
        "Для каждой темы укажи в виде нумерованного списка:"
    )
    lines.append("")
    lines.append("1. **Заголовок** — цепляющий, под SEO если применимо")
    lines.append("2. **Формат** — статья / пост / видео / сторис / карточки и т.д.")
    lines.append("3. **Ключевые слова** — релевантные из списка выше или смежные")
    lines.append("4. **Платформа** — куда публикуем")
    lines.append("5. **Аудитория** — для какого сегмента")
    lines.append("6. **Главный тезис** — одно предложение, суть материала")
    lines.append("")
    lines.append(
        "Темы должны охватывать разные сегменты аудитории, форматы и этапы воронки "
        "(осведомлённость, рассмотрение, решение)."
    )

    return "\n".join(lines)
