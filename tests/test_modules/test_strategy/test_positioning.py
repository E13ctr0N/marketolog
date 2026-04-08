"""Tests for analyze_positioning tool."""

import pytest

from marketolog.modules.strategy.positioning import run_analyze_positioning


def test_positioning_with_competitors(project_context):
    """Builds positioning map when competitors are present."""
    result = run_analyze_positioning(project_context=project_context)

    assert isinstance(result, str)
    assert "позиционирование" in result.lower() or "УТП" in result
    assert "Trello" in result or "конкурент" in result.lower()
    assert "управление проектами" in result


def test_positioning_no_competitors(project_context):
    """Without competitors — still gives positioning guidance."""
    project_context["competitors"] = []
    result = run_analyze_positioning(project_context=project_context)

    assert isinstance(result, str)
    assert len(result) > 50


def test_positioning_uses_audience(project_context):
    """Positioning references audience segments."""
    result = run_analyze_positioning(project_context=project_context)

    assert isinstance(result, str)
    assert "управление проектами" in result
