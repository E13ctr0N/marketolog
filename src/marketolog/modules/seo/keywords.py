"""Keyword research and clustering tools using Yandex Wordstat API."""

from collections import defaultdict
from typing import Any

from marketolog.core.config import MarketologConfig
from marketolog.utils.cache import FileCache
from marketolog.utils.formatting import format_tabular
from marketolog.utils.http import fetch_with_retry

WORDSTAT_API_URL = "https://api.wordstat.yandex.net/v1/topRequests"
CACHE_NAMESPACE = "wordstat"
CACHE_TTL = 86400  # 24 hours


async def run_keyword_research(
    seed_keywords: list[str],
    *,
    config: MarketologConfig,
    cache: FileCache,
    count: int = 50,
) -> str:
    """Fetch keyword suggestions from Yandex Wordstat for each seed keyword.

    Returns a CSV string with deduplicated results sorted by count descending,
    limited to `count` entries.
    """
    if not config.is_configured("yandex_wordstat_token"):
        return (
            "Для использования инструмента укажите токен Яндекс Вордстат.\n"
            "Установите переменную окружения: YANDEX_WORDSTAT_TOKEN=<ваш_токен>\n"
            "или добавьте yandex_wordstat_token в ~/.marketolog/config.yaml"
        )

    token: str = config.yandex_wordstat_token  # type: ignore[assignment]
    headers = {"Authorization": f"Bearer {token}"}

    # Gather all results, deduplicate by text
    seen: dict[str, int] = {}

    for keyword in seed_keywords:
        cached = cache.get(CACHE_NAMESPACE, keyword)
        if cached is not None:
            items: list[dict[str, Any]] = cached
        else:
            response = await fetch_with_retry(
                WORDSTAT_API_URL,
                method="POST",
                headers=headers,
                json={"text": keyword, "top": 50},
            )
            response.raise_for_status()
            data = response.json()
            items = data.get("result", [])
            cache.set(CACHE_NAMESPACE, keyword, items, ttl_seconds=CACHE_TTL)

        for item in items:
            text = item["text"]
            count_val = int(item["count"])
            # Keep the higher count if duplicate
            if text not in seen or count_val > seen[text]:
                seen[text] = count_val

    # Sort by count descending, limit
    sorted_results = sorted(
        [{"text": t, "count": c} for t, c in seen.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:count]

    return format_tabular(sorted_results)


def run_keyword_cluster(keywords: list[dict]) -> list[dict]:
    """Group keywords by shared common words (longer than 2 chars).

    Returns a list of clusters, each with:
      - name: the anchor keyword (highest count in cluster)
      - keywords: list of keyword dicts in this cluster
      - total_volume: sum of counts
    """
    # Build a mapping: keyword index → set of significant words
    def significant_words(text: str) -> set[str]:
        return {w for w in text.lower().split() if len(w) > 2}

    n = len(keywords)
    # Union-Find for grouping
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        pi, pj = find(i), find(j)
        if pi != pj:
            parent[pi] = pj

    word_sets = [significant_words(kw["text"]) for kw in keywords]

    for i in range(n):
        for j in range(i + 1, n):
            if word_sets[i] & word_sets[j]:
                union(i, j)

    # Collect groups
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)

    clusters = []
    for indices in groups.values():
        group_keywords = [keywords[i] for i in indices]
        # Anchor = keyword with highest count
        anchor = max(group_keywords, key=lambda kw: kw["count"])
        total_volume = sum(kw["count"] for kw in group_keywords)
        clusters.append(
            {
                "name": anchor["text"],
                "keywords": group_keywords,
                "total_volume": total_volume,
            }
        )

    # Sort clusters by total_volume descending
    clusters.sort(key=lambda c: c["total_volume"], reverse=True)
    return clusters
