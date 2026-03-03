"""Hub check screen — verify hub reachability; offer to spin up if missing."""

from __future__ import annotations

import asyncio

from textual import work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label

from porthole_setup.state import StateDecryptionError, StateNotFoundError, load_state

CSS = """
HubCheckScreen { background: $surface; }
.section-title { text-style: bold; color: $accent; margin: 1 0 0 1; }
.info { color: $text-muted; margin: 0 1; }
.status-ok       { color: $success; margin: 0 1; }
.status-bad      { color: $error;   margin: 0 1; }
.status-checking { color: $warning; margin: 0 1; }
#button-row { layout: horizontal; height: 3; margin: 1; }
#recheck-btn { margin: 1 0 0 1; }
"""


class HubCheckScreen(Screen):
    """Check whether the hub VPS is reachable; offer to spin it up if not."""

    TITLE = "Step 3 of 5: Hub Check"
    CSS = CSS

    def __init__(self) -> None:
        super().__init__()
        self._hostname: str = ""
        self._endpoint: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield ScrollableContainer(
            Label("Hub endpoint", classes="section-title"),
            Label("Loading state…", id="endpoint-label", classes="info"),
            Label("Ping", classes="section-title"),
            Label("Checking…", id="ping-label", classes="status-checking"),
            Label("WireGuard interface (this node)", classes="section-title"),
            Label("Checking…", id="wg-label", classes="status-checking"),
            Vertical(id="button-row"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self._run_checks()

    # ------------------------------------------------------------------
    # Main check worker
    # ------------------------------------------------------------------

    @work(exclusive=True)
    async def _run_checks(self) -> None:
        # --- Load state ---
        try:
            state = load_state()
        except StateNotFoundError:
            self.query_one("#endpoint-label", Label).update(
                "[bold red]✗ network.sops.yaml not found — go back to Secrets screen[/]"
            )
            self._show_buttons(reachable=False, state_error=True)
            return
        except (StateDecryptionError, ValueError) as exc:
            self.query_one("#endpoint-label", Label).update(
                f"[bold red]✗ Could not load state: {exc}[/]"
            )
            self._show_buttons(reachable=False, state_error=True)
            return

        self._endpoint = state.endpoint
        self._hostname = state.endpoint.split(":")[0]
        self.query_one("#endpoint-label", Label).update(
            f"Endpoint: [bold]{state.endpoint}[/]  (host: [bold]{self._hostname}[/])"
        )

        # --- Ping ---
        ping_ok = await self._ping(self._hostname)
        ping_lbl = self.query_one("#ping-label", Label)
        if ping_ok:
            ping_lbl.update(f"[bold green]✓ {self._hostname} is reachable[/]")
            ping_lbl.set_classes("status-ok")
        else:
            ping_lbl.update(f"[bold red]✗ {self._hostname} is not reachable (hub may be down or not yet provisioned)[/]")
            ping_lbl.set_classes("status-bad")

        # --- WireGuard status ---
        wg_text, wg_ok = await self._wg_status()
        wg_lbl = self.query_one("#wg-label", Label)
        wg_lbl.update(wg_text)
        wg_lbl.set_classes("status-ok" if wg_ok else "info")

        self._show_buttons(reachable=ping_ok, state_error=False)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    async def _ping(self, hostname: str) -> bool:
        """Return True if hostname responds to a single ping within 5 s."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "3", hostname,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            rc = await asyncio.wait_for(proc.wait(), timeout=6)
            return rc == 0
        except Exception:  # noqa: BLE001
            return False

    async def _wg_status(self) -> tuple[str, bool]:
        """
        Return (display_text, is_up) for the local wg0 interface.
        Not being up is expected before enrollment — treated as informational.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                "wg", "show", "wg0",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0 and stdout.strip():
                lines = stdout.decode(errors="replace")
                peer_count = lines.count("peer:")
                return (f"[green]✓ wg0 is active ({peer_count} peer(s))[/]", True)
            return ("[dim]wg0 not active on this node — expected before enrollment[/]", False)
        except FileNotFoundError:
            return ("[dim]wireguard-tools not installed[/]", False)
        except Exception:  # noqa: BLE001
            return ("[dim]Could not query WireGuard status[/]", False)

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------

    def _show_buttons(self, *, reachable: bool, state_error: bool) -> None:
        row = self.query_one("#button-row", Vertical)
        row.remove_children()
        if state_error:
            row.mount(Button("← Back", id="back-btn", variant="default"))
            return
        if not reachable:
            row.mount(Button("Spin Up Hub", id="spinup-btn", variant="primary"))
            row.mount(Button("Skip (continue anyway)", id="continue-btn", variant="default"))
        else:
            row.mount(Button("Continue →", id="continue-btn", variant="success"))
        row.mount(Button("← Back", id="back-btn", variant="default"))
        row.mount(Button("Re-check", id="recheck-btn", variant="default"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "back-btn":
            self.app.pop_screen()
        elif bid == "spinup-btn":
            from porthole_setup.screens.hub_spinup import HubSpinupScreen  # noqa: PLC0415
            self.app.push_screen(HubSpinupScreen(endpoint=self._endpoint))
        elif bid == "recheck-btn":
            # Reset labels and re-run
            self.query_one("#ping-label", Label).update("Checking…")
            self.query_one("#ping-label", Label).set_classes("status-checking")
            self.query_one("#wg-label", Label).update("Checking…")
            self.query_one("#wg-label", Label).set_classes("status-checking")
            row = self.query_one("#button-row", Vertical)
            row.remove_children()
            self._run_checks()
        elif bid == "continue-btn":
            # Enrollment screen not yet implemented — placeholder
            self.app.pop_screen()
