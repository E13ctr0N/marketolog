"""Tests for content analyzer tool."""
import httpx
import pytest
import respx
from marketolog.modules.content.analyzer import run_analyze_content

SAMPLE_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
  <title>Как выбрать таск-трекер — Руководство 2026</title>
  <meta name="description" content="Полное руководство по выбору таск-трекера для команды.">
</head>
<body>
  <h1>Как выбрать таск-трекер для команды</h1>
  <p>Выбор правильного таск-трекера — важный шаг для продуктивности. Рассмотрим ключевые критерии.</p>
  <h2>Критерии выбора</h2>
  <p>При выборе обратите внимание на удобство интерфейса, интеграции и стоимость.</p>
  <h2>Топ решений</h2>
  <p>Лучшие таск-трекеры для малых команд включают множество решений на рынке.</p>
  <img src="img1.jpg" alt="Сравнение трекеров">
  <img src="img2.jpg">
</body>
</html>"""


@respx.mock
@pytest.mark.asyncio
async def test_analyze_content(cache):
    respx.get("https://example.ru/blog/article").mock(
        return_value=httpx.Response(200, text=SAMPLE_PAGE)
    )
    report = await run_analyze_content(url="https://example.ru/blog/article", cache=cache)
    assert isinstance(report, str)
    assert "таск-трекер" in report.lower() or "title" in report.lower()
    assert "H1" in report or "заголов" in report.lower()
    assert "H2" in report


@respx.mock
@pytest.mark.asyncio
async def test_analyze_content_cached(cache):
    cache.set("content_analysis", "https://example.ru/page", "cached analysis", ttl_seconds=3600)
    report = await run_analyze_content(url="https://example.ru/page", cache=cache)
    assert report == "cached analysis"
    assert len(respx.calls) == 0


@respx.mock
@pytest.mark.asyncio
async def test_analyze_content_error(cache):
    respx.get("https://example.ru/404").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    report = await run_analyze_content(url="https://example.ru/404", cache=cache)
    assert isinstance(report, str)
    assert "404" in report or "ошибк" in report.lower()
