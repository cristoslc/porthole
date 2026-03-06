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


@pytest.fixture
def mock_all_installed(monkeypatch):
    """Patch platform functions so all tools appear installed."""
    from porthole_setup.platform import OS

    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.is_installed", lambda _: True
    )
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.detect_os", lambda: OS.MACOS
    )
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.get_install_command",
        lambda t, o: ["echo", "ok"],
    )
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.get_tool_description",
        lambda t: "test tool",
    )
    monkeypatch.setattr(
        "porthole_setup.screens.prerequisites.get_manual_hint",
        lambda t, o: None,
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
    """Redirect SecretsScreen path constants to tmp_path with files present."""
    age_key = tmp_path / "keys.txt"
    age_key.parent.mkdir(parents=True, exist_ok=True)
    age_key.write_text("# public key: age1testpubkey123\nAGE-SECRET-KEY-1TEST\n")

    sops_yaml = tmp_path / ".sops.yaml"
    sops_yaml.write_text("creation_rules: []\n")

    state_file = tmp_path / "network.sops.yaml"
    state_file.write_text("encrypted: true\n")

    monkeypatch.setattr("porthole_setup.screens.secrets.AGE_KEY_PATH", age_key)
    monkeypatch.setattr("porthole_setup.screens.secrets.SOPS_CONFIG_PATH", sops_yaml)
    monkeypatch.setattr("porthole_setup.screens.secrets.STATE_PATH", state_file)
    monkeypatch.setattr(
        "porthole_setup.screens.secrets._summarise_state",
        lambda: "endpoint=hub.example.com, 1 peer(s)",
    )
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
