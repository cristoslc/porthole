"""Test forward/back navigation and global quit across the TUI wizard."""

from __future__ import annotations

import pytest

from porthole_setup.app import PortholeApp
from porthole_setup.screens.enrollment import EnrollmentScreen
from porthole_setup.screens.hub_check import HubCheckScreen
from porthole_setup.screens.prerequisites import PrerequisitesScreen
from porthole_setup.screens.secrets import SecretsScreen

pytest_plugins = ["tests.conftest_tui"]


# ---------------------------------------------------------------------------
# Forward navigation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prerequisites_continue_pushes_secrets(mock_all_installed):
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, PrerequisitesScreen)

        await pilot.click("#continue-btn")
        await pilot.pause()
        assert isinstance(app.screen, SecretsScreen)


@pytest.mark.asyncio
async def test_secrets_continue_pushes_hub_check(
    mock_all_installed, mock_secrets_paths, mock_subprocess_success
):
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        # Prerequisites -> Secrets
        await pilot.click("#continue-btn")
        await pilot.pause()
        assert isinstance(app.screen, SecretsScreen)

        # All secrets OK -> Continue enabled
        app.screen.age_ok = True
        app.screen.sops_ok = True
        await pilot.pause()

        await pilot.click("#continue-btn")
        await pilot.pause()
        assert isinstance(app.screen, HubCheckScreen)


@pytest.mark.asyncio
async def test_three_screen_forward_flow(
    mock_all_installed,
    mock_secrets_paths,
    mock_network_state,
    mock_subprocess_success,
):
    """Walk Prerequisites -> Secrets -> HubCheck -> Enrollment."""
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, PrerequisitesScreen)

        # -> Secrets
        await pilot.click("#continue-btn")
        await pilot.pause()
        assert isinstance(app.screen, SecretsScreen)

        # -> HubCheck
        app.screen.age_ok = True
        app.screen.sops_ok = True
        await pilot.pause()
        await pilot.click("#continue-btn")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, HubCheckScreen)

        # -> Enrollment
        await pilot.click("#continue-btn")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, EnrollmentScreen)


# ---------------------------------------------------------------------------
# Back navigation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_secrets_back_pops_to_prerequisites(mock_all_installed, mock_secrets_paths):
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.click("#continue-btn")
        await pilot.pause()
        assert isinstance(app.screen, SecretsScreen)

        await pilot.click("#back-btn")
        await pilot.pause()
        assert isinstance(app.screen, PrerequisitesScreen)


@pytest.mark.asyncio
async def test_hub_check_back_pops_to_secrets(
    mock_all_installed, mock_secrets_paths, mock_network_state, mock_subprocess_success
):
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
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

        await pilot.click("#back-btn")
        await pilot.pause()
        assert isinstance(app.screen, SecretsScreen)


@pytest.mark.asyncio
async def test_enrollment_back_pops_to_hub_check(
    mock_all_installed,
    mock_secrets_paths,
    mock_network_state,
    mock_subprocess_success,
):
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
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

        await pilot.click("#continue-btn")  # -> Enrollment
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, EnrollmentScreen)

        await pilot.click("#back-btn")
        await pilot.pause()
        assert isinstance(app.screen, HubCheckScreen)


# ---------------------------------------------------------------------------
# Global quit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ctrl_q_exits_from_prerequisites(mock_all_installed):
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, PrerequisitesScreen)
        await pilot.press("ctrl+q")
        await pilot.pause()


@pytest.mark.asyncio
async def test_ctrl_q_exits_from_secrets(mock_all_installed):
    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.click("#continue-btn")  # -> Secrets
        await pilot.pause()
        assert isinstance(app.screen, SecretsScreen)
        await pilot.press("ctrl+q")
        await pilot.pause()
