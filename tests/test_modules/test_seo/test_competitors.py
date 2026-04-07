"""Tests for SEO competitors module.

TDD: write tests first, then implement.
"""

import httpx
import pytest
import respx

from marketolog.modules.seo.competitors import run_analyze_competitors, run_content_gap

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

YANDEX_SEARCH_URL = "https://yandex.ru/search/xml"

COMPETITOR_URL = "https://trello.com/pricing"
SITE_URL = "https://example.ru"
KEYWORDS = ["таск трекер", "управление задачами"]

SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Trello | Manage Your Team's Projects From Anywhere</title>
  <meta name="description" content="Trello is the visual collaboration platform that gives teams perspective on projects.">
  <script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite","name":"Trello"}</script>
</head>
<body>
  <h1>Simple pricing for teams of all sizes</h1>
  <h2>Free plan</h2>
  <h2>Standard plan</h2>
  <h2>Premium plan</h2>
  <p>Trello helps teams work more collaboratively and get more done.</p>
  <p>Organize anything, together. Trello is a collaboration tool that organizes your projects into boards.</p>
</body>
</html>"""


def _make_xml(urls_with_titles: list[tuple[str, str]]) -> str:
    """Build a minimal Yandex Search XML response."""
    groups = "\n".join(
        f"<group><doc><url>{url}</url><title>{title}</title></doc></group>"
        for url, title in urls_with_titles
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<yandexsearch version="1.0">\n'
        "<response><results><grouping>\n"
        f"{groups}\n"
        "</grouping></results></response>\n"
        "</yandexsearch>"
    )


# ---------------------------------------------------------------------------
# Test 1: analyze_competitors
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_analyze_competitors(config_with_keys, cache):
    """Mock competitor HTML page — report must contain title and heading info."""
    respx.get(COMPETITOR_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_HTML)
    )

    result = await run_analyze_competitors(
        [COMPETITOR_URL],
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert len(result) > 0

    # Title must be in the report
    assert "Trello" in result

    # H1 content must appear
    assert "Simple pricing" in result

    # H2 count should be reflected (3 H2s)
    assert "3" in result

    # URL must appear
    assert "trello.com" in result


# ---------------------------------------------------------------------------
# Test 2: content_gap
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_content_gap(config_with_keys, cache):
    """Mock Yandex search — CSV output must contain gap keyword."""
    # "таск трекер": competitor ranks at 1, our site absent
    # "управление задачами": our site ranks at 2, competitor at 1
    xml_kw1 = _make_xml(
        [
            ("https://trello.com/", "Trello"),
            ("https://other.ru/", "Other"),
        ]
    )
    xml_kw2 = _make_xml(
        [
            ("https://trello.com/features", "Trello Features"),
            ("https://example.ru/page", "Example Page"),
        ]
    )

    # respx matches GET requests; Yandex API always goes to same URL with params
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(200, text=xml_kw1)
        return httpx.Response(200, text=xml_kw2)

    respx.get(YANDEX_SEARCH_URL).mock(side_effect=side_effect)

    result = await run_content_gap(
        SITE_URL,
        ["https://trello.com"],
        KEYWORDS,
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert len(result) > 0

    # "таск трекер" should appear as a gap (competitor ranks, site absent)
    assert "таск трекер" in result

    # CSV header must contain expected columns
    assert "keyword" in result
    assert "competitor" in result or "competitor_best" in result


# ---------------------------------------------------------------------------
# Test 3: content_gap with no API key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_content_gap_no_api_key(config_no_keys, cache):
    """When API key is not configured, return setup instructions."""
    result = await run_content_gap(
        SITE_URL,
        ["https://trello.com"],
        KEYWORDS,
        config=config_no_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "YANDEX_SEARCH_API_KEY" in result
