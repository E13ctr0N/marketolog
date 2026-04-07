"""Yandex Webmaster API report tool.

Fetches indexing statistics, diagnostics, and popular search queries
for a given host from the Yandex Webmaster API.
"""

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.formatting import format_tabular
from marketolog.utils.http import fetch_with_retry

BASE_URL = "https://api.webmaster.yandex.net/v4"

SETUP_INSTRUCTIONS = """\
Yandex Webmaster не настроен.

Для использования инструмента задайте переменную окружения:

    YANDEX_OAUTH_TOKEN=<ваш OAuth-токен>

Получить токен можно на https://oauth.yandex.ru/
(создайте приложение с доступом к Яндекс.Вебмастеру).
"""


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"OAuth {token}"}


def _encode_host_id(host: str) -> str:
    """Encode host URL to Yandex Webmaster host_id format.

    E.g. https://example.ru → https:example.ru:443
         http://example.ru  → http:example.ru:80
    """
    if host.startswith("https://"):
        domain = host[len("https://"):].rstrip("/")
        return f"https:{domain}:443"
    if host.startswith("http://"):
        domain = host[len("http://"):].rstrip("/")
        return f"http:{domain}:80"
    return host


async def _get_user_id(token: str) -> str:
    resp = await fetch_with_retry(
        f"{BASE_URL}/user",
        headers=_auth_headers(token),
    )
    resp.raise_for_status()
    return str(resp.json()["user_id"])


async def _get_host_id(token: str, user_id: str, host: str) -> str | None:
    """Find the host_id that matches the given host URL."""
    resp = await fetch_with_retry(
        f"{BASE_URL}/user/{user_id}/hosts",
        headers=_auth_headers(token),
    )
    resp.raise_for_status()
    data = resp.json()

    normalized_host = host.rstrip("/")
    for entry in data.get("hosts", []):
        if entry.get("unicode_host_url", "").rstrip("/") == normalized_host or \
           entry.get("host_url", "").rstrip("/") == normalized_host:
            return entry["host_id"]

    # Fallback: use encoded form if no match found
    return _encode_host_id(host)


async def _get_popular_queries(token: str, user_id: str, host_id: str) -> list[dict]:
    resp = await fetch_with_retry(
        f"{BASE_URL}/user/{user_id}/hosts/{host_id}/search-queries/popular",
        headers=_auth_headers(token),
    )
    if resp.status_code != 200:
        return []
    return resp.json().get("queries", [])


async def _get_diagnostics(token: str, user_id: str, host_id: str) -> list[dict]:
    resp = await fetch_with_retry(
        f"{BASE_URL}/user/{user_id}/hosts/{host_id}/diagnostics",
        headers=_auth_headers(token),
    )
    if resp.status_code != 200:
        return []
    return resp.json().get("indicators", [])


async def _get_indexing_history(token: str, user_id: str, host_id: str) -> list[dict]:
    resp = await fetch_with_retry(
        f"{BASE_URL}/user/{user_id}/hosts/{host_id}/indexing/history",
        headers=_auth_headers(token),
    )
    if resp.status_code != 200:
        return []
    return resp.json().get("history", [])


def _format_report(
    host: str,
    history: list[dict],
    diagnostics: list[dict],
    queries: list[dict],
) -> str:
    lines: list[str] = [f"## Отчёт Яндекс.Вебмастер: {host}", ""]

    # --- Индексация ---
    lines.append("### Индексация страниц")
    if history:
        latest = history[-1]
        pages = latest.get("pages_count", "—")
        excluded = latest.get("excluded_count", "—")
        lines.append(f"Страниц в индексе: **{pages}**")
        lines.append(f"Исключено: {excluded}")

        if len(history) >= 2:
            first_count = history[0].get("pages_count", 0)
            last_count = history[-1].get("pages_count", 0)
            if isinstance(first_count, int) and isinstance(last_count, int):
                delta = last_count - first_count
                trend_sign = "+" if delta >= 0 else ""
                lines.append(f"Тренд за период: {trend_sign}{delta} страниц")
    else:
        lines.append("Данные об индексации недоступны.")
    lines.append("")

    # --- Проблемы ---
    lines.append("### Проблемы сайта")
    if diagnostics:
        for item in diagnostics:
            severity = item.get("severity", "INFO")
            indicator = item.get("indicator", "")
            message = item.get("message", "")
            lines.append(f"- [{severity}] {indicator}: {message}")
    else:
        lines.append("Проблем не обнаружено.")
    lines.append("")

    # --- Популярные запросы ---
    lines.append("### Популярные поисковые запросы")
    if queries:
        table_data = [
            {
                "Запрос": q.get("query_text", ""),
                "Позиция": q.get("position", "—"),
                "Клики": q.get("clicks", 0),
                "Показы": q.get("impressions", 0),
            }
            for q in queries
        ]
        lines.append(format_tabular(table_data))
    else:
        lines.append("Данные о запросах недоступны.")

    return "\n".join(lines)


async def run_webmaster_report(
    host: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    """Generate a Yandex Webmaster report for the given host.

    Args:
        host: The site URL to report on (e.g. "https://example.ru").
        config: Marketolog configuration with API credentials.
        cache: File cache instance.

    Returns:
        Formatted report string.
    """
    # Step 1: check token
    if not config.is_configured("yandex_oauth_token"):
        return SETUP_INSTRUCTIONS

    token: str = config.yandex_oauth_token  # type: ignore[assignment]

    # Step 2: check cache
    cached = cache.get("webmaster", host)
    if cached is not None:
        return cached

    # Step 3: get user_id
    user_id = await _get_user_id(token)

    # Step 4: get host_id
    host_id = await _get_host_id(token, user_id, host)

    # Steps 5-7: fetch data in order
    queries = await _get_popular_queries(token, user_id, host_id)
    diagnostics = await _get_diagnostics(token, user_id, host_id)
    history = await _get_indexing_history(token, user_id, host_id)

    # Step 8: format report
    report = _format_report(host, history, diagnostics, queries)

    # Step 9: cache with TTL 3600
    cache.set("webmaster", host, report, ttl_seconds=3600)

    return report
