"""Tests for PrerequisitesScreen — tool detection and Continue gating."""

from __future__ import annotations

import pytest
from textual.widgets import Button

from porthole_setup.app import PortholeApp
from porthole_setup.screens.prerequisites import PrerequisitesScreen

pytest_plugins = ["tests.conftest_tui"]


@pytest.mark.asyncio
async def test_continue_disabled_when_tool_missing(monkeypatch):
    """Continue button is disabled when any tool is not installed."""
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.is_installed", lambda t: t != "sops"
    )
    from porthole_setup.platform import OS

    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.detect_os", lambda: OS.MACOS
    )

    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, PrerequisitesScreen)
        btn = app.screen.query_one("#continue-btn", Button)
        assert btn.disabled is True


@pytest.mark.asyncio
async def test_continue_enabled_when_all_installed(mock_all_installed):
    """Continue button is enabled when all tools are installed."""
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, PrerequisitesScreen)
        btn = app.screen.query_one("#continue-btn", Button)
        assert btn.disabled is False
