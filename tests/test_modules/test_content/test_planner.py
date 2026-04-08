"""Tests for content plan tool."""
import pytest
from marketolog.modules.content.planner import run_content_plan


def test_content_plan_basic(project_context):
    result = run_content_plan(project_context=project_context, period="2 weeks", topics_count=5)
    assert isinstance(result, str)
    assert "контент" in result.lower() or "план" in result.lower()
    assert "управление проектами" in result or "таск трекер" in result
    assert "1." in result or "1)" in result


def test_content_plan_includes_keywords(project_context):
    result = run_content_plan(project_context=project_context, period="1 month", topics_count=3)
    assert "таск трекер" in result or "управление задачами" in result


def test_content_plan_includes_audience(project_context):
    result = run_content_plan(project_context=project_context, period="1 week", topics_count=3)
    assert "фрилансер" in result.lower() or "команд" in result.lower()


def test_content_plan_default_params(project_context):
    result = run_content_plan(project_context=project_context)
    assert isinstance(result, str)
    assert len(result) > 100
