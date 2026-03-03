"""Prerequisites screen — check and install required tools."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, RichLog, Static

from porthole_setup.platform import detect_os, get_install_command, is_installed

# (binary_to_check, display_name_shown_in_ui, platform_key_for_install_commands)
TOOLS: list[tuple[str, str, str]] = [
    ("uv",               "uv",              "uv"),
    ("wg",               "wireguard-tools", "wireguard-tools"),
    ("sops",             "sops",            "sops"),
    ("age",              "age",             "age"),
    ("wgmesh",           "wgmesh",          "wgmesh"),
    ("terraform",        "terraform",       "terraform"),
    ("ansible-playbook", "ansible",         "ansible"),
]

CSS = """
PrerequisitesScreen { background: $surface; }
.section-title { text-style: bold; color: $accent; margin: 1 0 0 1; }
.tool-row { height: 3; layout: horizontal; align: left middle; margin: 0 1; }
.tool-status { width: 4; }
.tool-name   { width: 22; }
.ok  { color: $success; }
.bad { color: $error;   }
#log { height: 10; border: solid $primary; margin: 1; display: none; }
#log.visible { display: block; }
#continue-btn { margin: 1; dock: bottom; }
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
        self._states = {
            binary: _TS(
                binary=binary,
                display=display,
                platform_key=pk,
                installed=is_installed(binary),
            )
            for binary, display, pk in TOOLS
        }

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        rows = [self._make_row(ts) for ts in self._states.values()]
        yield ScrollableContainer(
            Label("Required tools", classes="section-title"),
            Vertical(*rows, id="tool-list"),
            RichLog(id="log", highlight=True, markup=True),
        )
        all_ok = all(ts.installed for ts in self._states.values())
        yield Button("Continue →", id="continue-btn", variant="success", disabled=not all_ok)
        yield Footer()

    def _make_row(self, ts: _TS) -> Static:
        icon = "✓" if ts.installed else "✗"
        css = "ok" if ts.installed else "bad"
        parts: list[str] = [
            f"[id=icon-{ts.binary}]{icon}[/]  [{css}]{ts.display}[/]",
        ]
        row = Static(" ".join(parts), id=f"row-{ts.binary}", classes="tool-row")
        return row

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        self._rebuild_rows()
        self._refresh_continue()

    def _rebuild_rows(self) -> None:
        """Re-render tool rows (handles adding Install buttons)."""
        container = self.query_one("#tool-list", Vertical)
        container.remove_children()
        for ts in self._states.values():
            icon = "✓" if ts.installed else "✗"
            icon_cls = "ok" if ts.installed else "bad"
            container.mount(
                Label(
                    f"[{icon_cls}]{icon}[/]  {ts.display}",
                    id=f"lbl-{ts.binary}",
                    classes="tool-row tool-name",
                )
            )
            if not ts.installed and not ts.installing:
                container.mount(
                    Button("Install", id=f"btn-{ts.binary}", variant="primary")
                )

    @on(Button.Pressed, "#continue-btn")
    def _continue(self) -> None:
        from porthole_setup.screens.secrets import SecretsScreen  # noqa: PLC0415
        self.app.push_screen(SecretsScreen())

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
            self._log(f"[bold red]No install command for '{ts.display}' on {self._os.name}[/]")
            return
        ts.installing = True
        event.button.disabled = True
        self._run_install(binary, ts.display, cmd)

    @work(exclusive=False)
    async def _run_install(self, binary: str, display: str, cmd: list[str]) -> None:
        log = self.query_one("#log", RichLog)
        log.add_class("visible")
        log.write(f"[bold]$ {' '.join(cmd)}[/]")

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
        except Exception as exc:  # noqa: BLE001
            log.write(f"[bold red]Error: {exc}[/]")
            returncode = 1

        ts = self._states[binary]
        ts.installing = False
        if returncode == 0:
            ts.installed = True
            log.write(f"[bold green]✓ {display} installed[/]")
        else:
            log.write(f"[bold red]✗ Install failed (exit {returncode})[/]")

        self._rebuild_rows()
        self._refresh_continue()

    def _refresh_continue(self) -> None:
        all_ok = all(ts.installed for ts in self._states.values())
        self.query_one("#continue-btn", Button).disabled = not all_ok

    def _log(self, msg: str) -> None:
        log = self.query_one("#log", RichLog)
        log.add_class("visible")
        log.write(msg)
