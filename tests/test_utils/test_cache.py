import json
import time
from pathlib import Path

import pytest

from marketolog.utils.cache import FileCache


@pytest.fixture
def cache(tmp_path: Path) -> FileCache:
    return FileCache(base_dir=tmp_path / "cache")


def test_cache_set_and_get(cache: FileCache):
    cache.set("seo", "audit_example.ru", {"score": 85}, ttl_seconds=3600)
    result = cache.get("seo", "audit_example.ru")
    assert result == {"score": 85}


def test_cache_miss(cache: FileCache):
    result = cache.get("seo", "nonexistent")
    assert result is None


def test_cache_expired(cache: FileCache):
    cache.set("seo", "audit_example.ru", {"score": 85}, ttl_seconds=0)
    time.sleep(0.05)
    result = cache.get("seo", "audit_example.ru")
    assert result is None


def test_cache_different_namespaces(cache: FileCache):
    cache.set("seo", "key1", {"a": 1}, ttl_seconds=3600)
    cache.set("metrika", "key1", {"b": 2}, ttl_seconds=3600)
    assert cache.get("seo", "key1") == {"a": 1}
    assert cache.get("metrika", "key1") == {"b": 2}


def test_cache_overwrite(cache: FileCache):
    cache.set("seo", "key1", {"old": True}, ttl_seconds=3600)
    cache.set("seo", "key1", {"new": True}, ttl_seconds=3600)
    assert cache.get("seo", "key1") == {"new": True}


def test_cache_clear_namespace(cache: FileCache):
    cache.set("seo", "key1", {"a": 1}, ttl_seconds=3600)
    cache.set("seo", "key2", {"b": 2}, ttl_seconds=3600)
    cache.set("metrika", "key1", {"c": 3}, ttl_seconds=3600)
    cache.clear("seo")
    assert cache.get("seo", "key1") is None
    assert cache.get("seo", "key2") is None
    assert cache.get("metrika", "key1") == {"c": 3}


def test_cache_creates_dirs(tmp_path: Path):
    cache = FileCache(base_dir=tmp_path / "deep" / "nested" / "cache")
    cache.set("ns", "key", {"x": 1}, ttl_seconds=3600)
    assert cache.get("ns", "key") == {"x": 1}
