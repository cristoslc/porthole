"""Tests for PrerequisitesScreen — ansible-based tool installation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from textual.widgets import Button

from porthole_setup.app import PortholeApp
from porthole_setup.screens.prerequisites import PrerequisitesScreen

pytest_plugins = ["tests.conftest_tui"]


@pytest.mark.asyncio
async def test_continue_disabled_on_mount(mock_ansible_noop):
    """Continue button starts disabled while ansible runs."""
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, PrerequisitesScreen)
        btn = app.screen.query_one("#continue-btn", Button)
        # Button is disabled until ansible succeeds and tools verified
        assert btn.disabled is True


@pytest.mark.asyncio
async def test_continue_enabled_after_ansible_success(mock_ansible_success):
    """Continue button enables after ansible succeeds and tools are on PATH."""
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        # Give the background worker time to complete
        await pilot.pause()
        await pilot.pause()
        await pilot.pause()
        btn = app.screen.query_one("#continue-btn", Button)
        assert btn.disabled is False


@pytest.mark.asyncio
async def test_retry_enabled_after_ansible_failure(mock_ansible_failure):
    """Retry button enables when ansible fails."""
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.pause()
        await pilot.pause()
        btn = app.screen.query_one("#retry-btn", Button)
        assert btn.disabled is False
