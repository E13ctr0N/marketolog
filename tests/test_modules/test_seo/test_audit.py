"""Tests for SEO audit module.

TDD: write tests first, then implement.
"""

import json

import httpx
import pytest
import respx

from marketolog.modules.seo.audit import run_seo_audit

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

AUDIT_URL = "https://example.com"
PAGESPEED_API_URL = "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed"
ROBOTS_URL = "https://example.com/robots.txt"
SITEMAP_URL = "https://example.com/sitemap.xml"

SAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Example Domain — Test Page</title>
  <meta name="description" content="This is a test meta description for SEO audit.">
  <link rel="canonical" href="https://example.com/">
  <meta name="robots" content="index, follow">
  <script type="application/ld+json">
  {"@context": "https://schema.org", "@type": "WebSite", "name": "Example"}
  </script>
</head>
<body>
  <h1>Main Heading</h1>
  <h2>Sub Heading One</h2>
  <h2>Sub Heading Two</h2>
  <img src="with-alt.jpg" alt="Image with alt">
  <img src="no-alt.jpg">
</body>
</html>"""

SAMPLE_ROBOTS = """User-agent: *
Disallow: /private/
Sitemap: https://example.com/sitemap.xml
"""

SAMPLE_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
</urlset>"""

SAMPLE_PAGESPEED = {
    "lighthouseResult": {
        "categories": {
            "performance": {"score": 0.87}
        },
        "audits": {
            "largest-contentful-paint": {"displayValue": "1.2 s"},
            "total-blocking-time": {"displayValue": "50 ms"},
            "cumulative-layout-shift": {"displayValue": "0.05"},
            "first-contentful-paint": {"displayValue": "0.8 s"},
            "speed-index": {"displayValue": "1.5 s"},
        },
    }
}


# ---------------------------------------------------------------------------
# Test: full audit — PageSpeed + HTML + robots.txt
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_full_audit(config_with_keys, cache):
    """Full audit with all external calls mocked."""
    # Mock PageSpeed API
    respx.get(PAGESPEED_API_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGESPEED)
    )
    # Mock page HTML
    respx.get(AUDIT_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_HTML, headers={"Content-Type": "text/html"})
    )
    # Mock robots.txt
    respx.get(ROBOTS_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_ROBOTS)
    )
    # Mock sitemap
    respx.get(SITEMAP_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_SITEMAP)
    )

    report = await run_seo_audit(AUDIT_URL, config=config_with_keys, cache=cache)

    assert isinstance(report, str)
    assert len(report) > 0

    # Core Web Vitals section
    assert "Core Web Vitals" in report or "Performance" in report
    assert "87" in report  # performance score 0.87 → 87%

    # Meta tags section
    assert "Example Domain" in report  # title
    assert "test meta description" in report  # meta description

    # Headings section
    assert "Main Heading" in report  # H1
    assert "Sub Heading" in report   # H2

    # Technical section — canonical
    assert "https://example.com/" in report

    # Technical — robots.txt found
    assert "robots" in report.lower()

    # Technical — sitemap found
    assert "sitemap" in report.lower()

    # Images without alt
    assert "no-alt" in report or "1" in report  # 1 image without alt


@respx.mock
@pytest.mark.asyncio
async def test_full_audit_result_is_cached(config_with_keys, cache):
    """After a full audit the result is stored in cache."""
    respx.get(PAGESPEED_API_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGESPEED)
    )
    respx.get(AUDIT_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_HTML, headers={"Content-Type": "text/html"})
    )
    respx.get(ROBOTS_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_ROBOTS)
    )
    respx.get(SITEMAP_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_SITEMAP)
    )

    report = await run_seo_audit(AUDIT_URL, config=config_with_keys, cache=cache)

    cached = cache.get("seo_audit", AUDIT_URL)
    assert cached is not None
    assert cached == report


# ---------------------------------------------------------------------------
# Test: audit without PageSpeed API key — should still work (keyless allowed)
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_audit_no_api_key(config_no_keys, cache):
    """Audit works even without a PageSpeed API key."""
    respx.get(PAGESPEED_API_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGESPEED)
    )
    respx.get(AUDIT_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_HTML, headers={"Content-Type": "text/html"})
    )
    respx.get(ROBOTS_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_ROBOTS)
    )
    respx.get(SITEMAP_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_SITEMAP)
    )

    report = await run_seo_audit(AUDIT_URL, config=config_no_keys, cache=cache)

    assert isinstance(report, str)
    assert len(report) > 0
    # Should still have Core Web Vitals data
    assert "87" in report

    # Verify PageSpeed was called WITHOUT a key param
    pagespeed_request = respx.calls[0].request
    assert "key" not in str(pagespeed_request.url)


# ---------------------------------------------------------------------------
# Test: cached result — no HTTP calls made
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_cached_result_no_http(config_with_keys, cache):
    """Pre-filled cache must be returned without any HTTP requests."""
    cached_report = "## SEO Audit (cached)\n\nThis is a cached result."
    cache.set("seo_audit", AUDIT_URL, cached_report, ttl_seconds=3600)

    report = await run_seo_audit(AUDIT_URL, config=config_with_keys, cache=cache)

    assert report == cached_report
    # respx.mock with no routes: any HTTP call would raise
    assert len(respx.calls) == 0


# ---------------------------------------------------------------------------
# Test: graceful degradation when PageSpeed returns non-200
# ---------------------------------------------------------------------------

@respx.mock
@pytest.mark.asyncio
async def test_audit_pagespeed_error(config_with_keys, cache):
    """If PageSpeed API fails, audit still runs using HTML data."""
    respx.get(PAGESPEED_API_URL).mock(
        return_value=httpx.Response(403, json={"error": {"message": "API key invalid"}})
    )
    respx.get(AUDIT_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_HTML, headers={"Content-Type": "text/html"})
    )
    respx.get(ROBOTS_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_ROBOTS)
    )
    respx.get(SITEMAP_URL).mock(
        return_value=httpx.Response(200, text=SAMPLE_SITEMAP)
    )

    report = await run_seo_audit(AUDIT_URL, config=config_with_keys, cache=cache)

    assert isinstance(report, str)
    # HTML data should still be there
    assert "Example Domain" in report
    assert "Main Heading" in report


# ---------------------------------------------------------------------------
# Test: no meta description / no H1 — warnings appear in report
# ---------------------------------------------------------------------------

SPARSE_HTML = """<!DOCTYPE html>
<html>
<head><title>Sparse Page</title></head>
<body>
  <h2>Only a subheading</h2>
  <img src="a.jpg">
  <img src="b.jpg">
</body>
</html>"""


@respx.mock
@pytest.mark.asyncio
async def test_audit_sparse_html_warnings(config_with_keys, cache):
    """Report surfaces missing meta description, missing H1, images without alt."""
    respx.get(PAGESPEED_API_URL).mock(
        return_value=httpx.Response(200, json=SAMPLE_PAGESPEED)
    )
    respx.get(AUDIT_URL).mock(
        return_value=httpx.Response(200, text=SPARSE_HTML, headers={"Content-Type": "text/html"})
    )
    respx.get(ROBOTS_URL).mock(
        return_value=httpx.Response(404, text="Not found")
    )
    respx.get(SITEMAP_URL).mock(
        return_value=httpx.Response(404, text="Not found")
    )

    report = await run_seo_audit(AUDIT_URL, config=config_with_keys, cache=cache)

    lower = report.lower()
    # Missing meta description warning
    assert "description" in lower
    # Missing H1 warning
    assert "h1" in lower
    # Images without alt — 2 images
    assert "2" in report
