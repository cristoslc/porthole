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
    await pilot.pause()
    await pilot.click("#continue-btn")  # -> HubCheck
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()
    assert isinstance(app.screen, HubCheckScreen)


@pytest.mark.asyncio
async def test_state_not_found_shows_init_section(
    mock_all_installed, mock_secrets_paths, monkeypatch, mock_subprocess_success
):
    """When load_state raises StateNotFoundError, init section is shown."""
    monkeypatch.setattr(
        "porthole_setup.screens.hub_check.load_state",
        lambda: (_ for _ in ()).throw(StateNotFoundError("missing")),
    )

    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await _navigate_to_hub_check(pilot, app)

        # State label should show not found
        state_label = app.screen.query_one("#state-label", Label)
        assert "not found" in str(state_label.render()).lower()

        # Init section should be visible with endpoint input and buttons
        init_section = app.screen.query_one("#init-section")
        assert init_section.display is True


@pytest.mark.asyncio
async def test_hub_state_loaded_shows_continue(
    mock_all_installed,
    mock_secrets_paths,
    mock_network_state,
    mock_subprocess_success,
):
    """When state loads successfully, Continue button appears."""
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await _navigate_to_hub_check(pilot, app)

        # Should have a continue button
        btn = app.screen.query_one("#continue-btn", Button)
        assert btn.variant == "success"

        # Should also have spinup and reinit buttons
        app.screen.query_one("#spinup-btn", Button)
        app.screen.query_one("#reinit-btn", Button)
