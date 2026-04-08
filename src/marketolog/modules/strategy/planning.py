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
