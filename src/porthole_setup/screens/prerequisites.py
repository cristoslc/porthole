"""Prerequisites screen — check and install required tools."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RichLog, Static

from rich.markup import escape
from rich.text import Text

from porthole_setup.platform import (
    NEEDS_SUDO,
    detect_os,
    get_install_command,
    get_manual_hint,
    get_tool_description,
    is_installed,
)

_log = logging.getLogger(__name__)

# (binary_to_check, display_name_shown_in_ui, platform_key_for_install_commands)
TOOLS: list[tuple[str, str, str]] = [
    ("uv",               "uv",              "uv"),
    ("wg",               "wireguard-tools", "wireguard-tools"),
    ("sops",             "sops",            "sops"),
    ("age",              "age",             "age"),
    ("porthole",          "porthole",         "porthole"),
    ("terraform",        "terraform",       "terraform"),
    ("ansible-playbook", "ansible",         "ansible"),
]

_SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

CSS = """
PrerequisitesScreen { background: $surface; }
.section-title { text-style: bold; color: $accent; margin: 1 0 0 1; }

#prereq-layout { width: 1fr; height: 1fr; }
#tool-sidebar { width: 44; padding: 1 2; border-right: solid $primary; }
#tool-sidebar-title { text-style: bold; margin: 0 0 1 0; }
#elapsed-timer { dock: bottom; height: auto; padding: 0 0; margin: 1 0 0 0; }

.tool-status-row { height: auto; margin: 0 0; }
.tool-icon { width: 3; }
.tool-name { width: 1fr; }
.tool-state { width: auto; color: $text-muted; }
.tool-detail { color: $text-muted; margin: 0 0 0 3; height: auto; }

.status-installed .tool-icon { color: $success; }
.status-pending .tool-icon { color: $text-muted; }
.status-queued .tool-icon { color: $warning; }
.status-installing .tool-icon { color: $warning; text-style: bold; }
.status-done .tool-icon { color: $success; }
.status-failed .tool-icon { color: $error; }

#log-panel { width: 1fr; height: 1fr; padding: 1 2; }
#log { width: 1fr; height: 1fr; border: solid $primary; }

#footer-buttons { height: auto; padding: 0 2; align-horizontal: center; }
#footer-buttons Button { margin: 0 1; }
"""


class ToolStatus(Enum):
    PENDING = auto()     # not yet checked / missing, idle
    INSTALLED = auto()   # present on PATH
    QUEUED = auto()      # waiting in install queue
    INSTALLING = auto()  # currently being installed
    DONE = auto()        # just installed successfully
    FAILED = auto()      # install attempted and failed


_STATUS_ICONS = {
    ToolStatus.PENDING: ("○", "status-pending"),
    ToolStatus.INSTALLED: ("✓", "status-installed"),
    ToolStatus.QUEUED: ("◌", "status-queued"),
    ToolStatus.INSTALLING: ("●", "status-installing"),
    ToolStatus.DONE: ("✓", "status-done"),
    ToolStatus.FAILED: ("✗", "status-failed"),
}

_STATUS_LABELS = {
    ToolStatus.PENDING: "",
    ToolStatus.INSTALLED: "installed",
    ToolStatus.QUEUED: "queued",
    ToolStatus.INSTALLING: "installing…",
    ToolStatus.DONE: "done",
    ToolStatus.FAILED: "failed",
}


@dataclass
class _TS:
    binary: str
    display: str
    platform_key: str
    status: ToolStatus


class PrerequisitesScreen(Screen):
    """Check and optionally install every required tool before proceeding."""

    TITLE = "Step 1 of 5: Prerequisites"
    CSS = CSS

    def __init__(self) -> None:
        super().__init__()
        self._os = detect_os()
        _log.info("PrerequisitesScreen.__init__ OS=%s", self._os)
        self._states: dict[str, _TS] = {}
        for binary, display, pk in TOOLS:
            installed = is_installed(binary)
            _log.info("  tool %s (%s): installed=%s", display, binary, installed)
            self._states[binary] = _TS(
                binary=binary,
                display=display,
                platform_key=pk,
                status=ToolStatus.INSTALLED if installed else ToolStatus.PENDING,
            )
        self._spinner_idx = 0
        self._start_time: float | None = None
        self._timer = None
        self._install_running = False
        _log.info("__init__ complete: %d tools, %d installed",
                   len(self._states),
                   sum(1 for ts in self._states.values() if ts.status == ToolStatus.INSTALLED))

    # ------------------------------------------------------------------
    # Compose — pre-create all widgets with stable IDs
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="prereq-layout"):
            with Vertical(id="tool-sidebar"):
                yield Static("[bold]Required Tools[/bold]", id="tool-sidebar-title")
                yield Static("", id="subtitle")
                for ts in self._states.values():
                    icon, cls = _STATUS_ICONS[ts.status]
                    desc = get_tool_description(ts.platform_key)
                    with Vertical(id=f"row-{ts.binary}", classes=f"tool-status-row {cls}"):
                        with Horizontal():
                            yield Static(icon, id=f"icon-{ts.binary}", classes="tool-icon")
                            yield Static(ts.display, classes="tool-name")
                            yield Static(
                                _STATUS_LABELS[ts.status],
                                id=f"state-{ts.binary}",
                                classes="tool-state",
                            )
                        if desc:
                            yield Static(f"[dim]{desc}[/dim]", id=f"desc-{ts.binary}", classes="tool-detail")
                        yield Static("", id=f"hint-{ts.binary}", classes="tool-detail")
                yield Static("", id="elapsed-timer")
            with Vertical(id="log-panel"):
                yield RichLog(id="log", highlight=True, markup=True, wrap=True)
        with Horizontal(id="footer-buttons"):
            yield Button("Install All Missing", id="install-all-btn", variant="warning", disabled=True)
            yield Button("Re-check", id="recheck-btn", variant="default")
            yield Button("Continue →", id="continue-btn", variant="success", disabled=True)
        yield Footer()

    # ------------------------------------------------------------------
    # Mount — initial state
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        _log.info("on_mount called")
        self._refresh_all_tool_ui()
        self._refresh_buttons()
        log = self.query_one("#log", RichLog)
        log.write("[dim]Ready. Click a tool's Install button or Install All Missing to begin.[/dim]")
        _log.info("on_mount complete")

    # ------------------------------------------------------------------
    # In-place UI updates (no widget teardown)
    # ------------------------------------------------------------------

    def _update_tool_ui(self, binary: str) -> None:
        """Update a single tool's icon, state label, hint, and row class in place."""
        ts = self._states[binary]
        icon_text, cls = _STATUS_ICONS[ts.status]

        # Update icon
        self.query_one(f"#icon-{binary}", Static).update(icon_text)
        # Update state label
        self.query_one(f"#state-{binary}", Static).update(_STATUS_LABELS[ts.status])

        # Update row CSS class
        row = self.query_one(f"#row-{binary}", Vertical)
        for status in ToolStatus:
            _, scls = _STATUS_ICONS[status]
            row.remove_class(scls)
        row.add_class(cls)

        # Update hint line
        hint_widget = self.query_one(f"#hint-{binary}", Static)
        if ts.status == ToolStatus.PENDING:
            cmd = get_install_command(ts.platform_key, self._os)
            hint = get_manual_hint(ts.platform_key, self._os)
            if cmd:
                sudo_note = "  [yellow](sudo)[/]" if ts.platform_key in NEEDS_SUDO else ""
                hint_widget.update(f"[dim]$ {escape(' '.join(cmd))}[/]{sudo_note}")
            elif hint:
                hint_widget.update(f"[yellow]Manual:[/] {escape(hint)}")
            else:
                hint_widget.update("[yellow]Install manually, then re-check[/]")
        elif ts.status == ToolStatus.FAILED:
            hint = get_manual_hint(ts.platform_key, self._os)
            if hint:
                hint_widget.update(f"[red]Failed.[/red] [dim]Try: {escape(hint)}[/dim]")
            else:
                hint_widget.update("[red]Failed.[/red] Check log for details.")
        elif ts.status in (ToolStatus.QUEUED, ToolStatus.INSTALLING):
            hint_widget.update("")
        else:
            hint_widget.update("")

    def _refresh_all_tool_ui(self) -> None:
        """Update all tool rows and the subtitle."""
        for binary in self._states:
            self._update_tool_ui(binary)
        self._refresh_subtitle()

    def _refresh_subtitle(self) -> None:
        missing = sum(1 for ts in self._states.values() if ts.status not in (ToolStatus.INSTALLED, ToolStatus.DONE))
        subtitle = self.query_one("#subtitle", Static)
        if missing == 0:
            subtitle.update(f"[bold green]All {len(self._states)} tools ready[/bold green]")
        else:
            subtitle.update(f"[bold]{missing} of {len(self._states)} missing[/bold]")

    def _refresh_buttons(self) -> None:
        """Enable/disable footer buttons based on current state."""
        all_ok = all(ts.status in (ToolStatus.INSTALLED, ToolStatus.DONE)
                     for ts in self._states.values())
        self.query_one("#continue-btn", Button).disabled = not all_ok

        installable = [
            ts for ts in self._states.values()
            if ts.status in (ToolStatus.PENDING, ToolStatus.FAILED)
            and get_install_command(ts.platform_key, self._os) is not None
        ]
        self.query_one("#install-all-btn", Button).disabled = (
            len(installable) == 0 or self._install_running
        )
        install_btn = self.query_one("#install-all-btn", Button)
        if installable:
            install_btn.label = f"Install All Missing ({len(installable)})"
        else:
            install_btn.label = "Install All Missing"

        self.query_one("#recheck-btn", Button).disabled = self._install_running

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#continue-btn")
    def _continue(self) -> None:
        from porthole_setup.screens.secrets import SecretsScreen  # noqa: PLC0415
        self.app.push_screen(SecretsScreen())

    @on(Button.Pressed, "#recheck-btn")
    def _recheck(self) -> None:
        for ts in self._states.values():
            if ts.status not in (ToolStatus.QUEUED, ToolStatus.INSTALLING):
                ts.status = ToolStatus.INSTALLED if is_installed(ts.binary) else ToolStatus.PENDING
        self._refresh_all_tool_ui()
        self._refresh_buttons()
        log = self.query_one("#log", RichLog)
        log.write("\n[bold]Re-checked tool availability.[/bold]")

    @on(Button.Pressed, "#install-all-btn")
    def _install_all(self) -> None:
        queue = []
        for ts in self._states.values():
            if ts.status in (ToolStatus.PENDING, ToolStatus.FAILED):
                cmd = get_install_command(ts.platform_key, self._os)
                if cmd is not None:
                    ts.status = ToolStatus.QUEUED
                    queue.append(ts.binary)
        if not queue:
            return
        self._refresh_all_tool_ui()
        self._refresh_buttons()
        self._run_install_queue(queue)

    @on(Button.Pressed)
    def _install_pressed(self, event: Button.Pressed) -> None:
        """Handle individual Install / Retry buttons (future: per-tool buttons)."""
        bid = event.button.id or ""
        if not bid.startswith("btn-"):
            return
        binary = bid.removeprefix("btn-")
        ts = self._states.get(binary)
        if ts is None or ts.status in (ToolStatus.INSTALLED, ToolStatus.DONE, ToolStatus.QUEUED, ToolStatus.INSTALLING):
            return
        cmd = get_install_command(ts.platform_key, self._os)
        if cmd is None:
            hint = get_manual_hint(ts.platform_key, self._os)
            log = self.query_one("#log", RichLog)
            if hint:
                log.write(f"[bold yellow]No auto-install for '{ts.display}'. Install manually:[/]\n  {escape(hint)}")
            else:
                log.write(f"[bold red]No install command for '{ts.display}' on {self._os.name}[/]")
            return
        ts.status = ToolStatus.QUEUED
        self._update_tool_ui(binary)
        self._refresh_buttons()
        self._run_install_queue([binary])

    # ------------------------------------------------------------------
    # Sequential install queue (single background thread)
    # ------------------------------------------------------------------

    @work(thread=True, exclusive=True)
    def _run_install_queue(self, queue: list[str]) -> None:
        """Install tools sequentially in a background thread."""
        self._install_running = True
        self._start_time = time.monotonic()
        self.app.call_from_thread(self._start_timer)

        for binary in queue:
            ts = self._states[binary]
            cmd = get_install_command(ts.platform_key, self._os)
            if cmd is None:
                continue

            ts.status = ToolStatus.INSTALLING
            self.app.call_from_thread(self._update_tool_ui, binary)
            self.app.call_from_thread(self._refresh_subtitle)

            self.app.call_from_thread(
                self._log_markup,
                f"\n[bold cyan]{'─' * 40}[/bold cyan]\n"
                f"[bold cyan]>>> Installing {ts.display}[/bold cyan]\n"
                f"[dim]$ {escape(' '.join(cmd))}[/dim]",
            )

            returncode = self._run_subprocess(cmd)

            # Post-install: check if binary is on PATH
            if returncode == 0:
                actually_installed = is_installed(binary)
                if not actually_installed:
                    actually_installed = self._check_extra_paths(binary)
                if actually_installed:
                    ts.status = ToolStatus.DONE
                    self.app.call_from_thread(
                        self._log_markup,
                        f"[bold green]✓ {ts.display} installed successfully[/bold green]",
                    )
                else:
                    ts.status = ToolStatus.FAILED
                    self.app.call_from_thread(
                        self._log_markup,
                        f"[bold yellow]Install succeeded but '{binary}' not found on PATH.[/bold yellow]\n"
                        "[dim]You may need to restart your shell or add the install location to PATH.[/dim]",
                    )
            else:
                ts.status = ToolStatus.FAILED
                hint = get_manual_hint(ts.platform_key, self._os)
                msg = f"[bold red]✗ {ts.display} install failed (exit {returncode})[/bold red]"
                if hint:
                    msg += f"\n[dim]Try manually: {escape(hint)}[/dim]"
                self.app.call_from_thread(self._log_markup, msg)

            self.app.call_from_thread(self._update_tool_ui, binary)
            self.app.call_from_thread(self._refresh_subtitle)

        # Queue complete
        self._install_running = False
        self.app.call_from_thread(self._stop_timer)
        self.app.call_from_thread(self._refresh_buttons)

        failed = [ts for ts in self._states.values() if ts.status == ToolStatus.FAILED]
        done = [ts for ts in self._states.values() if ts.status == ToolStatus.DONE]
        if failed:
            self.app.call_from_thread(
                self._log_markup,
                f"\n[bold yellow]Finished: {len(done)} installed, {len(failed)} failed.[/bold yellow]\n"
                "[dim]Click Install All Missing to retry failed tools, or Re-check after manual install.[/dim]",
            )
        else:
            self.app.call_from_thread(
                self._log_markup,
                f"\n[bold green]All {len(done)} tools installed successfully![/bold green]",
            )

    def _run_subprocess(self, cmd: list[str]) -> int:
        """Run a command in the current thread, streaming output to the log."""
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
        except FileNotFoundError as exc:
            self.app.call_from_thread(
                self._log_markup,
                f"[bold red]Command not found: {exc.filename or exc}[/bold red]\n"
                "[dim]The installer command itself is missing.[/dim]",
            )
            return 1
        except PermissionError:
            self.app.call_from_thread(
                self._log_markup,
                "[bold red]Permission denied — this install may require sudo.[/bold red]",
            )
            return 1
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(
                self._log_markup,
                f"[bold red]Error: {exc}[/bold red]",
            )
            _log.exception("Subprocess error")
            return 1

    def _check_extra_paths(self, binary: str) -> bool:
        """Check common install locations and update PATH if found."""
        extra_paths = [
            "/usr/local/bin",
            str(Path.home() / ".local/bin"),
            str(Path.home() / ".cargo/bin"),
        ]
        for extra_path in extra_paths:
            candidate = os.path.join(extra_path, binary)
            if os.path.isfile(candidate):
                self.app.call_from_thread(
                    self._log_markup,
                    f"[dim]Found at: {candidate}[/dim]",
                )
                os.environ["PATH"] = extra_path + os.pathsep + os.environ.get("PATH", "")
                if shutil.which(binary):
                    return True
        return False

    # ------------------------------------------------------------------
    # Timer / spinner
    # ------------------------------------------------------------------

    def _start_timer(self) -> None:
        self._timer = self.set_interval(1, self._tick_elapsed)

    def _stop_timer(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        # Show final elapsed
        if self._start_time is not None:
            elapsed = int(time.monotonic() - self._start_time)
            mins, secs = divmod(elapsed, 60)
            self.query_one("#elapsed-timer", Static).update(
                f"[dim]Elapsed: {mins}:{secs:02d}[/dim]"
            )

    def _tick_elapsed(self) -> None:
        if self._start_time is None:
            return
        elapsed = int(time.monotonic() - self._start_time)
        mins, secs = divmod(elapsed, 60)

        spinner = _SPINNER_FRAMES[self._spinner_idx]
        self._spinner_idx = (self._spinner_idx + 1) % len(_SPINNER_FRAMES)

        self.query_one("#elapsed-timer", Static).update(
            f"[bold yellow]{spinner}[/bold yellow] [dim]Elapsed: {mins}:{secs:02d}[/dim]"
        )

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def _log_markup(self, msg: str) -> None:
        """Write Rich-markup text to the log widget."""
        self.query_one("#log", RichLog).write(msg)

    def _log_output(self, text: str) -> None:
        """Write raw subprocess output (no markup parsing)."""
        self.query_one("#log", RichLog).write(Text(text))
