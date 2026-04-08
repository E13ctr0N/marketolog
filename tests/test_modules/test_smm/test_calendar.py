"""Tests for SMM calendar and best time to post tools."""

import pytest

from marketolog.modules.smm.calendar import run_smm_calendar, run_best_time_to_post


def test_smm_calendar(project_context):
    """Calendar returns overview of channels."""
    result = run_smm_calendar(
        project_context=project_context,
        period="1 week",
    )

    assert isinstance(result, str)
    assert "telegram" in result.lower()
    assert "vk" in result.lower()


def test_smm_calendar_default_period(project_context):
    """Calendar works with default period."""
    result = run_smm_calendar(project_context=project_context)

    assert isinstance(result, str)
    assert len(result) > 50


def test_best_time_telegram(project_context):
    """Best time for Telegram posting."""
    result = run_best_time_to_post(
        project_context=project_context,
        platform="telegram",
    )

    assert isinstance(result, str)
    assert "telegram" in result.lower()
    # Should contain time recommendations
    assert ":" in result  # time format like "10:00"


def test_best_time_all_platforms(project_context):
    """Best time for all platforms."""
    result = run_best_time_to_post(
        project_context=project_context,
    )

    assert isinstance(result, str)
    assert "telegram" in result.lower() or "vk" in result.lower()
