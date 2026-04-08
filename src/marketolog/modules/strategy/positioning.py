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

    # Weak spots
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
