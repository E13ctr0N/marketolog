"""Google Search Console API — search performance report."""

from urllib.parse import quote

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.formatting import format_tabular
from marketolog.utils.http import fetch_with_retry

SC_API_BASE = "https://www.googleapis.com/webmasters/v3/sites"
CACHE_NS = "search_console"
CACHE_TTL = 1800

SETUP_INSTRUCTIONS = """\
Google Search Console не настроен.

Для использования задайте переменную окружения:

    GOOGLE_SC_CREDENTIALS=/path/to/service-account.json

1. Создайте Service Account в Google Cloud Console
2. Добавьте его email в Search Console как пользователя
3. Скачайте JSON-ключ и укажите путь в переменной
"""


def _get_access_token(credentials_path: str) -> str | None:
    """Get Google access token from service account JSON.
    Uses google-auth library if available, otherwise returns None.
    """
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
        credentials.refresh(Request())
        return credentials.token
    except ImportError:
        return None
    except Exception:
        return None


async def run_search_console_report(
    site_url: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
    period: str = "7d",
) -> str:
    if not config.is_configured("google_sc_credentials"):
        return SETUP_INSTRUCTIONS

    cache_key = f"{site_url}:{period}"
    cached = cache.get(CACHE_NS, cache_key)
    if cached is not None:
        return cached

    creds_path: str = config.google_sc_credentials
    token = _get_access_token(creds_path)
    if token is None:
        return (
            "Не удалось получить токен Google SC.\n\n"
            "Убедитесь, что установлен пакет `google-auth`:\n"
            "    pip install google-auth\n\n"
            "И что путь в GOOGLE_SC_CREDENTIALS указывает на валидный service account JSON."
        )

    from datetime import date, timedelta
    today = date.today()
    end_date = today - timedelta(days=3)
    days_map = {"7d": 7, "28d": 28, "90d": 90}
    days = days_map.get(period, 7)
    start_date = end_date - timedelta(days=days)

    encoded_url = quote(site_url, safe="")
    api_url = f"{SC_API_BASE}/{encoded_url}/searchAnalytics/query"

    body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["query"],
        "rowLimit": 50,
    }

    resp = await fetch_with_retry(
        api_url,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
    )

    if resp.status_code != 200:
        return f"Ошибка Google SC (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json()
    report = _format_sc_report(site_url, period, data)

    cache.set(CACHE_NS, cache_key, report, ttl_seconds=CACHE_TTL)
    return report


def _format_sc_report(site_url: str, period: str, data: dict) -> str:
    lines = [f"## Google Search Console: {site_url} (период: {period})\n"]

    rows = data.get("rows", [])
    if not rows:
        lines.append("Нет данных за выбранный период.")
        return "\n".join(lines)

    total_clicks = sum(r.get("clicks", 0) for r in rows)
    total_impressions = sum(r.get("impressions", 0) for r in rows)
    avg_ctr = total_clicks / total_impressions if total_impressions > 0 else 0

    lines.append("### Сводка")
    lines.append(f"- **Клики:** {total_clicks:,}")
    lines.append(f"- **Показы:** {total_impressions:,}")
    lines.append(f"- **Средний CTR:** {avg_ctr:.1%}")
    lines.append("")

    lines.append("### Топ запросы")
    table_data = [
        {
            "Запрос": r["keys"][0] if r.get("keys") else "—",
            "Клики": r.get("clicks", 0),
            "Показы": r.get("impressions", 0),
            "CTR": f"{r.get('ctr', 0):.1%}",
            "Позиция": round(r.get("position", 0), 1),
        }
        for r in rows
    ]
    lines.append(format_tabular(table_data))

    return "\n".join(lines)
