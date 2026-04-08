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
