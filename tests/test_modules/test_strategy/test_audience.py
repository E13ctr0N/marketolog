"""Tests for analyze_target_audience tool."""

import pytest

from marketolog.modules.strategy.audience import run_analyze_target_audience


def test_analyze_target_audience_with_existing_data(project_context):
    """When project has target_audience segments, builds detailed profiles."""
    result = run_analyze_target_audience(project_context=project_context)

    assert isinstance(result, str)
    assert "фрилансеры" in result
    assert "малые команды" in result.lower() or "малых команд" in result.lower()
    assert "управление проектами" in result


def test_analyze_target_audience_empty_segments(project_context):
    """When no audience segments — returns prompt for gathering info."""
    project_context["target_audience"] = []
    result = run_analyze_target_audience(project_context=project_context)

    assert isinstance(result, str)
    assert "update_project" in result or "целевая аудитория" in result.lower()


def test_analyze_target_audience_no_key(project_context):
    """Works without any API keys — pure context assembly."""
    result = run_analyze_target_audience(project_context=project_context)

    assert isinstance(result, str)
    assert len(result) > 100
