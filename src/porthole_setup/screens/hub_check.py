"""Hub check screen — initialize state, verify hub, offer spinup."""

from __future__ import annotations

import logging
import socket
import subprocess
from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, RichLog

from porthole_setup.screens.secrets import AGE_KEY_PATH, _age_pubkey_from_keyfile
from porthole_setup.state import StateDecryptionError, StateNotFoundError, load_state

_log = logging.getLogger(__name__)

STATE_PATH = Path("network.sops.yaml")

CSS = """
HubCheckScreen { background: $surface; }
.section-title { text-style: bold; color: $accent; margin: 1 0 0 1; }
.info { color: $text-muted; margin: 0 1; }
.status-ok       { color: $success; margin: 0 1; }
.status-bad      { color: $error;   margin: 0 1; }
.status-warn     { color: $warning; margin: 0 1; }
.status-checking { color: $warning; margin: 0 1; }
#init-section { margin: 0 1; }
#endpoint-input { width: 50; margin: 0 0 1 0; }
#button-row { height: auto; margin: 1; }
#button-row Button { margin: 0 1 0 0; }
#log { height: 10; border: solid $primary; margin: 1; display: none; }
#log.visible { display: block; }
"""


class HubCheckScreen(Screen):
    """Initialize network state, check hub reachability, offer spinup."""

    TITLE = "Step 3 of 5: Hub Check"
    CSS = CSS

    def __init__(self) -> None:
        super().__init__()
        self._hostname: str = ""
        self._endpoint: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield ScrollableContainer(
            Label("Network state", classes="section-title"),
            Label("Checking…", id="state-label", classes="status-checking"),

            # --- Init section (shown when no state file) ---
            Vertical(
                Label("No network state found. Enter the hub endpoint to initialize,", classes="info"),
                Label("or spin up a new hub with terraform.", classes="info"),
                Label("Hub endpoint (e.g. hub.example.com:51820):", classes="info"),
                Input(placeholder="hub.example.com:51820", id="endpoint-input"),
                Button("Initialize with existing hub", id="init-btn", variant="primary", disabled=True),
                Button("Spin up a new hub (terraform)", id="spinup-new-btn", variant="warning"),
                id="init-section",
            ),

            # --- Check results (shown when state exists) ---
            Label("Hub endpoint", classes="section-title"),
            Label("", id="endpoint-label", classes="info"),
            Label("DNS resolution", classes="section-title"),
            Label("", id="dns-label", classes="status-checking"),
            Label("WireGuard interface (this node)", classes="section-title"),
            Label("", id="wg-label", classes="status-checking"),
            RichLog(id="log", highlight=True, markup=True),
            Vertical(id="button-row"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self._hide_check_labels()
        self.query_one("#init-section").display = False
        self._run_checks()

    # ------------------------------------------------------------------
    # Init section handlers
    # ------------------------------------------------------------------

    @on(Input.Changed, "#endpoint-input")
    def _endpoint_changed(self, event: Input.Changed) -> None:
        self.query_one("#init-btn", Button).disabled = not event.value.strip()

    @on(Button.Pressed, "#init-btn")
    def _init_pressed(self) -> None:
        self._run_init()

    @on(Button.Pressed, "#spinup-new-btn")
    def _spinup_new_pressed(self) -> None:
        from porthole_setup.screens.hub_spinup import HubSpinupScreen  # noqa: PLC0415
        self.app.push_screen(HubSpinupScreen(endpoint=""))

    @work(thread=True, exclusive=True)
    def _run_init(self) -> None:
        endpoint = self.app.call_from_thread(
            lambda: self.query_one("#endpoint-input", Input).value.strip()
        )
        pubkey = _age_pubkey_from_keyfile(AGE_KEY_PATH)
        if not endpoint or not pubkey:
            self.app.call_from_thread(
                self._log_markup,
                "[bold red]✗ Endpoint and age public key are both required[/]",
            )
            return

        self.app.call_from_thread(self._show_log)
        cmd = ["porthole", "init", "--endpoint", endpoint, "--age-key", pubkey]
        self.app.call_from_thread(
            self._log_markup, f"[bold]$ {' '.join(cmd)}[/]"
        )
        _log.info("Running: %s", " ".join(cmd))

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            for line in result.stdout.splitlines():
                self.app.call_from_thread(self._log_markup, line)
        if result.stderr:
            for line in result.stderr.splitlines():
                self.app.call_from_thread(self._log_markup, line)

        if result.returncode != 0:
            self.app.call_from_thread(
                self._log_markup,
                f"[bold red]✗ porthole init failed (exit {result.returncode})[/]",
            )
            return

        self.app.call_from_thread(
            self._log_markup, "[bold green]✓ Network state initialized[/]"
        )
        self.app.call_from_thread(self._hide_init_section)
        self._run_checks()

    # ------------------------------------------------------------------
    # Main check flow
    # ------------------------------------------------------------------

    @work(thread=True, exclusive=True)
    def _run_checks(self) -> None:
        try:
            state = load_state()
        except StateNotFoundError:
            self.app.call_from_thread(self._show_no_state)
            return
        except (StateDecryptionError, ValueError) as exc:
            self.app.call_from_thread(
                self._show_state_error, f"Could not load state: {exc}"
            )
            return

        self._endpoint = state.endpoint
        self._hostname = state.endpoint.split(":")[0]
        self.app.call_from_thread(self._show_state_loaded, state.endpoint, self._hostname)

        # DNS check — does the hostname resolve to a real IP?
        resolved_ip = self._resolve_hostname(self._hostname)
        self.app.call_from_thread(self._update_dns, self._hostname, resolved_ip)

        # WireGuard status
        wg_text, wg_ok = self._sync_wg_status()
        self.app.call_from_thread(self._update_wg, wg_text, wg_ok)

        self.app.call_from_thread(self._show_buttons)

    def _resolve_hostname(self, hostname: str) -> str | None:
        """Resolve hostname to IP. Returns IP string or None."""
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror:
            return None

    def _sync_wg_status(self) -> tuple[str, bool]:
        try:
            result = subprocess.run(
                ["wg", "show", "wg0"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                peer_count = result.stdout.count("peer:")
                return (f"[green]✓ wg0 is active ({peer_count} peer(s))[/]", True)
            return ("[dim]wg0 not active — expected before enrollment[/]", False)
        except FileNotFoundError:
            return ("[dim]wireguard-tools not installed[/]", False)
        except Exception:  # noqa: BLE001
            return ("[dim]Could not query WireGuard status[/]", False)

    # ------------------------------------------------------------------
    # UI helpers (main thread)
    # ------------------------------------------------------------------

    def _hide_check_labels(self) -> None:
        for sel in ("#endpoint-label", "#dns-label", "#wg-label"):
            self.query_one(sel, Label).display = False

    def _show_check_labels(self) -> None:
        for sel in ("#endpoint-label", "#dns-label", "#wg-label"):
            self.query_one(sel, Label).display = True

    def _show_no_state(self) -> None:
        self.query_one("#state-label", Label).update(
            "[bold yellow]✗ network.sops.yaml not found[/]"
        )
        self.query_one("#state-label").set_classes("status-bad")
        self.query_one("#init-section").display = True
        self._hide_check_labels()
        row = self.query_one("#button-row", Vertical)
        row.remove_children()
        row.mount(Button("← Back", id="back-btn", variant="default"))

    def _show_state_error(self, msg: str) -> None:
        self.query_one("#state-label", Label).update(f"[bold red]✗ {msg}[/]")
        self.query_one("#state-label").set_classes("status-bad")
        row = self.query_one("#button-row", Vertical)
        row.remove_children()
        row.mount(Button("← Back", id="back-btn", variant="default"))

    def _hide_init_section(self) -> None:
        self.query_one("#init-section").display = False

    def _show_state_loaded(self, endpoint: str, hostname: str) -> None:
        self.query_one("#state-label", Label).update("[bold green]✓ State loaded[/]")
        self.query_one("#state-label").set_classes("status-ok")
        self.query_one("#init-section").display = False
        self._show_check_labels()
        self.query_one("#endpoint-label", Label).update(
            f"Endpoint: [bold]{endpoint}[/]  (host: [bold]{hostname}[/])"
        )
        self.query_one("#dns-label", Label).update("Resolving…")
        self.query_one("#dns-label").set_classes("status-checking")
        self.query_one("#wg-label", Label).update("Checking…")
        self.query_one("#wg-label").set_classes("status-checking")

    def _update_dns(self, hostname: str, ip: str | None) -> None:
        lbl = self.query_one("#dns-label", Label)
        if ip:
            lbl.update(f"[green]✓ {hostname} → {ip}[/]")
            lbl.set_classes("status-ok")
        else:
            lbl.update(f"[bold red]✗ {hostname} does not resolve[/]")
            lbl.set_classes("status-bad")

    def _update_wg(self, text: str, ok: bool) -> None:
        lbl = self.query_one("#wg-label", Label)
        lbl.update(text)
        lbl.set_classes("status-ok" if ok else "info")

    def _show_log(self) -> None:
        self.query_one("#log", RichLog).add_class("visible")

    def _log_markup(self, msg: str) -> None:
        self._show_log()
        self.query_one("#log", RichLog).write(msg)

    # ------------------------------------------------------------------
    # Buttons — always show Continue; spinup and re-init always available
    # ------------------------------------------------------------------

    def _show_buttons(self) -> None:
        row = self.query_one("#button-row", Vertical)
        row.remove_children()
        row.mount(Button("Continue →", id="continue-btn", variant="success"))
        row.mount(Button("Spin Up Hub (terraform)", id="spinup-btn", variant="warning"))
        row.mount(Button("Re-initialize state", id="reinit-btn", variant="error"))
        row.mount(Button("Re-check", id="recheck-btn", variant="default"))
        row.mount(Button("← Back", id="back-btn", variant="default"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "back-btn":
            self.app.pop_screen()
        elif bid == "spinup-btn":
            from porthole_setup.screens.hub_spinup import HubSpinupScreen  # noqa: PLC0415
            self.app.push_screen(HubSpinupScreen(endpoint=self._endpoint))
        elif bid == "reinit-btn":
            # Delete existing state and show init section
            if STATE_PATH.exists():
                STATE_PATH.unlink()
                _log.info("Deleted %s for re-initialization", STATE_PATH)
            self._show_no_state()
            row = self.query_one("#button-row", Vertical)
            row.remove_children()
            row.mount(Button("← Back", id="back-btn", variant="default"))
        elif bid == "recheck-btn":
            self._hide_check_labels()
            self.query_one("#state-label", Label).update("Checking…")
            self.query_one("#state-label").set_classes("status-checking")
            row = self.query_one("#button-row", Vertical)
            row.remove_children()
            self._run_checks()
        elif bid == "continue-btn":
            from porthole_setup.screens.enrollment import EnrollmentScreen  # noqa: PLC0415
            self.app.push_screen(EnrollmentScreen())
