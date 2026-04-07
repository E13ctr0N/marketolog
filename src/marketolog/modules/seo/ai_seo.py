"""AI-SEO readiness check — evaluates how well a page supports AI crawlers."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

# AI crawlers to audit
AI_CRAWLERS = [
    "GPTBot",
    "ClaudeBot",
    "PerplexityBot",
    "GoogleOther",
    "Applebot-Extended",
]

_CACHE_NAMESPACE = "ai_seo"
_CACHE_TTL = 3600


def _get_domain_root(url: str) -> str:
    """Extract scheme + netloc from URL, e.g. 'https://example.com'."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _parse_robots(robots_text: str) -> dict[str, str]:
    """Parse robots.txt and return status for each AI crawler.

    Returns dict: bot_name -> one of:
      "разрешён", "заблокирован", "частично заблокирован", "не упомянут"
    """
    result = {bot: "не упомянут" for bot in AI_CRAWLERS}

    # Split into blocks per User-agent
    lines = robots_text.splitlines()

    # Collect groups: list of (user_agents_list, rules_list)
    groups: list[tuple[list[str], list[str]]] = []
    current_agents: list[str] = []
    current_rules: list[str] = []
    in_block = False

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            if in_block and current_agents:
                groups.append((list(current_agents), list(current_rules)))
                current_agents.clear()
                current_rules.clear()
                in_block = False
            continue

        if line.lower().startswith("user-agent:"):
            agent = line[len("user-agent:"):].strip()
            if in_block and current_rules:
                # New agent group starting mid-block
                groups.append((list(current_agents), list(current_rules)))
                current_agents.clear()
                current_rules.clear()
            current_agents.append(agent)
            in_block = True
        elif line.lower().startswith("disallow:") or line.lower().startswith("allow:"):
            current_rules.append(line)

    if in_block and current_agents:
        groups.append((current_agents, current_rules))

    for agents, rules in groups:
        for bot in AI_CRAWLERS:
            # Check if this bot (case-insensitive) is in the agent list
            matched = any(a.strip().lower() == bot.lower() for a in agents)
            if not matched:
                continue

            disallow_rules = [
                r[len("disallow:"):].strip()
                for r in rules
                if r.lower().startswith("disallow:")
            ]
            allow_rules = [
                r[len("allow:"):].strip()
                for r in rules
                if r.lower().startswith("allow:")
            ]

            if not disallow_rules and not allow_rules:
                result[bot] = "разрешён"
            elif any(d == "/" for d in disallow_rules):
                result[bot] = "заблокирован"
            elif disallow_rules and any(d != "" for d in disallow_rules):
                result[bot] = "частично заблокирован"
            elif allow_rules:
                result[bot] = "разрешён"
            else:
                result[bot] = "разрешён"

    return result


def _check_schema_markup(html: str) -> bool:
    """Return True if page contains JSON-LD schema markup."""
    soup = BeautifulSoup(html, "lxml")
    scripts = soup.find_all("script", type="application/ld+json")
    return len(scripts) > 0


def _get_body_text(html: str) -> str:
    """Extract visible body text from HTML (without JS execution)."""
    soup = BeautifulSoup(html, "lxml")
    # Remove script and style tags
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    body = soup.find("body")
    if body is None:
        return ""
    return " ".join(body.get_text(separator=" ").split())


def _build_report(
    url: str,
    crawler_status: dict[str, str],
    has_llms_txt: bool,
    has_schema: bool,
    body_text: str,
) -> str:
    """Format the final Markdown report."""
    lines: list[str] = []

    lines.append(f"## AI-SEO Readiness Check: {url}")
    lines.append("")

    # --- AI Crawlers ---
    lines.append("### AI-краулеры (robots.txt)")
    for bot, status in crawler_status.items():
        lines.append(f"- **{bot}**: {status}")
    lines.append("")

    # --- llms.txt ---
    lines.append("### llms.txt")
    if has_llms_txt:
        lines.append("- Файл `/llms.txt` **присутствует** на сайте.")
    else:
        lines.append("- Файл `/llms.txt` **не найден** (404).")
    lines.append("")

    # --- Schema Markup ---
    lines.append("### Schema Markup (JSON-LD)")
    if has_schema:
        lines.append("- Структурированная разметка JSON-LD **обнаружена** на странице.")
    else:
        lines.append("- Структурированная разметка JSON-LD **не обнаружена**.")
    lines.append("")

    # --- Content without JS ---
    lines.append("### Контент без JavaScript")
    text_len = len(body_text)
    if text_len > 50:
        lines.append(
            f"- Страница содержит доступный текстовый контент ({text_len} символов) — "
            "AI-краулеры смогут проиндексировать контент без JS."
        )
    else:
        lines.append(
            f"- Текстовый контент без JS **недостаточен** ({text_len} символов). "
            "Страница может быть недоступна для AI-краулеров, не выполняющих JavaScript."
        )
    lines.append("")

    # --- Recommendations ---
    lines.append("### Рекомендации")
    recs: list[str] = []

    blocked = [b for b, s in crawler_status.items() if s == "заблокирован"]
    partial = [b for b, s in crawler_status.items() if s == "частично заблокирован"]
    not_mentioned = [b for b, s in crawler_status.items() if s == "не упомянут"]

    if blocked:
        recs.append(
            f"Снимите полную блокировку для AI-краулеров в robots.txt: {', '.join(blocked)}."
        )
    if partial:
        recs.append(
            f"Проверьте частичные ограничения для {', '.join(partial)} — убедитесь, "
            "что ключевые страницы доступны для индексации."
        )
    if not_mentioned:
        recs.append(
            f"Добавьте явные правила в robots.txt для: {', '.join(not_mentioned)} — "
            "это даёт краулерам сигнал о вашей политике."
        )
    if not has_llms_txt:
        recs.append(
            "Создайте файл `/llms.txt` с описанием сайта и ключевых разделов — "
            "это помогает LLM-системам лучше понять ваш контент."
        )
    if not has_schema:
        recs.append(
            "Добавьте JSON-LD разметку Schema.org — это улучшает понимание контента "
            "AI-системами и поисковыми движками."
        )
    if text_len <= 50:
        recs.append(
            "Обеспечьте доступность текстового контента без JavaScript — "
            "используйте SSR или статическую генерацию страниц."
        )

    if recs:
        for rec in recs:
            lines.append(f"- {rec}")
    else:
        lines.append("- Сайт хорошо подготовлен для AI-краулеров. Продолжайте в том же духе!")

    return "\n".join(lines)


async def run_ai_seo_check(url: str, *, cache: FileCache) -> str:
    """Run AI-SEO readiness check for the given URL.

    Checks:
    1. robots.txt for AI crawler rules (GPTBot, ClaudeBot, PerplexityBot,
       GoogleOther, Applebot-Extended)
    2. /llms.txt existence
    3. JSON-LD schema markup on the page
    4. Meaningful text content accessible without JS

    Results are cached for 3600 seconds.

    Args:
        url: The page URL to audit.
        cache: FileCache instance for caching results.

    Returns:
        Formatted Markdown report string.
    """
    cached = cache.get(_CACHE_NAMESPACE, url)
    if cached is not None:
        return cached  # type: ignore[return-value]

    domain = _get_domain_root(url)

    # Fetch robots.txt
    robots_text = ""
    try:
        robots_resp = await fetch_with_retry(f"{domain}/robots.txt")
        if robots_resp.status_code == 200:
            robots_text = robots_resp.text
    except Exception:
        pass

    crawler_status = _parse_robots(robots_text)

    # Check llms.txt
    has_llms_txt = False
    try:
        llms_resp = await fetch_with_retry(f"{domain}/llms.txt")
        has_llms_txt = llms_resp.status_code == 200
    except Exception:
        pass

    # Fetch page HTML
    page_html = ""
    try:
        page_resp = await fetch_with_retry(url)
        if page_resp.status_code == 200:
            page_html = page_resp.text
    except Exception:
        pass

    has_schema = _check_schema_markup(page_html)
    body_text = _get_body_text(page_html)

    report = _build_report(url, crawler_status, has_llms_txt, has_schema, body_text)

    cache.set(_CACHE_NAMESPACE, url, report, ttl_seconds=_CACHE_TTL)

    return report
