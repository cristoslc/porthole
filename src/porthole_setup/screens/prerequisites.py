"""Prerequisites screen — check and install required tools."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, RichLog, Static

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

CSS = """
PrerequisitesScreen { background: $surface; }
.section-title { text-style: bold; color: $accent; margin: 1 0 0 1; }
.tool-row { margin: 0 1 0 2; }
.tool-desc { color: $text-muted; margin: 0 1 0 6; }
.tool-hint { color: $warning; margin: 0 1 0 6; }
.ok  { color: $success; }
.bad { color: $error;   }
#log { height: 12; border: solid $primary; margin: 1; display: none; }
#log.visible { display: block; }
#continue-btn { margin: 1; dock: bottom; }
#install-all-btn { margin: 0 1; }
"""


@dataclass
class _TS:
    binary: str
    display: str
    platform_key: str
    installed: bool
    installing: bool = field(default=False)


class PrerequisitesScreen(Screen):
    """Check and optionally install every required tool before proceeding."""

    TITLE = "Step 1 of 5: Prerequisites"
    CSS = CSS

    def __init__(self) -> None:
        super().__init__()
        self._os = detect_os()
        _log.info("PrerequisitesScreen.__init__ OS=%s", self._os)
        self._states = {}
        for binary, display, pk in TOOLS:
            installed = is_installed(binary)
            _log.info("  tool %s (%s): installed=%s", display, binary, installed)
            self._states[binary] = _TS(
                binary=binary,
                display=display,
                platform_key=pk,
                installed=installed,
            )
        _log.info("__init__ complete: %d tools, %d installed",
                   len(self._states),
                   sum(1 for ts in self._states.values() if ts.installed))

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        yield ScrollableContainer(
            Label("Required tools", classes="section-title"),
            Static("Checking…", id="subtitle", classes="tool-row"),
            Vertical(id="tool-list"),
            RichLog(id="log", highlight=True, markup=True),
        )
        yield Button("Continue →", id="continue-btn", variant="success", disabled=True)
        yield Footer()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        _log.info("on_mount called")
        self._rebuild_rows()
        self._refresh_continue()
        _log.info("on_mount complete")

    def _rebuild_rows(self) -> None:
        """Re-render tool rows after install status changes."""
        _log.info("_rebuild_rows starting")
        container = self.query_one("#tool-list", Vertical)
        container.remove_children()
        _log.info("  old children removed")

        any_missing = False
        for ts in self._states.values():
            icon = "✓" if ts.installed else "✗"
            icon_cls = "ok" if ts.installed else "bad"
            desc = get_tool_description(ts.platform_key)

            container.mount(
                Label(
                    f"[{icon_cls}]{icon}[/]  {ts.display}",
                    id=f"lbl-{ts.binary}",
                    classes="tool-row",
                )
            )
            if desc:
                container.mount(
                    Static(f"[dim]{desc}[/]", classes="tool-desc")
                )
            if not ts.installed and not ts.installing:
                any_missing = True
                cmd = get_install_command(ts.platform_key, self._os)
                hint = get_manual_hint(ts.platform_key, self._os)
                if cmd:
                    sudo_note = "  [yellow](requires sudo)[/]" if ts.platform_key in NEEDS_SUDO else ""
                    container.mount(
                        Button(f"Install {ts.display}", id=f"btn-{ts.binary}", variant="primary")
                    )
                    container.mount(
                        Static(
                            f"[dim]Will run: {' '.join(cmd)}[/]{sudo_note}",
                            classes="tool-hint",
                        )
                    )
                elif hint:
                    container.mount(
                        Static(f"[yellow]Manual install:[/] {hint}", classes="tool-hint")
                    )
                else:
                    container.mount(
                        Static(
                            "[yellow]No auto-install available — install manually and re-check[/]",
                            classes="tool-hint",
                        )
                    )
            elif ts.installing:
                container.mount(
                    Static("[dim]Installing…[/]", classes="tool-hint")
                )

        # Install All button — only if there are multiple missing tools with auto-install
        installable_missing = [
            ts for ts in self._states.values()
            if not ts.installed and not ts.installing
            and get_install_command(ts.platform_key, self._os) is not None
        ]
        if len(installable_missing) > 1:
            container.mount(
                Button(
                    f"Install All Missing ({len(installable_missing)})",
                    id="install-all-btn",
                    variant="warning",
                )
            )
        elif any_missing:
            container.mount(
                Button("Re-check", id="recheck-btn", variant="default")
            )

        # Update subtitle
        missing = sum(1 for ts in self._states.values() if not ts.installed)
        _log.info("  mounted all rows, missing=%d", missing)
        try:
            subtitle = self.query_one("#subtitle", Static)
            if missing == 0:
                subtitle.update(f"[bold green]All {len(self._states)} tools installed[/]")
            else:
                subtitle.update(
                    f"[bold]{missing} of {len(self._states)} tools missing[/] — install them below"
                )
        except Exception as exc:  # noqa: BLE001
            _log.error("  subtitle update failed: %s", exc)
        _log.info("_rebuild_rows complete")

    @on(Button.Pressed, "#continue-btn")
    def _continue(self) -> None:
        from porthole_setup.screens.secrets import SecretsScreen  # noqa: PLC0415
        self.app.push_screen(SecretsScreen())

    @on(Button.Pressed, "#recheck-btn")
    def _recheck(self) -> None:
        for ts in self._states.values():
            ts.installed = is_installed(ts.binary)
        self._rebuild_rows()
        self._refresh_continue()
        self._log("[bold]Re-checked tool availability[/]")

    @on(Button.Pressed, "#install-all-btn")
    def _install_all(self) -> None:
        for ts in self._states.values():
            if ts.installed or ts.installing:
                continue
            cmd = get_install_command(ts.platform_key, self._os)
            if cmd is None:
                continue
            ts.installing = True
            self._run_install(ts.binary, ts.display, cmd)
        self._rebuild_rows()

    @on(Button.Pressed)
    def _install_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if not bid.startswith("btn-"):
            return
        binary = bid.removeprefix("btn-")
        ts = self._states.get(binary)
        if ts is None or ts.installing or ts.installed:
            return
        cmd = get_install_command(ts.platform_key, self._os)
        if cmd is None:
            hint = get_manual_hint(ts.platform_key, self._os)
            if hint:
                self._log(f"[bold yellow]No auto-install for '{ts.display}'. Install manually:[/]\n  {hint}")
            else:
                self._log(f"[bold red]No install command for '{ts.display}' on {self._os.name}[/]")
            return
        ts.installing = True
        event.button.disabled = True
        self._run_install(binary, ts.display, cmd)

    @work(exclusive=False)
    async def _run_install(self, binary: str, display: str, cmd: list[str]) -> None:
        log = self.query_one("#log", RichLog)
        log.add_class("visible")
        log.write(f"\n[bold]Installing {display}…[/]")
        log.write(f"[dim]$ {' '.join(cmd)}[/]")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            assert proc.stdout is not None
            async for raw in proc.stdout:
                log.write(raw.decode(errors="replace").rstrip())
            returncode = await proc.wait()
        except FileNotFoundError as exc:
            log.write(f"[bold red]Command not found: {exc.filename or exc}[/]")
            log.write("[dim]The installer command itself is missing. Install it first or use the manual method.[/]")
            returncode = 1
        except PermissionError:
            log.write("[bold red]Permission denied — this install may require sudo.[/]")
            log.write("[dim]Try running the setup TUI with sudo, or install this tool manually.[/]")
            returncode = 1
        except Exception as exc:  # noqa: BLE001
            log.write(f"[bold red]Error: {exc}[/]")
            returncode = 1

        ts = self._states[binary]
        ts.installing = False

        if returncode == 0:
            # Re-check — the binary might have been installed to a path
            # that requires a shell restart to appear on PATH
            actually_installed = is_installed(binary)
            if actually_installed:
                ts.installed = True
                log.write(f"[bold green]✓ {display} installed successfully[/]")
            else:
                log.write(f"[bold yellow]Install command succeeded but '{binary}' not found on PATH.[/]")
                log.write("[dim]You may need to restart your shell or add the install location to PATH.[/]")
                # Check common locations
                import shutil  # noqa: PLC0415
                for extra_path in ["/usr/local/bin", str(__import__("pathlib").Path.home() / ".local/bin"),
                                   str(__import__("pathlib").Path.home() / ".cargo/bin")]:
                    import os  # noqa: PLC0415
                    candidate = os.path.join(extra_path, binary)
                    if os.path.isfile(candidate):
                        log.write(f"[dim]Found at: {candidate}[/]")
                        # Add to PATH for this session
                        os.environ["PATH"] = extra_path + os.pathsep + os.environ.get("PATH", "")
                        if shutil.which(binary):
                            ts.installed = True
                            log.write(f"[bold green]✓ {display} found after PATH update[/]")
                        break
        else:
            log.write(f"[bold red]✗ {display} install failed (exit {returncode})[/]")
            hint = get_manual_hint(ts.platform_key, self._os)
            if hint:
                log.write(f"[dim]Try installing manually: {hint}[/]")

        self._rebuild_rows()
        self._refresh_continue()

    def _refresh_continue(self) -> None:
        all_ok = all(ts.installed for ts in self._states.values())
        self.query_one("#continue-btn", Button).disabled = not all_ok

    def _log(self, msg: str) -> None:
        log = self.query_one("#log", RichLog)
        log.add_class("visible")
        log.write(msg)
