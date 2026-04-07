"""Tests for keyword_research and keyword_cluster tools."""

import pytest
import respx
import httpx

from marketolog.modules.seo.keywords import run_keyword_research, run_keyword_cluster
from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache


WORDSTAT_URL = "https://api.wordstat.yandex.net/v1/topRequests"


@pytest.mark.asyncio
async def test_keyword_research(config_with_keys: MarketologConfig, cache: FileCache):
    """Mock Wordstat API → verify CSV output contains keyword + count."""
    seed = ["python"]
    mock_result = [
        {"text": "python курс", "count": 5000},
        {"text": "python онлайн", "count": 3000},
    ]

    with respx.mock:
        respx.post(WORDSTAT_URL).mock(
            return_value=httpx.Response(200, json={"result": mock_result})
        )
        result = await run_keyword_research(seed, config=config_with_keys, cache=cache)

    assert "python курс" in result
    assert "5000" in result
    assert "python онлайн" in result
    assert "3000" in result


@pytest.mark.asyncio
async def test_keyword_research_no_token(config_no_keys: MarketologConfig, cache: FileCache):
    """No token → returns message mentioning YANDEX_WORDSTAT_TOKEN."""
    result = await run_keyword_research(["python"], config=config_no_keys, cache=cache)
    assert "YANDEX_WORDSTAT_TOKEN" in result


@pytest.mark.asyncio
async def test_keyword_research_cached(config_with_keys: MarketologConfig, cache: FileCache):
    """Pre-filled cache → no HTTP calls made."""
    cached_data = [
        {"text": "cached keyword", "count": 9999},
    ]
    cache.set("wordstat", "python", cached_data, ttl_seconds=86400)

    with respx.mock:
        # If any HTTP call is made, respx will raise an error (no routes registered)
        result = await run_keyword_research(["python"], config=config_with_keys, cache=cache)

    assert "cached keyword" in result
    assert "9999" in result


def test_keyword_cluster_basic():
    """5 keywords → clusters with name, keywords, total_volume."""
    keywords = [
        {"text": "купить ноутбук недорого", "count": 1000},
        {"text": "купить ноутбук онлайн", "count": 800},
        {"text": "купить телефон недорого", "count": 600},
        {"text": "аренда автомобиля", "count": 400},
        {"text": "аренда авто москва", "count": 300},
    ]

    clusters = run_keyword_cluster(keywords)

    assert isinstance(clusters, list)
    assert len(clusters) > 0

    for cluster in clusters:
        assert "name" in cluster
        assert "keywords" in cluster
        assert "total_volume" in cluster
        assert isinstance(cluster["keywords"], list)
        assert isinstance(cluster["total_volume"], int)

    # Verify that keywords sharing common words land in same cluster
    all_cluster_keywords = {kw["text"] for c in clusters for kw in c["keywords"]}
    assert all_cluster_keywords == {kw["text"] for kw in keywords}

    # "купить" should group at least two keywords together
    buy_cluster = next(
        (c for c in clusters if any("купить" in kw["text"] for kw in c["keywords"])),
        None,
    )
    assert buy_cluster is not None
    assert len(buy_cluster["keywords"]) >= 2
