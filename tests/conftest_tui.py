"""Shared fixtures and helpers for Textual TUI tests."""

from __future__ import annotations

import asyncio
from contextlib import nullcontext
from unittest.mock import AsyncMock, MagicMock

import pytest

from porthole_setup.state import NetworkState, Peer


# ---------------------------------------------------------------------------
# Async subprocess mock helper
# ---------------------------------------------------------------------------


def make_fake_subprocess(
    returncode: int = 0,
    stdout_lines: list[bytes] | None = None,
):
    """Return an async callable replacing asyncio.create_subprocess_exec."""

    async def fake_create(*args, **kwargs):
        proc = MagicMock()
        proc.returncode = returncode
        proc.wait = AsyncMock(return_value=returncode)
        proc.communicate = AsyncMock(return_value=(b"", b""))

        if stdout_lines is not None:
            async def _aiter():
                for line in stdout_lines:
                    yield line

            proc.stdout = _aiter()
        else:
            async def _empty():
                return
                yield  # noqa: RET504 — make it an async generator

            proc.stdout = _empty()

        return proc

    return fake_create


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _fake_popen(returncode=0, stdout_lines=None):
    """Return a class that fakes subprocess.Popen for ansible-playbook."""
    class FakePopen:
        def __init__(self, cmd, **kwargs):
            self.returncode = returncode
            self._lines = stdout_lines or []
            self.stdout = iter(self._lines)

        def wait(self):
            return self.returncode

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    return FakePopen


@pytest.fixture
def mock_ansible_noop(monkeypatch):
    """Patch subprocess.Popen so ansible appears to be running (blocks briefly)."""
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.subprocess.Popen",
        _fake_popen(returncode=0, stdout_lines=["PLAY [Install porthole prerequisites]\n"]),
    )
    # Tools not yet installed — continue should stay disabled
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.is_installed", lambda _: False
    )


@pytest.fixture
def mock_ansible_success(monkeypatch):
    """Patch so ansible succeeds and all tools appear installed."""
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.subprocess.Popen",
        _fake_popen(returncode=0, stdout_lines=["ok: [localhost]\n"]),
    )
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.is_installed", lambda _: True
    )


@pytest.fixture
def mock_ansible_failure(monkeypatch):
    """Patch so ansible fails."""
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.subprocess.Popen",
        _fake_popen(returncode=1, stdout_lines=["fatal: [localhost]: FAILED!\n"]),
    )
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.is_installed", lambda _: False
    )


@pytest.fixture
def mock_all_installed(monkeypatch):
    """Patch so ansible succeeds and all tools are installed (for downstream screens)."""
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.subprocess.Popen",
        _fake_popen(returncode=0, stdout_lines=["ok: [localhost]\n"]),
    )
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.is_installed", lambda _: True
    )


@pytest.fixture
def mock_network_state(monkeypatch):
    """Provide a valid NetworkState for screens that call load_state()."""
    state = NetworkState(
        endpoint="hub.example.com:51820",
        peers=[
            Peer(
                name="testhost",
                ip="10.100.0.2",
                public_key="testkey=",
                role="workstation",
            )
        ],
    )
    for mod in [
        "porthole_setup.screens.hub_check",
        "porthole_setup.screens.enrollment",
        "porthole_setup.screens.summary",
    ]:
        monkeypatch.setattr(f"{mod}.load_state", lambda s=state: s)
    # service_install imports load_state inside a method body
    monkeypatch.setattr("porthole_setup.state.load_state", lambda s=state: s)
    return state


@pytest.fixture
def mock_subprocess_success(monkeypatch):
    """No-op all subprocess calls with rc=0."""
    monkeypatch.setattr(
        "asyncio.create_subprocess_exec",
        make_fake_subprocess(returncode=0),
    )
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: MagicMock(returncode=0, stdout="", stderr=""),
    )


@pytest.fixture
def mock_suspend(monkeypatch):
    """No-op App.suspend()."""
    monkeypatch.setattr(
        "textual.app.App.suspend", lambda self: nullcontext()
    )


@pytest.fixture
def mock_secrets_paths(monkeypatch, tmp_path):
    """Redirect secrets + hub_check path constants to tmp_path with files present."""
    age_key = tmp_path / "keys.txt"
    age_key.parent.mkdir(parents=True, exist_ok=True)
    age_key.write_text("# public key: age1testpubkey123\nAGE-SECRET-KEY-1TEST\n")

    sops_yaml = tmp_path / ".sops.yaml"
    sops_yaml.write_text("creation_rules: []\n")

    state_file = tmp_path / "network.sops.yaml"
    state_file.write_text("encrypted: true\n")

    monkeypatch.setattr("porthole_setup.screens.secrets.AGE_KEY_PATH", age_key)
    monkeypatch.setattr("porthole_setup.screens.secrets.SOPS_CONFIG_PATH", sops_yaml)
    monkeypatch.setattr("porthole_setup.screens.hub_check.STATE_PATH", state_file)
    monkeypatch.setattr("porthole_setup.screens.hub_check.AGE_KEY_PATH", age_key)
    return tmp_path


@pytest.fixture
def mock_summary_deps(monkeypatch, mock_all_installed, mock_secrets_paths):
    """Mock all dependencies for SummaryScreen."""
    monkeypatch.setattr(
        "porthole_setup.screens.summary.is_installed", lambda _: True
    )
    monkeypatch.setattr(
        "porthole_setup.screens.summary.AGE_KEY_PATH",
        mock_secrets_paths / "keys.txt",
    )
    monkeypatch.setattr(
        "porthole_setup.screens.summary.SOPS_CONFIG_PATH",
        mock_secrets_paths / ".sops.yaml",
    )
    monkeypatch.setattr(
        "porthole_setup.screens.summary.STATE_PATH",
        mock_secrets_paths / "network.sops.yaml",
    )
