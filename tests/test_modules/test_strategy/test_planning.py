"""Tests for marketing_plan tool."""

import pytest

from marketolog.modules.strategy.planning import run_marketing_plan


def test_marketing_plan_default(project_context):
    """Generates 3-month plan by default."""
    result = run_marketing_plan(project_context=project_context)

    assert isinstance(result, str)
    assert "маркетинговый план" in result.lower() or "план" in result.lower()
    assert "3 месяц" in result or "3 month" in result.lower() or "квартал" in result.lower()
    assert "управление проектами" in result


def test_marketing_plan_with_budget(project_context):
    """Plan includes budget allocation when provided."""
    result = run_marketing_plan(
        project_context=project_context,
        period="1 month",
        budget="50000",
    )

    assert isinstance(result, str)
    assert "50" in result
    assert "1 month" in result.lower() or "1 месяц" in result


def test_marketing_plan_minimal_context(project_context):
    """Works with minimal project data."""
    minimal = {
        "name": "test",
        "url": "https://test.ru",
        "niche": "тестирование",
        "description": "Тестовый продукт",
    }
    result = run_marketing_plan(project_context=minimal)

    assert isinstance(result, str)
    assert len(result) > 100


def test_marketing_plan_includes_channels(project_context):
    """Plan references configured social channels."""
    result = run_marketing_plan(project_context=project_context)

    assert isinstance(result, str)
    assert "telegram" in result.lower() or "vk" in result.lower()
