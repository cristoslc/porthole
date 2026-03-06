"""Secrets screen — manage age key, .sops.yaml, and network state."""

from __future__ import annotations

import subprocess
from pathlib import Path

from textual import on, work
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, RichLog

AGE_KEY_PATH = Path.home() / ".config" / "sops" / "age" / "keys.txt"
SOPS_CONFIG_PATH = Path(".sops.yaml")
STATE_PATH = Path("network.sops.yaml")

CSS = """
SecretsScreen { background: $surface; }
.section-title { text-style: bold; color: $accent; margin: 1 0 0 1; }
.status-ok  { color: $success; margin: 0 1; }
.status-bad { color: $error;   margin: 0 1; }
.status-warn { color: $warning; margin: 0 1; }
.info { color: $text-muted; margin: 0 1 1 1; }
.action-row { layout: horizontal; height: 3; margin: 0 1; }
#confirm-row { layout: horizontal; height: 3; margin: 0 1; display: none; }
#confirm-row.visible { display: block; }
#confirm-input { width: 12; }
#log { height: 10; border: solid $primary; margin: 1; display: none; }
#log.visible { display: block; }
#continue-btn { margin: 1; dock: bottom; }
"""

_SOPS_YAML_TEMPLATE = """\
creation_rules:
  - path_regex: network\\.sops\\.yaml$
    encrypted_regex: "^private_key$"
    age: "{age_pubkey}"
"""


def _age_pubkey_from_keyfile(path: Path) -> str | None:
    """Extract the age public key from the keys.txt file."""
    try:
        text = path.read_text()
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("# public key:"):
                return line.split(":", 1)[1].strip()
        return None
    except OSError:
        return None


def _summarise_state() -> str | None:
    """Return a one-line summary of network.sops.yaml, or None if unreadable."""
    try:
        result = subprocess.run(
            ["sops", "-d", "--output-type", "json", str(STATE_PATH)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None
        import json  # noqa: PLC0415
        data = json.loads(result.stdout)
        net = data.get("network", {})
        endpoint = net.get("hub", {}).get("endpoint", "?")
        peers = net.get("peers", [])
        return f"endpoint={endpoint}, {len(peers)} peer(s)"
    except Exception:  # noqa: BLE001
        return None


class SecretsScreen(Screen):
    """Manage age key, .sops.yaml configuration, and network state file."""

    TITLE = "Step 2 of 5: Secrets"
    CSS = CSS

    # Reactive states — updated after each async operation
    age_ok: reactive[bool] = reactive(False)
    sops_ok: reactive[bool] = reactive(False)
    state_ok: reactive[bool] = reactive(False)
    state_summary: reactive[str] = reactive("")

    def __init__(self) -> None:
        super().__init__()
        self._check_initial_state()

    def _check_initial_state(self) -> None:
        self.age_ok = AGE_KEY_PATH.exists()
        self.sops_ok = SOPS_CONFIG_PATH.exists()
        self.state_ok = STATE_PATH.exists()
        if self.state_ok:
            summary = _summarise_state()
            self.state_summary = summary or "(could not decrypt)"

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        yield ScrollableContainer(
            # --- Age key ---
            Label("Age encryption key", classes="section-title"),
            Label(
                ("✓ Key found" if self.age_ok else "✗ Key not found"),
                id="age-status",
                classes="status-ok" if self.age_ok else "status-bad",
            ),
            Label(str(AGE_KEY_PATH), classes="info"),
            Vertical(
                Button(
                    "Generate key" if not self.age_ok else "Regenerate key (will break existing state)",
                    id="age-btn",
                    variant="primary" if not self.age_ok else "warning",
                ),
                id="age-action",
                classes="action-row",
            ),
            # --- .sops.yaml ---
            Label(".sops.yaml configuration", classes="section-title"),
            Label(
                ("✓ Found" if self.sops_ok else "✗ Not found"),
                id="sops-status",
                classes="status-ok" if self.sops_ok else "status-bad",
            ),
            Vertical(
                Button(
                    "Write from age key" if not self.sops_ok else "Overwrite from age key",
                    id="sops-btn",
                    variant="primary" if not self.sops_ok else "warning",
                    disabled=not self.age_ok,
                ),
                id="sops-action",
                classes="action-row",
            ),
            # --- network.sops.yaml ---
            Label("Network state (network.sops.yaml)", classes="section-title"),
            Label(
                (f"✓ Found — {self.state_summary}" if self.state_ok else "✗ Not found"),
                id="state-status",
                classes="status-ok" if self.state_ok else "status-bad",
            ),
            Vertical(
                Button(
                    "Initialize state" if not self.state_ok else "Re-initialize state (destructive)",
                    id="state-btn",
                    variant="primary" if not self.state_ok else "error",
                    disabled=not self.age_ok or not self.sops_ok,
                ),
                id="state-action",
                classes="action-row",
            ),
            Vertical(
                Input(
                    placeholder="type 'yes' to confirm re-initialization",
                    id="confirm-input",
                ),
                Button("Confirm re-initialize", id="confirm-btn", variant="error", disabled=True),
                id="confirm-row",
            ),
            RichLog(id="log", highlight=True, markup=True),
        )
        all_ok = self.age_ok and self.sops_ok and self.state_ok
        yield Button("Continue →", id="continue-btn", variant="success", disabled=not all_ok)
        yield Button("← Back", id="back-btn", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_ui()

    # ------------------------------------------------------------------
    # Reactive watches
    # ------------------------------------------------------------------

    def watch_age_ok(self, ok: bool) -> None:
        try:
            self.query_one("#age-status", Label).update("✓ Key found" if ok else "✗ Key not found")
            self.query_one("#age-status").set_class(ok, "status-ok")
            self.query_one("#age-status").set_class(not ok, "status-bad")
        except Exception:  # noqa: BLE001
            pass
        self._refresh_ui()

    def watch_sops_ok(self, ok: bool) -> None:
        try:
            self.query_one("#sops-status", Label).update("✓ Found" if ok else "✗ Not found")
            self.query_one("#sops-status").set_class(ok, "status-ok")
            self.query_one("#sops-status").set_class(not ok, "status-bad")
        except Exception:  # noqa: BLE001
            pass
        self._refresh_ui()

    def watch_state_ok(self, ok: bool) -> None:
        try:
            summary = f" — {self.state_summary}" if (ok and self.state_summary) else ""
            self.query_one("#state-status", Label).update(
                f"✓ Found{summary}" if ok else "✗ Not found"
            )
            self.query_one("#state-status").set_class(ok, "status-ok")
            self.query_one("#state-status").set_class(not ok, "status-bad")
        except Exception:  # noqa: BLE001
            pass
        self._refresh_ui()

    def watch_state_summary(self, summary: str) -> None:
        try:
            status = "✓ Found"
            if summary:
                status += f" — {summary}"
            self.query_one("#state-status", Label).update(status)
        except Exception:  # noqa: BLE001
            pass

    def _refresh_ui(self) -> None:
        try:
            self.query_one("#sops-btn", Button).disabled = not self.age_ok
            self.query_one("#state-btn", Button).disabled = not (self.age_ok and self.sops_ok)
            all_ok = self.age_ok and self.sops_ok and self.state_ok
            self.query_one("#continue-btn", Button).disabled = not all_ok
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    @on(Button.Pressed, "#age-btn")
    def _age_pressed(self) -> None:
        if self.age_ok:
            # Regeneration: show warning and require confirmation
            self._log("[bold yellow]Warning: regenerating the age key will break decryption of existing network.sops.yaml.[/]")
            self._log("If you proceed, you will need to re-initialize the network state. Continue anyway? [Use 'Generate key' to proceed.]")
            # Relabel button to confirm
            btn = self.query_one("#age-btn", Button)
            btn.label = "Yes, regenerate key (I understand)"
            btn.variant = "error"
            btn.id = "age-confirm-btn"
        else:
            self._generate_age_key()

    @on(Button.Pressed, "#age-confirm-btn")
    def _age_confirm(self) -> None:
        self._generate_age_key()

    @work(exclusive=True)
    async def _generate_age_key(self) -> None:
        log = self.query_one("#log", RichLog)
        log.add_class("visible")
        log.write("[bold]Generating age key…[/]")

        AGE_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        import asyncio  # noqa: PLC0415
        proc = await asyncio.create_subprocess_exec(
            "age-keygen", "-o", str(AGE_KEY_PATH),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert proc.stdout is not None
        async for raw in proc.stdout:
            log.write(raw.decode(errors="replace").rstrip())
        rc = await proc.wait()

        if rc == 0:
            log.write("[bold green]✓ Age key generated[/]")
            self.age_ok = True
            pubkey = _age_pubkey_from_keyfile(AGE_KEY_PATH)
            if pubkey:
                log.write(f"Public key: [bold]{pubkey}[/]")
            # Reset button
            btn = self.query_one("[id^='age']", Button)
            btn.label = "Regenerate key (will break existing state)"
            btn.variant = "warning"
            btn.id = "age-btn"
        else:
            log.write(f"[bold red]✗ age-keygen failed (exit {rc})[/]")

    @on(Button.Pressed, "#sops-btn")
    def _sops_pressed(self) -> None:
        self._write_sops_config()

    @work(exclusive=True)
    async def _write_sops_config(self) -> None:
        log = self.query_one("#log", RichLog)
        log.add_class("visible")
        pubkey = _age_pubkey_from_keyfile(AGE_KEY_PATH)
        if not pubkey:
            log.write("[bold red]✗ Could not read age public key from key file[/]")
            return
        content = _SOPS_YAML_TEMPLATE.format(age_pubkey=pubkey)
        SOPS_CONFIG_PATH.write_text(content)
        log.write(f"[bold green]✓ .sops.yaml written (public key: {pubkey})[/]")
        self.sops_ok = True

    @on(Button.Pressed, "#state-btn")
    def _state_pressed(self) -> None:
        if self.state_ok:
            # Destructive — show confirmation input
            confirm_row = self.query_one("#confirm-row")
            confirm_row.add_class("visible")
            self.query_one("#state-btn", Button).disabled = True
        else:
            self._init_state()

    @on(Input.Changed, "#confirm-input")
    def _confirm_changed(self, event: Input.Changed) -> None:
        ok = event.value.strip().lower() == "yes"
        self.query_one("#confirm-btn", Button).disabled = not ok

    @on(Button.Pressed, "#confirm-btn")
    def _confirm_reinit(self) -> None:
        confirm_row = self.query_one("#confirm-row")
        confirm_row.remove_class("visible")
        self.query_one("#state-btn", Button).disabled = False
        self._init_state()

    @work(exclusive=True)
    async def _init_state(self) -> None:
        log = self.query_one("#log", RichLog)
        log.add_class("visible")
        log.write("[bold]Initializing network state via porthole init…[/]")
        log.write("You will be prompted for the hub endpoint (e.g. hub.example.com).")

        # porthole init is interactive; run it in the terminal.
        # We can't stream its prompts through a Textual widget easily,
        # so we suspend the app, run it in the terminal, then resume.
        with self.app.suspend():
            import subprocess as sp  # noqa: PLC0415
            result = sp.run(["porthole", "init"])

        if STATE_PATH.exists():
            summary = _summarise_state()
            self.state_summary = summary or "(could not decrypt)"
            self.state_ok = True
            log.write("[bold green]✓ network.sops.yaml created[/]")
            if summary:
                log.write(f"  {summary}")
        else:
            log.write("[bold red]✗ network.sops.yaml not found after porthole init[/]")

    @on(Button.Pressed, "#back-btn")
    def _back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#continue-btn")
    def _continue(self) -> None:
        from porthole_setup.screens.hub_check import HubCheckScreen  # noqa: PLC0415
        self.app.push_screen(HubCheckScreen())
