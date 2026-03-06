"""Tests for HubCheckScreen — state errors and reachability."""

from __future__ import annotations

import pytest
from textual.widgets import Button, Label

from porthole_setup.app import PortholeApp
from porthole_setup.screens.hub_check import HubCheckScreen
from porthole_setup.state import StateNotFoundError

pytest_plugins = ["tests.conftest_tui"]


async def _navigate_to_hub_check(pilot, app):
    """Helper: navigate from Prerequisites through Secrets to HubCheck."""
    await pilot.pause()
    await pilot.click("#continue-btn")  # -> Secrets
    await pilot.pause()
    app.screen.age_ok = True
    app.screen.sops_ok = True
    app.screen.state_ok = True
    await pilot.pause()
    await pilot.click("#continue-btn")  # -> HubCheck
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()
    assert isinstance(app.screen, HubCheckScreen)


@pytest.mark.asyncio
async def test_state_not_found_shows_error_and_back_only(
    mock_all_installed, mock_secrets_paths, monkeypatch, mock_subprocess_success
):
    """When load_state raises, only Back button is shown."""
    monkeypatch.setattr(
        "porthole_setup.screens.hub_check.load_state",
        lambda: (_ for _ in ()).throw(StateNotFoundError("missing")),
    )

    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await _navigate_to_hub_check(pilot, app)

        # Should show error in endpoint label
        label = app.screen.query_one("#endpoint-label", Label)
        assert "not found" in str(label.render()).lower()

        # Only back button, no continue
        buttons = app.screen.query("#button-row Button")
        button_ids = [b.id for b in buttons]
        assert "back-btn" in button_ids
        assert "continue-btn" not in button_ids


@pytest.mark.asyncio
async def test_hub_reachable_shows_continue(
    mock_all_installed,
    mock_secrets_paths,
    mock_network_state,
    mock_subprocess_success,
):
    """When hub is reachable, Continue button appears."""
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await _navigate_to_hub_check(pilot, app)

        # Should have a continue button
        btn = app.screen.query_one("#continue-btn", Button)
        assert btn.variant == "success"
