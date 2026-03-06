"""Tests for ServiceInstallScreen — platform detection and button gating."""

from __future__ import annotations

import pytest
from textual.widgets import Button

from porthole_setup.app import PortholeApp
from porthole_setup.platform import OS
from porthole_setup.screens.service_install import ServiceInstallScreen

pytest_plugins = ["tests.conftest_tui"]


@pytest.mark.asyncio
async def test_install_disabled_when_scripts_missing(monkeypatch, tmp_path):
    """Install button disabled when peer scripts directory doesn't exist."""
    monkeypatch.setattr("porthole_setup.screens.service_install.detect_os", lambda: OS.MACOS)

    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        # Push directly — scripts dir won't exist
        await app.push_screen(ServiceInstallScreen(peer_name="nonexistent"))
        await pilot.pause()

        btn = app.screen.query_one("#install-btn", Button)
        assert btn.disabled is True


@pytest.mark.asyncio
async def test_back_button_pops_screen(monkeypatch):
    """Back button pops ServiceInstallScreen."""
    monkeypatch.setattr("porthole_setup.screens.service_install.detect_os", lambda: OS.MACOS)

    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await app.push_screen(ServiceInstallScreen(peer_name="test"))
        await pilot.pause()
        assert isinstance(app.screen, ServiceInstallScreen)

        await pilot.click("#back-btn")
        await pilot.pause()
        assert not isinstance(app.screen, ServiceInstallScreen)
