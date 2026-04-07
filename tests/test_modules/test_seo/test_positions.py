"""Tests for SEO positions module.

TDD: write tests first, then implement.
"""

import httpx
import pytest
import respx

from marketolog.modules.seo.positions import run_check_positions

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

YANDEX_SEARCH_URL = "https://yandex.ru/search/xml"

SITE_URL = "https://example.ru"
KEYWORDS = ["таск трекер", "управление задачами"]


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
# Test 1: site found at position 3
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_check_positions(config_with_keys, cache):
    """Site found at position 3 — output must contain '3'."""
    xml_response = _make_xml(
        [
            ("https://other1.ru/", "Other Site 1"),
            ("https://other2.ru/", "Other Site 2"),
            ("https://example.ru/some-page", "Example Page"),
            ("https://other3.ru/", "Other Site 3"),
        ]
    )

    respx.get(YANDEX_SEARCH_URL).mock(
        return_value=httpx.Response(200, text=xml_response)
    )

    result = await run_check_positions(
        ["таск трекер"],
        SITE_URL,
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert len(result) > 0
    # Position 3 must appear in the output
    assert "3" in result
    # Keyword must appear
    assert "таск трекер" in result


# ---------------------------------------------------------------------------
# Test 2: site not found in results
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_check_positions_not_found(config_with_keys, cache):
    """Site not in results — output must indicate not found."""
    xml_response = _make_xml(
        [
            ("https://competitor1.ru/", "Competitor 1"),
            ("https://competitor2.ru/", "Competitor 2"),
        ]
    )

    respx.get(YANDEX_SEARCH_URL).mock(
        return_value=httpx.Response(200, text=xml_response)
    )

    result = await run_check_positions(
        ["управление задачами"],
        SITE_URL,
        config=config_with_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    # Must indicate not found — either "не найден" or ">50"
    assert "не найден" in result or ">50" in result


# ---------------------------------------------------------------------------
# Test 3: no API key configured
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_check_positions_no_api_key(config_no_keys, cache):
    """When API key is not configured, return setup instructions."""
    result = await run_check_positions(
        KEYWORDS,
        SITE_URL,
        config=config_no_keys,
        cache=cache,
    )

    assert isinstance(result, str)
    assert "YANDEX_SEARCH_API_KEY" in result
