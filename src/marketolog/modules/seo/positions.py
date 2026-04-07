"""SEO position tracking via Yandex Search XML API."""

from urllib.parse import urlparse
from xml.etree import ElementTree as ET

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.formatting import format_tabular
from marketolog.utils.http import fetch_with_retry

YANDEX_SEARCH_URL = "https://yandex.ru/search/xml"
POSITIONS_CACHE_TTL = 21600  # 6 hours


async def _search_yandex(query: str, config: MarketologConfig) -> list[dict]:
    """Call Yandex Search XML API and return ranked results.

    Returns:
        List of dicts: [{"position": N, "url": "...", "title": "..."}, ...]
    """
    params = {
        "user": config.yandex_search_api_key,
        "key": config.yandex_folder_id,
        "query": query,
        "lr": "213",
        "groupby": "attr=d.mode=deep.groups-on-page=50.docs-in-group=1",
    }

    response = await fetch_with_retry(YANDEX_SEARCH_URL, params=params)

    if response.status_code != 200:
        return []

    try:
        root = ET.fromstring(response.text)
    except ET.ParseError:
        return []

    results: list[dict] = []
    position = 0

    # Namespace-agnostic search for <group> elements
    for group in root.iter("group"):
        doc = group.find("doc")
        if doc is None:
            continue

        url_el = doc.find("url")
        title_el = doc.find("title")

        url = url_el.text.strip() if url_el is not None and url_el.text else ""
        title = title_el.text.strip() if title_el is not None and title_el.text else ""

        position += 1
        results.append({"position": position, "url": url, "title": title})

    return results


def _extract_domain(url: str) -> str:
    """Return the netloc (hostname) from a URL, stripping 'www.'."""
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    return host.removeprefix("www.")


async def run_check_positions(
    keywords: list[str],
    site_url: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    """Check Yandex search positions for the given keywords and site.

    Args:
        keywords: List of search queries to check.
        site_url: The site whose position we track (e.g. "https://example.ru").
        config: Marketolog configuration with API credentials.
        cache: File-based cache for storing results.

    Returns:
        CSV-formatted string with columns: keyword, position, url, title.
    """
    if not config.is_configured("yandex_search_api_key"):
        return (
            "Для проверки позиций необходимо настроить Yandex Search API.\n\n"
            "Добавьте ключ в конфигурацию:\n"
            "  YANDEX_SEARCH_API_KEY=<ваш ключ>\n"
            "  YANDEX_FOLDER_ID=<идентификатор папки>\n\n"
            "Получить ключ можно в Яндекс.Вебмастере: "
            "https://webmaster.yandex.ru/tools/xml-search-api/"
        )

    target_domain = _extract_domain(site_url)
    rows: list[dict] = []

    for keyword in keywords:
        cache_key = f"{keyword}|{target_domain}"
        cached = cache.get("positions", cache_key)

        if cached is not None:
            rows.append(cached)
            continue

        search_results = await _search_yandex(keyword, config)

        found_row: dict | None = None
        for item in search_results:
            item_domain = _extract_domain(item["url"])
            if target_domain in item_domain or item_domain in target_domain:
                found_row = {
                    "keyword": keyword,
                    "position": str(item["position"]),
                    "url": item["url"],
                    "title": item["title"],
                }
                break

        if found_row is None:
            found_row = {
                "keyword": keyword,
                "position": "не найден (>50)",
                "url": "",
                "title": "",
            }

        cache.set("positions", cache_key, found_row, ttl_seconds=POSITIONS_CACHE_TTL)
        rows.append(found_row)

    return format_tabular(rows)
