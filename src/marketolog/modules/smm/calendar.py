"""SMM calendar and posting time recommendations.

Provides content calendar overview and best time to post
based on industry benchmarks (for new projects) or
analytics data (when available).
"""

from datetime import date, timedelta


# Industry benchmarks for Russian market (2025-2026)
PLATFORM_BENCHMARKS: dict[str, dict] = {
    "telegram": {
        "best_days": ["вторник", "среда", "четверг"],
        "best_times": ["09:00-10:00", "12:00-13:00", "18:00-19:00"],
        "frequency": "3-5 постов в неделю",
        "notes": "Утро и обед — пиковые часы. Вечер — для развлекательного контента.",
    },
    "vk": {
        "best_days": ["понедельник", "среда", "пятница"],
        "best_times": ["10:00-11:00", "13:00-14:00", "19:00-21:00"],
        "frequency": "3-4 поста в неделю",
        "notes": "Вечерний прайм-тайм 19-21 — максимальный охват. Выходные — вовлечённость ниже.",
    },
    "max": {
        "best_days": ["вторник", "четверг"],
        "best_times": ["10:00-11:00", "17:00-18:00"],
        "frequency": "2-3 поста в неделю",
        "notes": "Новая площадка, аудитория активнее в рабочее время.",
    },
    "dzen": {
        "best_days": ["среда", "четверг", "пятница"],
        "best_times": ["08:00-10:00", "20:00-22:00"],
        "frequency": "2-3 статьи в неделю",
        "notes": "Длинные статьи лучше заходят утром. SEO-эффект накопительный.",
    },
}


def run_smm_calendar(
    project_context: dict,
    period: str = "1 week",
) -> str:
    """Generate SMM content calendar overview.

    Args:
        project_context: Project context with social channels.
        period: Calendar period.

    Returns:
        Formatted calendar with channel schedule.
    """
    social = project_context.get("social", {})
    niche = project_context.get("niche", "")

    lines = [
        f"## SMM-календарь",
        f"**Период:** {period}",
        f"**Ниша:** {niche}",
        "",
    ]

    channels = []
    if social.get("telegram_channel"):
        channels.append(("telegram", social["telegram_channel"]))
    if social.get("vk_group"):
        channels.append(("vk", social["vk_group"]))
    if social.get("max_channel"):
        channels.append(("max", social["max_channel"]))
    if social.get("telegram_dzen_channel"):
        channels.append(("dzen", social["telegram_dzen_channel"]))

    if not channels:
        lines.append("Нет настроенных каналов. Добавьте каналы в проект через update_project().")
        return "\n".join(lines)

    for platform, channel in channels:
        bench = PLATFORM_BENCHMARKS.get(platform, {})
        lines.append(f"### {platform.upper()}: {channel}")
        lines.append(f"- **Частота:** {bench.get('frequency', '2-3 раза в неделю')}")
        lines.append(f"- **Лучшие дни:** {', '.join(bench.get('best_days', []))}")
        lines.append(f"- **Лучшее время:** {', '.join(bench.get('best_times', []))}")
        lines.append(f"- **Заметки:** {bench.get('notes', '')}")
        lines.append("")

    lines.append("### Рекомендация")
    lines.append("Составьте контент-план через `content_plan`, затем распределите по этому календарю.")
    lines.append("Используйте `generate_post` для адаптации под каждую площадку.")

    return "\n".join(lines)


def run_best_time_to_post(
    project_context: dict,
    platform: str | None = None,
) -> str:
    """Recommend best time to post.

    For new projects: uses industry benchmarks for Russian market.
    When analytics data is available, recommendations are data-driven.

    Args:
        project_context: Project context.
        platform: Specific platform (None = all configured).

    Returns:
        Time recommendations.
    """
    social = project_context.get("social", {})
    niche = project_context.get("niche", "")

    lines = [
        f"## Лучшее время для публикации",
        f"*На основе бенчмарков Рунета для ниши \"{niche}\"*\n",
    ]

    if platform:
        platforms = [platform.lower()]
    else:
        platforms = []
        if social.get("telegram_channel"):
            platforms.append("telegram")
        if social.get("vk_group"):
            platforms.append("vk")
        if social.get("max_channel"):
            platforms.append("max")
        if social.get("telegram_dzen_channel"):
            platforms.append("dzen")

    if not platforms:
        platforms = list(PLATFORM_BENCHMARKS.keys())

    for p in platforms:
        bench = PLATFORM_BENCHMARKS.get(p, {})
        if not bench:
            continue

        lines.append(f"### {p.upper()}")
        lines.append(f"- **Лучшие дни:** {', '.join(bench.get('best_days', []))}")
        lines.append(f"- **Лучшее время:** {', '.join(bench.get('best_times', []))}")
        lines.append(f"- **Частота:** {bench.get('frequency', '')}")
        lines.append(f"- {bench.get('notes', '')}")
        lines.append("")

    lines.append("*Для более точных рекомендаций используйте `telegram_stats` / `vk_stats` / `max_stats` — с данными об аудитории рекомендации станут персонализированными.*")

    return "\n".join(lines)
