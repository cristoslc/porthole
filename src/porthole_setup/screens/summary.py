"""Summary screen — final status of all setup steps."""

from __future__ import annotations

import asyncio
import socket
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static

from porthole_setup.platform import is_installed
from porthole_setup.screens.prerequisites import TOOLS
from porthole_setup.screens.secrets import AGE_KEY_PATH, SOPS_CONFIG_PATH, STATE_PATH
from porthole_setup.state import load_state

CSS = """
SummaryScreen { background: $surface; }
.section-title { text-style: bold; color: $accent; margin: 1 0 0 1; }
.check-row  { margin: 0 2; }
.ok    { color: $success; }
.bad   { color: $error; }
.dim   { color: $text-muted; }
#banner { text-style: bold; margin: 1; padding: 1; text-align: center; }
#banner.all-ok  { color: $success; border: solid $success; }
#banner.has-bad { color: $error;   border: solid $error; }
#button-row { layout: horizontal; height: 3; margin: 1; }
"""

# Each check: (id_suffix, display_label)
_TOOL_CHECK_IDS = [(f"tool-{b}", f"tool: {d}") for b, d, _ in TOOLS]


class SummaryScreen(Screen):
    """Read-only final status: all green or list of issues."""

    TITLE = "Step 5 of 5: Summary"
    CSS = CSS

    def __init__(self, peer_name: str = "") -> None:
        super().__init__()
        self._peer_name = peer_name or socket.gethostname()

    def compose(self) -> ComposeResult:
        yield Header()
        yield ScrollableContainer(
            Label("Prerequisites", classes="section-title"),
            *[
                Static(f"[dim]…[/]  {label}", id=f"chk-{id_suffix}", classes="check-row")
                for id_suffix, label in _TOOL_CHECK_IDS
            ],
            Label("Secrets & state", classes="section-title"),
            Static("[dim]…[/]  age key",            id="chk-age",   classes="check-row"),
            Static("[dim]…[/]  .sops.yaml",         id="chk-sops",  classes="check-row"),
            Static("[dim]…[/]  network.sops.yaml",  id="chk-state", classes="check-row"),
            Label("Hub", classes="section-title"),
            Static("[dim]…[/]  hub reachable",      id="chk-hub",   classes="check-row"),
            Label("This node", classes="section-title"),
            Static("[dim]…[/]  enrolled in state",  id="chk-enroll", classes="check-row"),
            Static("[dim]…[/]  WireGuard wg0 up",   id="chk-wg",    classes="check-row"),
            Static("", id="banner", classes="dim"),
            Vertical(id="button-row"),
        )
        yield Footer()

    def on_mount(self) -> None:
        row = self.query_one("#button-row", Vertical)
        row.mount(
            Button("← Back", id="back-btn", variant="default"),
        )
        self._run_checks()

    # ------------------------------------------------------------------
    # Check worker — runs all checks, updates widgets as results arrive
    # ------------------------------------------------------------------

    @work(exclusive=True)
    async def _run_checks(self) -> None:
        results: dict[str, bool] = {}

        # --- Tools ---
        for binary, display, _ in TOOLS:
            ok = is_installed(binary)
            results[f"tool-{binary}"] = ok
            self._set_check(f"tool-{binary}", ok, f"tool: {display}")
            await asyncio.sleep(0)  # yield to event loop between checks

        # --- Secrets ---
        age_ok = AGE_KEY_PATH.exists()
        results["age"] = age_ok
        self._set_check("age", age_ok, f"age key ({AGE_KEY_PATH})")

        sops_ok = SOPS_CONFIG_PATH.exists()
        results["sops"] = sops_ok
        self._set_check("sops", sops_ok, ".sops.yaml")

        state_ok, state_detail = self._check_state()
        results["state"] = state_ok
        self._set_check("state", state_ok, f"network.sops.yaml  {state_detail}")

        # --- Hub reachability ---
        hub_ok, hub_detail = await self._check_hub()
        results["hub"] = hub_ok
        self._set_check("hub", hub_ok, f"hub reachable  {hub_detail}")

        # --- Enrollment ---
        enroll_ok, enroll_detail = self._check_enrollment()
        results["enroll"] = enroll_ok
        self._set_check("enroll", enroll_ok, f"enrolled in state  {enroll_detail}")

        # --- WireGuard ---
        wg_ok, wg_detail = await self._check_wg()
        results["wg"] = wg_ok
        self._set_check("wg", wg_ok, f"WireGuard wg0  {wg_detail}")

        # --- Banner ---
        failed = [k for k, v in results.items() if not v]
        banner = self.query_one("#banner", Static)
        if not failed:
            banner.update("All checks passed — node is fully enrolled and operational.")
            banner.set_classes("all-ok")
        else:
            banner.update(f"{len(failed)} check(s) failed — see items marked ✗ above.")
            banner.set_classes("has-bad")

        # Add Finish button now that checks are complete
        row = self.query_one("#button-row", Vertical)
        row.remove_children()
        row.mount(
            Button("Finish", id="finish-btn", variant="success"),
            Button("← Back", id="back-btn", variant="default"),
        )

    # ------------------------------------------------------------------
    # Individual check helpers
    # ------------------------------------------------------------------

    def _check_state(self) -> tuple[bool, str]:
        if not STATE_PATH.exists():
            return False, "(file not found)"
        try:
            state = load_state()
            return True, f"({len(state.peers)} peer(s), endpoint={state.endpoint})"
        except Exception as exc:  # noqa: BLE001
            return False, f"(decrypt failed: {exc})"

    def _check_enrollment(self) -> tuple[bool, str]:
        try:
            state = load_state()
            peer = state.get_peer(self._peer_name)
            if peer:
                return True, f"({self._peer_name} → {peer.ip})"
            return False, f"('{self._peer_name}' not found in state)"
        except Exception:  # noqa: BLE001
            return False, "(could not load state)"

    async def _check_hub(self) -> tuple[bool, str]:
        try:
            state = load_state()
            host = state.endpoint.split(":")[0]
        except Exception:  # noqa: BLE001
            return False, "(state unavailable)"
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "3", host,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            rc = await asyncio.wait_for(proc.wait(), timeout=6)
            return rc == 0, f"({host})"
        except Exception:  # noqa: BLE001
            return False, f"(ping failed for {host})"

    async def _check_wg(self) -> tuple[bool, str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "wg", "show", "wg0",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0 and stdout.strip():
                peer_count = stdout.decode(errors="replace").count("peer:")
                return True, f"(active, {peer_count} peer(s))"
            return False, "(interface not active)"
        except FileNotFoundError:
            return False, "(wireguard-tools not installed)"
        except Exception:  # noqa: BLE001
            return False, "(check failed)"

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def _set_check(self, id_suffix: str, ok: bool, label: str) -> None:
        icon = "[green]✓[/]" if ok else "[red]✗[/]"
        try:
            widget = self.query_one(f"#chk-{id_suffix}", Static)
            widget.update(f"{icon}  {label}")
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "back-btn":
            self.app.pop_screen()
        elif bid == "finish-btn":
            self.app.exit(message="Setup complete.")
