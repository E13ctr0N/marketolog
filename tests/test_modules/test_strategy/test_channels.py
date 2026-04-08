"""Tests for channel_recommendation tool."""

import pytest

from marketolog.modules.strategy.channels import run_channel_recommendation


def test_channel_recommendation(project_context):
    """Recommends channels based on project context."""
    result = run_channel_recommendation(project_context=project_context)

    assert isinstance(result, str)
    assert "канал" in result.lower() or "рекомендац" in result.lower()
    assert "ROI" in result or "эффективность" in result.lower()


def test_channel_recommendation_with_social(project_context):
    """References configured social channels."""
    result = run_channel_recommendation(project_context=project_context)

    assert isinstance(result, str)
    assert "telegram" in result.lower()


def test_channel_recommendation_no_social(project_context):
    """Without social channels — recommends setting them up."""
    project_context["social"] = {}
    result = run_channel_recommendation(project_context=project_context)

    assert isinstance(result, str)
    assert len(result) > 100
