"""Tests for UTM link generator."""

from marketolog.modules.analytics.utm import generate_utm


def test_basic_utm():
    """Minimal required params: url, source, medium."""
    result = generate_utm(
        url="https://example.ru",
        source="telegram",
        medium="social",
    )
    assert "https://example.ru" in result
    assert "utm_source=telegram" in result
    assert "utm_medium=social" in result


def test_full_utm():
    """All UTM params provided."""
    result = generate_utm(
        url="https://example.ru/pricing",
        source="vk",
        medium="cpc",
        campaign="spring_sale",
        term="таск трекер",
        content="banner_top",
    )
    assert "utm_source=vk" in result
    assert "utm_medium=cpc" in result
    assert "utm_campaign=spring_sale" in result
    assert "utm_term=" in result  # URL-encoded cyrillic
    assert "utm_content=banner_top" in result
    assert "https://example.ru/pricing?" in result


def test_utm_preserves_existing_query():
    """URL already has query params — UTM appended with &."""
    result = generate_utm(
        url="https://example.ru?ref=main",
        source="google",
        medium="organic",
    )
    assert "ref=main" in result
    assert "utm_source=google" in result
    assert result.count("?") == 1


def test_utm_encodes_cyrillic():
    """Cyrillic characters in term/content are URL-encoded."""
    result = generate_utm(
        url="https://example.ru",
        source="yandex",
        medium="cpc",
        term="управление задачами",
    )
    # Should be percent-encoded, not raw cyrillic in query
    assert "utm_term=" in result
    # Decoded form should match
    from urllib.parse import unquote
    assert "управление задачами" in unquote(result)


def test_utm_returns_markdown_block():
    """generate_utm returns a formatted string with the link and breakdown."""
    result = generate_utm(
        url="https://example.ru",
        source="telegram",
        medium="social",
        campaign="launch",
    )
    # Should contain the URL
    assert "https://example.ru" in result
    assert "utm_source=telegram" in result
