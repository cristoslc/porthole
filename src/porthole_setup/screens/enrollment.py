"""Node enrollment screen — register this node in network.sops.yaml."""

from __future__ import annotations

import asyncio
import socket

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, RichLog, Select, Static

from porthole_setup.state import StateDecryptionError, StateNotFoundError, load_state

CSS = """
EnrollmentScreen { background: $surface; }
.section-title { text-style: bold; color: $accent; margin: 1 0 0 1; }
.info   { color: $text-muted; margin: 0 1; }
.status-ok  { color: $success; margin: 0 1; }
.status-bad { color: $error;   margin: 0 1; }
.field-row  { height: 3; margin: 0 1; }
#form-container { margin: 0 1; }
#role-select { margin: 0 0 1 0; }
#platform-select { margin: 0 0 1 0; }
#log { height: 12; border: solid $primary; margin: 1; }
#button-row { layout: horizontal; height: 3; margin: 1; }
"""

ROLE_OPTIONS: list[tuple[str, str]] = [
    ("workstation", "Workstation"),
    ("server",      "Server"),
    ("family",      "Family"),
]

PLATFORM_OPTIONS: list[tuple[str, str]] = [
    ("linux", "Linux"),
    ("macos", "macOS"),
]


class EnrollmentScreen(Screen):
    """Register this node in network.sops.yaml and generate peer scripts."""

    TITLE = "Step 4 of 5: Node Enrollment"
    CSS = CSS

    def __init__(self) -> None:
        super().__init__()
        self._hostname = socket.gethostname()
        self._running = False
        self._enrolled_name: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield ScrollableContainer(
            Label("Node registration", classes="section-title"),
            Label("Checking state…", id="status-label", classes="info"),
            Vertical(id="form-container"),
            RichLog(id="log", highlight=True, markup=True),
            Vertical(id="button-row"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self._check_registration()

    # ------------------------------------------------------------------
    # Check worker
    # ------------------------------------------------------------------

    @work(exclusive=True)
    async def _check_registration(self) -> None:
        try:
            state = load_state()
        except StateNotFoundError:
            self.query_one("#status-label", Label).update(
                "[bold red]✗ network.sops.yaml not found — go back to Secrets screen[/]"
            )
            self._show_back_only()
            return
        except (StateDecryptionError, ValueError) as exc:
            self.query_one("#status-label", Label).update(
                f"[bold red]✗ Could not load state: {exc}[/]"
            )
            self._show_back_only()
            return

        peer = state.get_peer(self._hostname)
        container = self.query_one("#form-container", Vertical)

        if peer is not None:
            self._enrolled_name = peer.name
            self.query_one("#status-label", Label).update(
                f"[bold green]✓ This node is already registered as '[bold]{peer.name}[/]' "
                f"({peer.ip})[/]"
            )
            await container.mount(
                Static(
                    f"  Role: {peer.role or '—'}   IP: {peer.ip}",
                    classes="info",
                ),
            )
            self._show_registered_buttons()
        else:
            self.query_one("#status-label", Label).update(
                f"Hostname '[bold]{self._hostname}[/]' not found in state — "
                "fill in the form below and click Enroll."
            )
            await self._mount_form(container)

    # ------------------------------------------------------------------
    # Dynamic UI helpers
    # ------------------------------------------------------------------

    async def _mount_form(self, container: Vertical) -> None:
        await container.mount(
            Label("Node name", classes="section-title"),
            Label(
                "Name to register this node under (defaults to hostname).",
                classes="info",
            ),
            Vertical(
                Input(
                    value=self._hostname,
                    placeholder="node-name",
                    id="name-input",
                ),
                classes="field-row",
            ),
            Label("Role", classes="section-title"),
            Select(
                [(label, value) for value, label in ROLE_OPTIONS],
                value="workstation",
                id="role-select",
            ),
            Label("Platform", classes="section-title"),
            Select(
                [(label, value) for value, label in PLATFORM_OPTIONS],
                value="linux",
                id="platform-select",
            ),
        )
        row = self.query_one("#button-row", Vertical)
        row.remove_children()
        row.mount(
            Button("Enroll", id="enroll-btn", variant="primary"),
            Button("← Back", id="back-btn", variant="default"),
        )

    def _show_registered_buttons(self) -> None:
        row = self.query_one("#button-row", Vertical)
        row.remove_children()
        row.mount(
            Button("Re-sync", id="resync-btn", variant="default"),
            Button("Continue →", id="continue-btn", variant="success"),
            Button("← Back", id="back-btn", variant="default"),
        )

    def _show_back_only(self) -> None:
        row = self.query_one("#button-row", Vertical)
        row.remove_children()
        row.mount(Button("← Back", id="back-btn", variant="default"))

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#back-btn")
    def _back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#continue-btn")
    def _continue(self) -> None:
        from porthole_setup.screens.service_install import ServiceInstallScreen  # noqa: PLC0415
        self.app.push_screen(ServiceInstallScreen(peer_name=self._enrolled_name))

    @on(Button.Pressed, "#enroll-btn")
    def _enroll(self) -> None:
        if self._running:
            return
        name = self.query_one("#name-input", Input).value.strip() or self._hostname
        role_val = self.query_one("#role-select", Select).value
        role = str(role_val) if role_val is not Select.BLANK else "workstation"
        platform_val = self.query_one("#platform-select", Select).value
        platform = str(platform_val) if platform_val is not Select.BLANK else "linux"

        self._running = True
        self.query_one("#enroll-btn", Button).disabled = True
        self._run_enrollment(name, role, platform)

    @on(Button.Pressed, "#resync-btn")
    def _resync(self) -> None:
        if self._running:
            return
        self._running = True
        self.query_one("#resync-btn", Button).disabled = True
        self._run_resync(self._enrolled_name)

    # ------------------------------------------------------------------
    # Workers
    # ------------------------------------------------------------------

    @work(exclusive=True)
    async def _run_enrollment(self, name: str, role: str, platform: str) -> None:
        log = self.query_one("#log", RichLog)
        self._enrolled_name = name

        # porthole add
        rc = await self._stream(
            log, ["porthole", "add", name, "--role", role, "--platform", platform]
        )
        if rc != 0:
            self._finish_failed(log, "porthole add failed")
            return

        # porthole sync
        rc = await self._stream(log, ["porthole", "sync"])
        if rc != 0:
            self._finish_failed(log, "porthole sync failed")
            return

        # porthole gen-peer-scripts
        rc = await self._stream(
            log, ["porthole", "gen-peer-scripts", name, "--out", f"peer-scripts/{name}/"]
        )
        if rc != 0:
            self._finish_failed(log, "gen-peer-scripts failed")
            return

        log.write("\n[bold green]✓ Enrollment complete[/]")
        self._running = False
        row = self.query_one("#button-row", Vertical)
        row.remove_children()
        row.mount(
            Button("Continue →", id="continue-btn", variant="success"),
            Button("← Back", id="back-btn", variant="default"),
        )

    @work(exclusive=True)
    async def _run_resync(self, name: str) -> None:
        log = self.query_one("#log", RichLog)

        rc = await self._stream(log, ["porthole", "sync"])
        if rc == 0:
            # Regenerate peer scripts after re-sync
            await self._stream(
                log, ["porthole", "gen-peer-scripts", name, "--out", f"peer-scripts/{name}/"]
            )
            log.write("\n[bold green]✓ Re-sync complete[/]")
        else:
            log.write("\n[bold red]✗ porthole sync failed[/]")

        self._running = False
        try:
            self.query_one("#resync-btn", Button).disabled = False
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _stream(self, log: RichLog, cmd: list[str]) -> int:
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
            return await proc.wait()
        except FileNotFoundError as exc:
            log.write(f"[bold red]✗ Command not found: {exc}[/]")
            return 1
        except Exception as exc:  # noqa: BLE001
            log.write(f"[bold red]✗ Unexpected error: {exc}[/]")
            return 1

    def _finish_failed(self, log: RichLog, msg: str) -> None:
        log.write(f"\n[bold red]✗ {msg}[/]")
        self._running = False
        try:
            self.query_one("#enroll-btn", Button).disabled = False
        except Exception:  # noqa: BLE001
            pass
