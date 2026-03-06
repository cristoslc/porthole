"""Tests for EnrollmentScreen — registration and error states."""

from __future__ import annotations

import pytest
from textual.widgets import Button, Label

from porthole_setup.app import PortholeApp
from porthole_setup.screens.enrollment import EnrollmentScreen
from porthole_setup.state import StateNotFoundError

pytest_plugins = ["tests.conftest_tui"]


@pytest.mark.asyncio
async def test_enrollment_shows_already_registered(
    monkeypatch, mock_subprocess_success
):
    """When peer is already in state, shows registered status and Continue."""
    from porthole_setup.state import NetworkState, Peer

    state = NetworkState(
        endpoint="hub.example.com:51820",
        peers=[Peer(name="testhost", ip="10.100.0.2", public_key="k=", role="workstation")],
    )
    monkeypatch.setattr("porthole_setup.screens.enrollment.load_state", lambda: state)
    monkeypatch.setattr("socket.gethostname", lambda: "testhost")

    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await app.push_screen(EnrollmentScreen())
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        label = app.screen.query_one("#status-label", Label)
        assert "already registered" in str(label.render()).lower()

        btn = app.screen.query_one("#continue-btn", Button)
        assert btn is not None


@pytest.mark.asyncio
async def test_enrollment_state_error_shows_back_only(monkeypatch, mock_subprocess_success):
    """When load_state fails, only Back button is shown."""
    monkeypatch.setattr(
        "porthole_setup.screens.enrollment.load_state",
        lambda: (_ for _ in ()).throw(StateNotFoundError("missing")),
    )
    monkeypatch.setattr("socket.gethostname", lambda: "testhost")

    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await app.push_screen(EnrollmentScreen())
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        buttons = app.screen.query("#button-row Button")
        button_ids = [b.id for b in buttons]
        assert "back-btn" in button_ids
        assert "continue-btn" not in button_ids


@pytest.mark.asyncio
async def test_enrollment_back_pops_screen(monkeypatch, mock_subprocess_success):
    """Back button pops the enrollment screen."""
    from porthole_setup.state import NetworkState, Peer

    state = NetworkState(
        endpoint="hub.example.com:51820",
        peers=[Peer(name="testhost", ip="10.100.0.2", public_key="k=", role="workstation")],
    )
    monkeypatch.setattr("porthole_setup.screens.enrollment.load_state", lambda: state)
    monkeypatch.setattr("socket.gethostname", lambda: "testhost")

    app = PortholeApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await app.push_screen(EnrollmentScreen())
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        await pilot.click("#back-btn")
        await pilot.pause()
        assert not isinstance(app.screen, EnrollmentScreen)
