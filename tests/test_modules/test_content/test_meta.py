"""Tests for meta generation tool."""
import pytest
from marketolog.modules.content.meta import run_generate_meta


def test_generate_meta_from_text():
    text = """
    Как выбрать таск-трекер для команды в 2026 году.
    Рассмотрим ключевые критерии: удобство, интеграции, стоимость.
    Лучшие решения для малых команд.
    """
    result = run_generate_meta(text=text, keywords=["таск-трекер", "управление задачами"])
    assert isinstance(result, str)
    assert "title" in result.lower() or "Title" in result
    assert "description" in result.lower() or "Description" in result
    assert "H1" in result


def test_generate_meta_with_keywords():
    result = run_generate_meta(
        text="Статья о продуктивности и управлении проектами.",
        keywords=["продуктивность", "управление проектами"],
    )
    assert "продуктивность" in result or "управление проектами" in result


def test_generate_meta_empty_keywords():
    result = run_generate_meta(text="Обзор лучших инструментов для работы.")
    assert isinstance(result, str)
    assert "title" in result.lower() or "Title" in result
