"""Tests for text optimizer tool."""
import pytest
from marketolog.modules.content.optimizer import run_optimize_text

SAMPLE_TEXT = """# Как выбрать таск-трекер для команды

Таск-трекер — инструмент для управления задачами. Выбор правильного таск-трекера важен для продуктивности.

## Критерии выбора

При выборе таск-трекера обратите внимание на:
- Удобство интерфейса
- Интеграции
- Стоимость

## Топ-5 решений

Рассмотрим лучшие таск-трекеры для малых команд.

Каждый из них имеет свои преимущества в управлении задачами.
"""


def test_optimize_text_basic():
    result = run_optimize_text(text=SAMPLE_TEXT, target_keywords=["таск-трекер", "управление задачами"])
    assert isinstance(result, str)
    assert "плотность" in result.lower() or "density" in result.lower() or "%" in result
    assert "таск-трекер" in result


def test_optimize_text_structure_analysis():
    result = run_optimize_text(text=SAMPLE_TEXT, target_keywords=["таск-трекер"])
    assert "H1" in result or "заголов" in result.lower()
    assert "H2" in result


def test_optimize_text_short():
    result = run_optimize_text(text="Короткий текст.", target_keywords=["ключ"])
    assert isinstance(result, str)
    assert "корот" in result.lower() or "длин" in result.lower() or "слов" in result.lower()


def test_optimize_text_readability():
    result = run_optimize_text(text=SAMPLE_TEXT, target_keywords=["таск-трекер"])
    assert "предложен" in result.lower() or "читаем" in result.lower() or "слов" in result.lower()
