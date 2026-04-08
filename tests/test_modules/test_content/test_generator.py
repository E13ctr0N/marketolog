"""Tests for content generation tools (context assembly)."""
import pytest
from marketolog.modules.content.generator import (
    run_generate_article, run_generate_post, run_repurpose_content,
)


def test_generate_article(project_context):
    result = run_generate_article(
        topic="Как выбрать таск-трекер для команды",
        project_context=project_context,
        keywords=["таск трекер", "управление задачами"],
        length="medium",
    )
    assert isinstance(result, str)
    assert "таск-трекер" in result.lower() or "таск трекер" in result.lower()
    assert "дружелюбный" in result or "tone" in result.lower()
    assert "H1" in result or "заголов" in result.lower()


def test_generate_article_defaults(project_context):
    result = run_generate_article(topic="Обзор рынка", project_context=project_context)
    assert isinstance(result, str)
    assert "таск трекер" in result or "управление задачами" in result


def test_generate_post_telegram(project_context):
    result = run_generate_post(platform="telegram", project_context=project_context, topic="Новая фича")
    assert isinstance(result, str)
    assert "telegram" in result.lower()
    assert "эмодзи" in result.lower() or "emoji" in result.lower() or "форматирован" in result.lower()


def test_generate_post_vk(project_context):
    result = run_generate_post(platform="vk", project_context=project_context, topic="Кейс клиента")
    assert isinstance(result, str)
    assert "vk" in result.lower() or "вк" in result.lower()


def test_generate_post_no_topic(project_context):
    result = run_generate_post(platform="telegram", project_context=project_context)
    assert isinstance(result, str)
    assert "управление проектами" in result or "таск трекер" in result


def test_repurpose_content(project_context):
    source_text = "Длинная статья о том, как управлять задачами в команде. " * 10
    result = run_repurpose_content(text=source_text, project_context=project_context)
    assert isinstance(result, str)
    assert "telegram" in result.lower()
    assert "vk" in result.lower()


def test_repurpose_specific_formats(project_context):
    source_text = "Статья о продуктивности для фрилансеров." * 5
    result = run_repurpose_content(text=source_text, project_context=project_context, formats=["telegram", "carousel"])
    assert isinstance(result, str)
    assert "telegram" in result.lower()
    assert "карусель" in result.lower() or "carousel" in result.lower()
