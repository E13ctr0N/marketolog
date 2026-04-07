"""SEO competitor analysis and content gap detection."""

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from marketolog.core.config import MarketologConfig
from marketolog.modules.seo.positions import _search_yandex
from marketolog.utils.cache import FileCache
from marketolog.utils.formatting import format_tabular
from marketolog.utils.http import fetch_with_retry

COMPETITORS_CACHE_TTL = 3600  # 1 hour


def _extract_domain(url: str) -> str:
    """Return the netloc (hostname) from a URL, stripping 'www.'."""
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path
    return host.removeprefix("www.")


def _parse_competitor_page(url: str, html: str) -> dict:
    """Parse competitor HTML and extract SEO-relevant signals.

    Returns a dict with:
      - url
      - title
      - description
      - h1
      - h2_count
      - h2_topics  (list of H2 texts)
      - text_length
      - has_schema  (bool: JSON-LD present)
    """
    soup = BeautifulSoup(html, "lxml")

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Meta description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag.get("content", "").strip() if desc_tag else ""

    # H1
    h1_tag = soup.find("h1")
    h1 = h1_tag.get_text(strip=True) if h1_tag else ""

    # H2 list
    h2_tags = soup.find_all("h2")
    h2_topics = [tag.get_text(strip=True) for tag in h2_tags]
    h2_count = len(h2_topics)

    # Text length (visible text)
    body_tag = soup.find("body")
    body_text = body_tag.get_text(separator=" ", strip=True) if body_tag else soup.get_text(separator=" ", strip=True)
    text_length = len(body_text)

    # JSON-LD schema
    ld_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
    has_schema = len(ld_tags) > 0

    return {
        "url": url,
        "title": title,
        "description": description,
        "h1": h1,
        "h2_count": h2_count,
        "h2_topics": h2_topics,
        "text_length": text_length,
        "has_schema": has_schema,
    }


def _format_competitor_report(data: dict) -> str:
    """Format a single competitor analysis as a readable text block."""
    lines = [
        f"URL: {data['url']}",
        f"Title: {data['title']}",
        f"Description: {data['description']}",
        f"H1: {data['h1']}",
        f"H2 count: {data['h2_count']}",
    ]
    if data["h2_topics"]:
        topics_str = " | ".join(data["h2_topics"])
        lines.append(f"H2 topics: {topics_str}")
    lines.append(f"Text length: {data['text_length']} chars")
    lines.append(f"JSON-LD schema: {'yes' if data['has_schema'] else 'no'}")
    return "\n".join(lines)


async def run_analyze_competitors(
    competitor_urls: list[str],
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    """Fetch and analyze competitor pages.

    For each URL: check cache("competitors", url), if miss → fetch page HTML.
    Parse with BeautifulSoup: title, description, H1, H2 count + topics,
    text length, has JSON-LD schema.

    Args:
        competitor_urls: List of competitor page URLs to analyze.
        config: Marketolog configuration.
        cache: File-based cache for storing results.

    Returns:
        A readable report for each competitor, separated by dividers.
    """
    sections: list[str] = []

    for url in competitor_urls:
        cached = cache.get("competitors", url)

        if cached is not None:
            page_data = cached
        else:
            response = await fetch_with_retry(url)
            if response.status_code != 200:
                sections.append(f"URL: {url}\nError: HTTP {response.status_code}")
                continue

            page_data = _parse_competitor_page(url, response.text)
            cache.set("competitors", url, page_data, ttl_seconds=COMPETITORS_CACHE_TTL)

        sections.append(_format_competitor_report(page_data))

    if not sections:
        return "Не удалось получить данные ни по одному конкуренту."

    divider = "\n" + "─" * 60 + "\n"
    return divider.join(sections)


async def run_content_gap(
    site_url: str,
    competitor_urls: list[str],
    keywords: list[str],
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    """Detect content gaps: keywords where competitors rank but site doesn't.

    For each keyword: call Yandex Search XML API, find site_url and competitor
    domains in results. Gap = competitor ranks but site doesn't (or ranks >20).

    Args:
        site_url: The site we're optimizing.
        competitor_urls: List of competitor URLs/domains to compare against.
        keywords: List of keywords to check.
        config: Marketolog configuration with Yandex Search API credentials.
        cache: File-based cache for storing results.

    Returns:
        CSV table with columns: keyword, your_position, competitor_best, competitor
    """
    if not config.is_configured("yandex_search_api_key"):
        return (
            "Для анализа контентных пробелов необходимо настроить Yandex Search API.\n\n"
            "Добавьте ключ в конфигурацию:\n"
            "  YANDEX_SEARCH_API_KEY=<ваш ключ>\n"
            "  YANDEX_FOLDER_ID=<идентификатор папки>\n\n"
            "Получить ключ можно в Яндекс.Вебмастере: "
            "https://webmaster.yandex.ru/tools/xml-search-api/"
        )

    site_domain = _extract_domain(site_url)
    competitor_domains = [_extract_domain(cu) for cu in competitor_urls]

    rows: list[dict] = []

    for keyword in keywords:
        search_results = await _search_yandex(keyword, config)

        your_position: int | None = None
        competitor_best_pos: int | None = None
        competitor_best_domain: str = ""

        for item in search_results:
            item_domain = _extract_domain(item["url"])

            # Check if this result belongs to our site
            if your_position is None:
                if site_domain in item_domain or item_domain in site_domain:
                    your_position = item["position"]

            # Check if this result belongs to a competitor
            for comp_domain in competitor_domains:
                if comp_domain in item_domain or item_domain in comp_domain:
                    if competitor_best_pos is None or item["position"] < competitor_best_pos:
                        competitor_best_pos = item["position"]
                        competitor_best_domain = comp_domain
                    break

        # Gap: competitor ranks but our site doesn't (or ranks beyond position 20)
        is_gap = (
            competitor_best_pos is not None
            and (your_position is None or your_position > 20)
        )

        if is_gap:
            rows.append(
                {
                    "keyword": keyword,
                    "your_position": str(your_position) if your_position else "не найден",
                    "competitor_best": str(competitor_best_pos),
                    "competitor": competitor_best_domain,
                }
            )

    if not rows:
        return "Контентных пробелов не обнаружено: по всем ключевым словам ваш сайт ранжируется лучше конкурентов."

    return format_tabular(rows)
