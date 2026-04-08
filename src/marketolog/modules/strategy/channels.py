"""Channel recommendation — prioritized marketing channels with ROI forecast.

Analyzes project context to recommend the most effective channels,
accounting for niche, audience, budget, and available platforms.
"""

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

    has_keywords = bool(seo.get("main_keywords"))
    seo_score = 90 if has_keywords else 70
    scores.append(("seo", seo_score, "органический трафик — самый дешёвый в долгосроке"))

    has_tg = bool(social.get("telegram_channel"))
    tg_score = 85 if has_tg else 60
    scores.append(("telegram", tg_score, "прямой канал связи, высокая вовлечённость" if has_tg else "рекомендуем создать канал"))

    scores.append(("content_marketing", 75, "экспертный контент усиливает все остальные каналы"))

    has_vk = bool(social.get("vk_group"))
    vk_score = 70 if has_vk else 50
    scores.append(("vk", vk_score, "широкий охват + таргетированная реклама" if has_vk else "полезен для B2C-аудитории"))

    has_dzen = bool(social.get("telegram_dzen_channel"))
    dzen_score = 65 if has_dzen else 45
    scores.append(("dzen", dzen_score, "двойной эффект: контент + SEO" if has_dzen else "полезен для SEO-трафика"))

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
        "content_marketing": True,
    }
    return mapping.get(channel_id, False)
