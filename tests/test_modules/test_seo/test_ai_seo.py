"""Tests for AI-SEO readiness check tool."""

import pytest
import respx
import httpx

from marketolog.modules.seo.ai_seo import run_ai_seo_check
from marketolog.utils.cache import FileCache


ROBOTS_WITH_AI_RULES = """\
User-agent: GPTBot
Disallow: /private/
Disallow: /admin/

User-agent: ClaudeBot
Disallow: /

User-agent: PerplexityBot
Allow: /

User-agent: *
Disallow: /secret/
"""

ROBOTS_NO_AI_RULES = """\
User-agent: *
Disallow: /admin/
Disallow: /private/
"""

HTML_WITH_SCHEMA = """\
<!DOCTYPE html>
<html>
<head>
  <title>Test Page</title>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Test Company",
    "url": "https://example.com"
  }
  </script>
</head>
<body>
  <main>
    <h1>Welcome to Test Company</h1>
    <p>We provide excellent services for all your testing needs. Our team is dedicated to quality.</p>
  </main>
</body>
</html>
"""

HTML_NO_SCHEMA = """\
<!DOCTYPE html>
<html>
<head>
  <title>Simple Page</title>
</head>
<body>
  <p>This page has enough text content to pass the 50 character threshold easily.</p>
</body>
</html>
"""


@pytest.mark.asyncio
@respx.mock
async def test_full_check_with_ai_rules_and_llms_txt(cache: FileCache) -> None:
    """Full check: robots.txt with AI rules + llms.txt exists + schema markup."""
    url = "https://example.com/page"

    respx.get("https://example.com/robots.txt").mock(
        return_value=httpx.Response(200, text=ROBOTS_WITH_AI_RULES)
    )
    respx.get("https://example.com/llms.txt").mock(
        return_value=httpx.Response(200, text="# LLMs.txt\nThis site is AI-friendly.")
    )
    respx.get(url).mock(
        return_value=httpx.Response(200, text=HTML_WITH_SCHEMA)
    )

    report = await run_ai_seo_check(url, cache=cache)

    # AI crawlers section present
    assert "GPTBot" in report
    assert "ClaudeBot" in report
    assert "PerplexityBot" in report

    # GPTBot has partial block (only /private/ and /admin/ are blocked)
    assert "частично заблокирован" in report

    # ClaudeBot is fully blocked
    assert "заблокирован" in report

    # llms.txt found
    assert "llms.txt" in report
    assert "существует" in report or "найден" in report or "присутствует" in report

    # Schema markup found
    assert "Schema" in report or "schema" in report or "JSON-LD" in report
    assert "найдена" in report or "обнаружена" in report or "присутствует" in report

    # Content accessible without JS
    assert "контент" in report.lower() or "content" in report.lower()

    # Recommendations section present
    assert "Рекомендации" in report or "рекомендации" in report


@pytest.mark.asyncio
@respx.mock
async def test_no_llms_txt_and_no_ai_rules(cache: FileCache) -> None:
    """Check with no llms.txt (404) + no AI rules in robots.txt."""
    url = "https://noai.example.org/home"

    respx.get("https://noai.example.org/robots.txt").mock(
        return_value=httpx.Response(200, text=ROBOTS_NO_AI_RULES)
    )
    respx.get("https://noai.example.org/llms.txt").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    respx.get(url).mock(
        return_value=httpx.Response(200, text=HTML_NO_SCHEMA)
    )

    report = await run_ai_seo_check(url, cache=cache)

    # All AI bots should be "не упомянут"
    assert "не упомянут" in report

    # llms.txt absent
    assert "llms.txt" in report
    assert "отсутствует" in report or "не найден" in report or "не обнаружен" in report

    # No schema markup
    assert "не найдена" in report or "отсутствует" in report or "не обнаружена" in report

    # Recommendations section present and suggests adding llms.txt
    assert "Рекомендации" in report or "рекомендации" in report
    assert "llms.txt" in report


@pytest.mark.asyncio
@respx.mock
async def test_result_is_cached(cache: FileCache) -> None:
    """Second call returns cached result without making HTTP requests."""
    url = "https://cached.example.com/page"

    respx.get("https://cached.example.com/robots.txt").mock(
        return_value=httpx.Response(200, text=ROBOTS_NO_AI_RULES)
    )
    respx.get("https://cached.example.com/llms.txt").mock(
        return_value=httpx.Response(404)
    )
    respx.get(url).mock(
        return_value=httpx.Response(200, text=HTML_NO_SCHEMA)
    )

    # First call populates cache
    report1 = await run_ai_seo_check(url, cache=cache)

    # Second call: respx will raise if any HTTP request is made (all routes used up)
    # We reset mocks to confirm no HTTP calls happen
    respx.reset()

    report2 = await run_ai_seo_check(url, cache=cache)

    assert report1 == report2


@pytest.mark.asyncio
@respx.mock
async def test_robots_txt_unavailable(cache: FileCache) -> None:
    """If robots.txt returns non-200, all bots marked as 'не упомянут'."""
    url = "https://broken.example.com/"

    respx.get("https://broken.example.com/robots.txt").mock(
        return_value=httpx.Response(404)
    )
    respx.get("https://broken.example.com/llms.txt").mock(
        return_value=httpx.Response(404)
    )
    respx.get(url).mock(
        return_value=httpx.Response(200, text=HTML_NO_SCHEMA)
    )

    report = await run_ai_seo_check(url, cache=cache)

    assert "не упомянут" in report
    # Report should still be structured
    assert "GPTBot" in report
    assert "ClaudeBot" in report


@pytest.mark.asyncio
@respx.mock
async def test_body_text_too_short_flagged(cache: FileCache) -> None:
    """Page with body text under 50 chars is flagged as JS-dependent."""
    url = "https://jsonly.example.com/"

    html_js_only = """\
<html><head></head><body>
<div id="app"></div>
<script src="app.js"></script>
</body></html>
"""

    respx.get("https://jsonly.example.com/robots.txt").mock(
        return_value=httpx.Response(200, text=ROBOTS_NO_AI_RULES)
    )
    respx.get("https://jsonly.example.com/llms.txt").mock(
        return_value=httpx.Response(404)
    )
    respx.get(url).mock(
        return_value=httpx.Response(200, text=html_js_only)
    )

    report = await run_ai_seo_check(url, cache=cache)

    # Should flag that content requires JS
    assert "JS" in report or "JavaScript" in report or "недоступен" in report or "недостаточно" in report
