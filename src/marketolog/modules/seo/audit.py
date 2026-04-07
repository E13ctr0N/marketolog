"""SEO Audit — PageSpeed Insights + HTML analysis.

Combines Google PageSpeed Core Web Vitals with on-page HTML signals
(title, meta description, H1/H2, canonical, schema, robots meta) and
technical checks (robots.txt, sitemap).
"""

from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.http import fetch_with_retry

PAGESPEED_API = "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed"
CACHE_NS = "seo_audit"
CACHE_TTL = 3600  # 1 hour


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_seo_audit(
    url: str,
    *,
    config: MarketologConfig,
    cache: FileCache,
) -> str:
    """Run a full SEO audit for *url* and return a formatted report string.

    Steps:
    1. Cache hit → return immediately.
    2. Fetch PageSpeed Insights (mobile, performance category).
    3. Fetch page HTML.
    4. Fetch robots.txt; derive sitemap URL.
    5. Fetch sitemap.
    6. Parse HTML with BeautifulSoup.
    7. Assemble report.
    8. Store in cache (TTL 3600 s).
    """
    cached = cache.get(CACHE_NS, url)
    if cached is not None:
        return cached  # type: ignore[return-value]

    pagespeed_data = await _fetch_pagespeed(url, config=config)
    html_response = await fetch_with_retry(url)
    robots_text, sitemap_url = await _fetch_robots(url)
    sitemap_found = await _check_sitemap(sitemap_url)

    html_text = html_response.text if html_response.status_code == 200 else ""
    soup = BeautifulSoup(html_text, "lxml") if html_text else None

    report = _build_report(
        url=url,
        pagespeed=pagespeed_data,
        soup=soup,
        robots_text=robots_text,
        sitemap_url=sitemap_url,
        sitemap_found=sitemap_found,
    )

    cache.set(CACHE_NS, url, report, ttl_seconds=CACHE_TTL)
    return report


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _fetch_pagespeed(url: str, *, config: MarketologConfig) -> dict | None:
    """Call PageSpeed Insights API; return parsed JSON or None on failure."""
    params: dict[str, str] = {
        "url": url,
        "strategy": "mobile",
        "category": "performance",
    }
    if config.is_configured("pagespeed_api_key"):
        params["key"] = config.pagespeed_api_key  # type: ignore[assignment]

    response = await fetch_with_retry(PAGESPEED_API, params=params)
    if response.status_code == 200:
        try:
            return response.json()
        except Exception:
            return None
    return None


async def _fetch_robots(url: str) -> tuple[str | None, str]:
    """Fetch robots.txt; return (text_or_None, sitemap_url).

    Falls back to /sitemap.xml if no Sitemap: directive found.
    """
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{base}/robots.txt"

    response = await fetch_with_retry(robots_url)
    if response.status_code == 200:
        text = response.text
        sitemap = _extract_sitemap_from_robots(text) or f"{base}/sitemap.xml"
        return text, sitemap
    return None, f"{base}/sitemap.xml"


def _extract_sitemap_from_robots(robots_text: str) -> str | None:
    """Return first Sitemap: URL from robots.txt content."""
    for line in robots_text.splitlines():
        if line.strip().lower().startswith("sitemap:"):
            parts = line.split(":", 1)
            if len(parts) == 2:
                return parts[1].strip()
    return None


async def _check_sitemap(sitemap_url: str) -> bool:
    """Return True if sitemap responds with 2xx."""
    response = await fetch_with_retry(sitemap_url)
    return response.status_code < 300


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------


def _build_report(
    *,
    url: str,
    pagespeed: dict | None,
    soup: BeautifulSoup | None,
    robots_text: str | None,
    sitemap_url: str,
    sitemap_found: bool,
) -> str:
    parts: list[str] = [f"# SEO Audit: {url}\n"]

    parts.append(_section_core_web_vitals(pagespeed))
    parts.append(_section_meta_tags(soup))
    parts.append(_section_headings(soup))
    parts.append(_section_technical(soup, robots_text, sitemap_url, sitemap_found))

    return "\n".join(parts)


# ---- Core Web Vitals -------------------------------------------------------


def _section_core_web_vitals(pagespeed: dict | None) -> str:
    lines = ["## Core Web Vitals (PageSpeed Insights — mobile)\n"]

    if pagespeed is None:
        lines.append("- PageSpeed data unavailable (API error or network issue).")
        return "\n".join(lines)

    lr = pagespeed.get("lighthouseResult", {})
    perf_score = (
        lr.get("categories", {}).get("performance", {}).get("score")
    )
    if perf_score is not None:
        pct = round(perf_score * 100)
        rating = _perf_rating(pct)
        lines.append(f"- **Performance score:** {pct}/100 ({rating})")

    audits = lr.get("audits", {})
    metrics = [
        ("largest-contentful-paint", "LCP"),
        ("first-contentful-paint", "FCP"),
        ("total-blocking-time", "TBT"),
        ("cumulative-layout-shift", "CLS"),
        ("speed-index", "Speed Index"),
    ]
    for audit_key, label in metrics:
        value = audits.get(audit_key, {}).get("displayValue")
        if value:
            lines.append(f"- **{label}:** {value}")

    return "\n".join(lines)


def _perf_rating(score: int) -> str:
    if score >= 90:
        return "Good"
    if score >= 50:
        return "Needs Improvement"
    return "Poor"


# ---- Meta tags -------------------------------------------------------------


def _section_meta_tags(soup: BeautifulSoup | None) -> str:
    lines = ["\n## Meta Tags\n"]

    if soup is None:
        lines.append("- Page HTML unavailable.")
        return "\n".join(lines)

    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else None
    if title_text:
        lines.append(f"- **Title:** {title_text} ({len(title_text)} chars)")
    else:
        lines.append("- **Title:** MISSING")

    desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    desc_text = desc_tag.get("content", "").strip() if desc_tag else None  # type: ignore[union-attr]
    if desc_text:
        lines.append(f"- **Meta description:** {desc_text} ({len(desc_text)} chars)")
    else:
        lines.append("- **Meta description:** MISSING")

    robots_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    if robots_tag:
        robots_content = robots_tag.get("content", "").strip()  # type: ignore[union-attr]
        lines.append(f"- **Meta robots:** {robots_content}")

    return "\n".join(lines)


# ---- Headings --------------------------------------------------------------


def _section_headings(soup: BeautifulSoup | None) -> str:
    lines = ["\n## Headings\n"]

    if soup is None:
        lines.append("- Page HTML unavailable.")
        return "\n".join(lines)

    h1_tags = soup.find_all("h1")
    if h1_tags:
        for tag in h1_tags:
            lines.append(f"- **H1:** {tag.get_text(strip=True)}")
    else:
        lines.append("- **H1:** MISSING")

    h2_tags = soup.find_all("h2")
    if h2_tags:
        for tag in h2_tags:
            lines.append(f"- **H2:** {tag.get_text(strip=True)}")
    else:
        lines.append("- **H2:** none found")

    return "\n".join(lines)


# ---- Technical -------------------------------------------------------------


def _section_technical(
    soup: BeautifulSoup | None,
    robots_text: str | None,
    sitemap_url: str,
    sitemap_found: bool,
) -> str:
    lines = ["\n## Technical SEO\n"]

    # Canonical
    if soup is not None:
        canonical = soup.find("link", rel="canonical")
        if canonical:
            href = canonical.get("href", "")
            lines.append(f"- **Canonical:** {href}")
        else:
            lines.append("- **Canonical:** not set")

        # JSON-LD schema
        schema_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
        if schema_tags:
            types = []
            for tag in schema_tags:
                try:
                    data = json.loads(tag.string or "")
                    schema_type = data.get("@type", "unknown")
                    types.append(schema_type)
                except (json.JSONDecodeError, AttributeError):
                    types.append("invalid JSON-LD")
            lines.append(f"- **JSON-LD schema:** {', '.join(types)}")
        else:
            lines.append("- **JSON-LD schema:** none found")

        # Images without alt
        all_imgs = soup.find_all("img")
        no_alt_imgs = [
            img for img in all_imgs
            if not img.get("alt", "").strip()
        ]
        lines.append(
            f"- **Images without alt:** {len(no_alt_imgs)} of {len(all_imgs)}"
        )

    # robots.txt
    if robots_text is not None:
        lines.append("- **robots.txt:** found")
    else:
        lines.append("- **robots.txt:** not found (404)")

    # Sitemap
    status = "found" if sitemap_found else "not found (404)"
    lines.append(f"- **Sitemap ({sitemap_url}):** {status}")

    return "\n".join(lines)
