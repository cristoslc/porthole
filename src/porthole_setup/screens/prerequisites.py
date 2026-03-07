"""Prerequisites screen — run ansible to install required tools."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RichLog, Static

from rich.text import Text

from porthole_setup.platform import is_installed

_log = logging.getLogger(__name__)

# All tools needed by porthole. uv and ansible are bootstrapped by setup.sh;
# the rest are installed by the ansible prereqs playbook.
TOOLS: list[tuple[str, str]] = [
    ("uv",               "uv"),
    ("ansible-playbook", "ansible"),
    ("wg",               "wireguard-tools"),
    ("sops",             "sops"),
    ("age",              "age"),
    ("terraform",        "terraform"),
    ("porthole",         "porthole"),
]

# Only these are verified after ansible runs (uv and ansible are already present).
_ANSIBLE_TOOLS: list[tuple[str, str]] = [
    ("wg",               "wireguard-tools"),
    ("sops",             "sops"),
    ("age",              "age"),
    ("terraform",        "terraform"),
    ("porthole",         "porthole"),
]

# Resolve the playbook path relative to the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_PREREQS_PLAYBOOK = _REPO_ROOT / "ansible" / "prereqs.yml"

CSS = """
PrerequisitesScreen { background: $surface; }
#prereq-title { text-style: bold; color: $accent; margin: 1 0 0 1; }
#prereq-status { margin: 0 1; }
#log { margin: 1; border: solid $primary; height: 1fr; }
#footer-buttons { height: auto; padding: 0 2; align-horizontal: center; }
#footer-buttons Button { margin: 0 1; }
"""


class PrerequisitesScreen(Screen):
    """Run ansible to install prerequisites, then verify."""

    TITLE = "Step 1 of 5: Prerequisites"
    CSS = CSS

    def __init__(self) -> None:
        super().__init__()
        self._running = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("[bold]Prerequisites[/bold]", id="prereq-title")
            yield Static("", id="prereq-status")
            yield RichLog(id="log", highlight=True, markup=True, wrap=True)
        with Vertical(id="footer-buttons"):
            yield Button("Retry", id="retry-btn", variant="warning", disabled=True)
            yield Button("Continue →", id="continue-btn", variant="success", disabled=True)
        yield Footer()

    def on_mount(self) -> None:
        _log.info("PrerequisitesScreen mounted")
        self._run_ansible()

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#continue-btn")
    def _continue(self) -> None:
        from porthole_setup.screens.secrets import SecretsScreen  # noqa: PLC0415
        self.app.push_screen(SecretsScreen())

    @on(Button.Pressed, "#retry-btn")
    def _retry(self) -> None:
        self.query_one("#retry-btn", Button).disabled = True
        self.query_one("#log", RichLog).clear()
        self._run_ansible()

    # ------------------------------------------------------------------
    # Ansible runner
    # ------------------------------------------------------------------

    @work(thread=True, exclusive=True)
    def _run_ansible(self) -> None:
        self._running = True
        self.app.call_from_thread(
            self._set_status, "[bold yellow]Running ansible to install prerequisites...[/bold yellow]"
        )

        playbook = str(_PREREQS_PLAYBOOK)
        cmd = [
            "ansible-playbook", playbook,
            "--connection", "local",
            "--inventory", "localhost,",
        ]
        _log.info("Running: %s", " ".join(cmd))
        self.app.call_from_thread(
            self._log_markup, f"[dim]$ {' '.join(cmd)}[/dim]\n"
        )

        returncode = self._stream_subprocess(cmd)
        _log.info("ansible-playbook exited with %d", returncode)

        self._running = False

        if returncode == 0:
            # Verify all tools are actually on PATH
            missing = [(binary, display) for binary, display in _ANSIBLE_TOOLS if not is_installed(binary)]
            if missing:
                names = ", ".join(d for _, d in missing)
                self.app.call_from_thread(
                    self._set_status,
                    f"[bold yellow]Ansible succeeded but some tools not on PATH: {names}[/bold yellow]\n"
                    "[dim]You may need to restart your shell.[/dim]",
                )
                self.app.call_from_thread(self._enable_retry)
            else:
                self.app.call_from_thread(
                    self._set_status, "[bold green]All prerequisites installed.[/bold green]"
                )
                self.app.call_from_thread(self._enable_continue)
        else:
            self.app.call_from_thread(
                self._set_status,
                f"[bold red]Ansible failed (exit {returncode}). See log above.[/bold red]",
            )
            self.app.call_from_thread(self._enable_retry)

    def _stream_subprocess(self, cmd: list[str]) -> int:
        """Run cmd in current thread, stream output to log. Returns exit code."""
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                stripped = line.rstrip("\n")
                self.app.call_from_thread(self._log_output, stripped)
                _log.debug(stripped)
            proc.wait()
            return proc.returncode
        except FileNotFoundError:
            self.app.call_from_thread(
                self._log_markup,
                "[bold red]ansible-playbook not found.[/bold red]\n"
                "[dim]Run: uv tool install ansible[/dim]",
            )
            return 1
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(
                self._log_markup, f"[bold red]Error: {exc}[/bold red]"
            )
            _log.exception("Subprocess error")
            return 1

    # ------------------------------------------------------------------
    # UI helpers (called on main thread via call_from_thread)
    # ------------------------------------------------------------------

    def _set_status(self, msg: str) -> None:
        self.query_one("#prereq-status", Static).update(msg)

    def _log_markup(self, msg: str) -> None:
        self.query_one("#log", RichLog).write(msg)

    def _log_output(self, text: str) -> None:
        self.query_one("#log", RichLog).write(Text(text))

    def _enable_continue(self) -> None:
        self.query_one("#continue-btn", Button).disabled = False

    def _enable_retry(self) -> None:
        self.query_one("#retry-btn", Button).disabled = False
