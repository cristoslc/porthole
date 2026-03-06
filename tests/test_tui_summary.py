"""Tests for SummaryScreen — check results and Finish exit."""

from __future__ import annotations

import pytest
from textual.widgets import Button, Static

from porthole_setup.app import PortholeApp
from porthole_setup.screens.summary import SummaryScreen

pytest_plugins = ["tests.conftest_tui"]


@pytest.mark.asyncio
async def test_summary_finish_button_exists(
    mock_summary_deps, mock_network_state, mock_subprocess_success
):
    """Finish button appears after checks complete."""
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await app.push_screen(SummaryScreen(peer_name="testhost"))
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        btn = app.screen.query_one("#finish-btn", Button)
        assert btn is not None


@pytest.mark.asyncio
async def test_summary_back_pops_screen(
    mock_summary_deps, mock_network_state, mock_subprocess_success
):
    """Back button pops SummaryScreen."""
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await app.push_screen(SummaryScreen(peer_name="testhost"))
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        await pilot.click("#back-btn")
        await pilot.pause()
        assert not isinstance(app.screen, SummaryScreen)


@pytest.mark.asyncio
async def test_summary_shows_banner(
    mock_summary_deps, mock_network_state, mock_subprocess_success
):
    """Summary shows a banner after checks."""
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await app.push_screen(SummaryScreen(peer_name="testhost"))
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        banner = app.screen.query_one("#banner", Static)
        text = str(banner.render()).lower()
        assert "passed" in text or "failed" in text
