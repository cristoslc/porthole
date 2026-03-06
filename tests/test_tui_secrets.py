"""Tests for SecretsScreen — reactive state and button gating."""

from __future__ import annotations

import pytest
from textual.widgets import Button

from porthole_setup.app import PortholeApp
from porthole_setup.screens.secrets import SecretsScreen

pytest_plugins = ["tests.conftest_tui"]


@pytest.mark.asyncio
async def test_continue_disabled_when_secrets_missing(mock_all_installed, monkeypatch):
    """Continue disabled when age/sops/state not all OK."""
    # Don't redirect paths — let them point to nonexistent defaults
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.click("#continue-btn")  # -> Secrets
        await pilot.pause()
        assert isinstance(app.screen, SecretsScreen)

        btn = app.screen.query_one("#continue-btn", Button)
        assert btn.disabled is True


@pytest.mark.asyncio
async def test_continue_enabled_when_all_secrets_ok(mock_all_installed, mock_secrets_paths):
    """Continue enabled when all three secrets conditions are met."""
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.click("#continue-btn")  # -> Secrets
        await pilot.pause()
        assert isinstance(app.screen, SecretsScreen)

        # Secrets paths are redirected to tmp_path with files present
        # But reactive state is set in __init__ — update reactives directly
        app.screen.age_ok = True
        app.screen.sops_ok = True
        app.screen.state_ok = True
        await pilot.pause()

        btn = app.screen.query_one("#continue-btn", Button)
        assert btn.disabled is False


@pytest.mark.asyncio
async def test_back_button_exists_on_secrets(mock_all_installed):
    """SecretsScreen should have a Back button."""
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.click("#continue-btn")  # -> Secrets
        await pilot.pause()
        assert isinstance(app.screen, SecretsScreen)

        back_btn = app.screen.query_one("#back-btn", Button)
        assert back_btn is not None
